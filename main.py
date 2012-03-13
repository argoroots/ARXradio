# -*- coding: utf-8 -*-

import os
import webapp2
import jinja2
import json
import random
from datetime import *

from google.appengine.ext import db
from google.appengine.api import channel
from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulStoneSoup
from BeautifulSoup import *


class ShowPage(webapp2.RequestHandler):
    def get(self):
        token = channel.create_channel('raadio')
        jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__))))
        template = jinja_environment.get_template('template.html')
        self.response.out.write(template.render({'token': token}))


class UpdateInfo(webapp2.RequestHandler):
    def get(self):
        json_dict = {}

        json_dict['etv']     = get_info('http://otse.err.ee/xml/live-etv.html', '$(\'#onair\').html(\'', '\');$(\'#onairdesc')
        json_dict['etv2']    = get_info('http://otse.err.ee/xml/live-etv2.html', '$(\'#onair\').html(\'', '\');$(\'#onairdesc')

        json_dict['viker']   = get_info('http://otse.err.ee/xml/live-vikerraadio.html', '$(\'#onair\').html(\'', '\');$(\'#onairdesc')
        json_dict['klassika']= get_info('http://otse.err.ee/xml/live-klassikaraadio.html', '$(\'#onair\').html(\'', '\');$(\'#onairdesc')
        json_dict['r2']      = get_info('http://otse.err.ee/xml/live-r2.html', '$(\'#onair\').html(\'', '\');$(\'#onairdesc')
        json_dict['r4']      = get_info('http://otse.err.ee/xml/live-r4.html', '$(\'#onair\').html(\'', '\');$(\'#onairdesc')
        json_dict['tallinn'] = get_info('http://otse.err.ee/xml/live-raadiotallinn.html', '$(\'#onair\').html(\'', '\');$(\'#onairdesc')

        json_dict['elmar']   = get_info('http://www.elmar.ee/', '<div class="onair">', '</div>')
        json_dict['kuku']    = get_info('http://www.kuku.ee/', '<span class="pealkiri">Hetkel eetris</span>', '</a>')
        json_dict['mania']   = get_info('http://www.mania.ee/eeter.php?rnd='+str(random.randint(1, 1000000)), '<font color=\'ffffff\'>', '</font>')
        json_dict['sky']     = get_info('http://www.skyplus.fm/ram/nowplaying_main.html?rnd='+str(random.randint(1, 1000000)), '<span class="hetkeleetris">', '</span>')
        json_dict['r3']      = get_info('http://www.raadio3.ee/ram/nowplaying_main.html?rnd='+str(random.randint(1, 1000000)), '<span class="eetris2">', '</body>')
        json_dict['star']    = get_info('http://rds.starfm.ee/jsonRdsInfo.php?Name=Star&rnd='+str(random.randint(1, 1000000)), '({"currentArtist":"', '","nextArtist"').replace('","currentSong":"', ' - ')
        json_dict['power']   = get_info('http://rds.power.ee/jsonRdsInfo.php?Name=Power&rnd='+str(random.randint(1, 1000000)), '({"currentArtist":"', '","nextArtist"').replace('","currentSong":"', ' - ')

        json_str = json.dumps(json_dict)
        channel.send_message('raadio', json_str)

        self.response.headers['Content-type'] = 'application/json'
        self.response.out.write(json_str)


class ChannelConnection(webapp2.RequestHandler):
    def post(self, type):
        type = type.strip('/')


class RSS(db.Model):
    channel = db.StringProperty()
    show    = db.StringProperty()
    date    = db.DateTimeProperty()
    title   = db.StringProperty()
    url     = db.StringProperty()


class ShowRSS(webapp2.RequestHandler):
    def get(self, show):
        show = show.strip('/')
        items = db.Query(RSS)
        if show:
            items = db.Query(RSS).filter('show', show).order('-date').fetch(100)
        else:
            items = db.Query(RSS).order('-date').fetch(100)
        for i in items:
            i.sdate = i.date.strftime('%a, %d %b %Y %H:%M:%S +0000')
            i.url = 'http://%s/playlist.m3u8' % i.url.replace('rtsp://', '')
        jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__))))
        template = jinja_environment.get_template('rss.xml')
        self.response.out.write(template.render({
            'items': items,
            'show': '/%s' % show if show else ''
        }))


class UpdateRSS(webapp2.RequestHandler):
    def get(self):
        shows = {
            'ajavaod':           'ajavaod',
            'aktuaalne kaamera': 'ak',
            'arktikast antarktikasse': 'antarktikasse',
            'batareja':          'batareja',
            'eesti lood':        'eestilood',
            'jüri üdi klubi':    'jyriydi',
            'kapital':           'kapital',
            'nöbinina':          'nobinina',
            'osoon':             'osoon',
            'pealtnägija':       'pealtnagija',
            'puutepunkt':        'puutepunkt',
            'ringvaade':         'ringvaade',
            'teatrivara':        'teater',
            'telelavastus':      'teater',
            'lastelavastus':     'teater',
            'terevisioon':       'terevisioon',
            'välisilm':          'valisilm',
            'õnne 13':           'onne13',
        }
        for channel, channel_url in {'ETV':'http://m.err.ee/arhiiv/etv/', 'ETV2':'http://m.err.ee/arhiiv/etv2/'}.iteritems():
            soup = BeautifulSoup(urlfetch.fetch(channel_url, deadline=60).content)
            for i in soup.findAll('a', attrs={'class': 'releated jqclip'}):
                url = i['href'].replace('\n', '').strip()
                title = i.contents[0].replace('\n', '').strip()
                date = datetime.strptime(i.find('span').contents[0].replace('\n', '').strip(), '%H:%M | %d.%m.%Y')
                show = ''
                for s, u in shows.iteritems():
                    if title.lower().find(s.decode('utf-8')) > -1:
                        show = u
                        break

                row = db.Query(RSS).filter('channel', channel).filter('date', date).filter('title', title).filter('url', url).get()
                if not row:
                    row = RSS()
                    row.channel = channel
                    row.show = show
                    row.date = date
                    row.title = title
                    row.url = url
                    row.put()


def get_info(url, before, after):
    try:
        string = urlfetch.fetch(url, deadline=10).content.split(before)[1].split(after)[0].decode('utf-8')
        string = ' '.join(BeautifulStoneSoup(string, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).findAll(text=True))
        return unicode(string).strip()
    except:
        return ''


app = webapp2.WSGIApplication([
        ('/', ShowPage),
        ('/update', UpdateInfo),
        ('/_ah/channel/(.*)', ChannelConnection),
        ('/rss_update', UpdateRSS),
        ('/rss(.*)', ShowRSS),
    ], debug=True)
