# -*- coding: utf-8 -*-

import os
import webapp2
import jinja2
import logging
import json
import random

from datetime import *
from operator import itemgetter

from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
from google.appengine.api import channel

from BeautifulSoup import BeautifulStoneSoup
from BeautifulSoup import *

from database import *


class UpdateLive(webapp2.RequestHandler):
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

def get_info(url, before, after):
    try:
        string = urlfetch.fetch(url, deadline=10).content.split(before)[1].split(after)[0].decode('utf-8')
        string = ' '.join(BeautifulStoneSoup(string, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).findAll(text=True))
        return unicode(string).strip()
    except:
        return ''


class UpdateGroup(webapp2.RequestHandler):
    def get(self):
        taskqueue.Task(url='/update/group').add()

    def post(self):
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        for i in db.Query(Archive).filter('group', 'other').fetch(1500):
            group = 'other'
            for s in db.Query(Show).order('find_order').fetch(1000):
                if i.title.startswith(tuple(s.find.split(' @ '))) or i.title in s.find.split(' @ '):
                    i.group = s.path
                    i.put()
                    logging.debug('%s -> %s\n' % (i.title, s.title))
                    break


class UpdateArchive(webapp2.RequestHandler):
    def get(self):
        taskqueue.Task(url='/update/err', params={'url': 'http://m.err.ee/arhiiv/etv', 'channel': 'ETV'}).add()
        taskqueue.Task(url='/update/err', params={'url': 'http://m.err.ee/arhiiv/etv2', 'channel': 'ETV2'}).add()
        taskqueue.Task(url='/update/kanal2', params={'url': 'http://kanal2.ee/vaatasaateid'}).add()


class UpdateERR(webapp2.RequestHandler):
    def post(self):
        channel = self.request.get('channel')
        channel_url = self.request.get('url')
        soup = BeautifulSoup(urlfetch.fetch(channel_url, deadline=60).content)
        for i in soup.findAll('a', attrs={'class': 'releated jqclip'}):
            url = i['href'].replace('\n', '').strip()
            url = 'http://%s/playlist.m3u8' % url.replace('rtmp://', '').replace('rtsp://', '').replace(':80/', '/').replace('/M/', '/').replace('_definst_/', '/').replace('//', '/')
            title = i.contents[0].replace('\n', '').strip()
            date = datetime.strptime(i.find('span').contents[0].replace('\n', '').strip(), '%H:%M | %d.%m.%Y')
            group = 'other'
            for s in db.Query(Show).order('find_order').fetch(1000):
                if title.startswith(tuple(s.find.split(' @ '))) or title in s.find.split(' @ '):
                    group = s.path
                    break
            row = db.Query(Archive).filter('url', url).get()
            if not row:
                row = Archive()
            row.channel = channel
            row.group = group
            row.date = date
            row.title = title
            row.url = url
            row.put()
            logging.debug('%s %s -> %s' % (date.strftime('%d.%m.%Y %H:%M'), title, group))


class UpdateETV(webapp2.RequestHandler):
    def get(self, d):
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        channel_url = 'http://etv.err.ee/arhiiv.php?sort=paev&paev=%s' % d
        soup = BeautifulSoup(urlfetch.fetch(channel_url, deadline=60).content)
        soup = soup.find('div', attrs={'class': 'right_col_sees'})
        soup = soup.find('div', attrs={'class': 'fake_href_list'})
        if soup:
            for i in soup.findAll('a'):
                xml_url = 'http://etv.err.ee/%s' % i['href']
                html = urlfetch.fetch(xml_url, deadline=60).content
                show = BeautifulSoup(html)
                show = show.find('div', attrs={'class': 'right_col_sees'})

                date = show.find('span', attrs={'class': 'tugev valge'})
                date = date.contents[1].replace('\n', '').strip()
                date = datetime.strptime(date[:16].strip(), '%d.%m.%Y %H:%M')

                title = show.find('span', attrs={'class': 'tugev valge'})
                title = title.contents[1].replace('\n', '').strip()
                title = title[18:].strip()

                description = show.find('div', attrs={'style': 'margin:10px; padding:10px; background:#EEF2D4; border: 1px solid gray; clear:both'})
                description = description.getText()
                description = description.replace(date.strftime('(%d.%m.%Y %H:%M)'), '').replace(title, '').strip()

                url = html.split('loadFlow(\'flow_player\', \'')[1].split('\');')[0].replace('\',\'','/').replace('rtmp://', '').replace('rtsp://', '').strip()
                url = 'http://%s/playlist.m3u8' % url

                group = 'other'
                for s in db.Query(Show).order('find_order').fetch(1000):
                    if title.startswith(tuple(s.find.split(' @ '))) or title in s.find.split(' @ '):
                        group = s.path
                        break
                row = db.Query(Archive).filter('url', url).get()
                if not row:
                    row = Archive()
                    row.channel = 'ETV'
                    row.group = group
                    row.title = title
                    row.date = date
                    row.url = url
                row.description = description
                row.info_from = xml_url
                row.put()
                logging.debug('%s %s -> %s' % (date.strftime('%d.%m.%Y %H:%M'), title, group))
        else:
            logging.debug('Nothing to import!')

        previous = datetime.strptime(d, '%Y-%m-%d')-timedelta(1)
        taskqueue.Task(url='/update/etv/%s' % previous.strftime('%Y-%m-%d'), method='GET').add(queue_name='etv')


class UpdateKanal2(webapp2.RequestHandler):
    def post(self):
        channel_url = self.request.get('url')
        ids = []
        soup = BeautifulSoup(urlfetch.fetch(channel_url, deadline=60).content)
        for r in soup.findAll('div', attrs={'class': 'nettv_videod_row'}):
            for t in soup.findAll('div', attrs={'class': 'title'}):
                a = t.find('a')
                try:
                    id = a['href'].split('?videoid=')[1]
                    ids.append(id)
                except:
                    pass
        logging.debug('%s - %s' % (len(list(set(ids))), channel_url))

        for id in list(set(ids)):
            xml_url = 'http://kanal2.ee/video/playerPlaylistApi?id=%s' % id
            xml = BeautifulSoup(urlfetch.fetch(xml_url, deadline=60).content)

            try:
                date = xml.find('name')
                date = ' '.join(date.contents).replace('\n', '').strip()
                date = datetime.strptime(date[-17:-1].strip(), '%d.%m.%Y %H:%M')
                title = title[:-18].strip()
            except:
                date = datetime.strptime('01.01.1970 00:00', '%d.%m.%Y %H:%M')

            title = xml.find('name')
            title = ' '.join(title.contents).replace('\n', ' ').strip()

            episode = xml.find('episode')
            episode = ' '.join(episode.contents).replace('\n', ' ').strip()

            url = xml.find('videourl')
            url = url.contents[0].replace('\n', '').replace('http://k2vod1.mmm.elion.ee/', 'http://video.kanal2.ee/').strip()

            description = xml.find('description')
            description = ' '.join(description.contents).replace('\n', ' ').strip()

            group = 'other'
            for s in db.Query(Show).order('find_order').fetch(1000):
                if title.startswith(tuple(s.find.split(' @ '))) or title in s.find.split(' @ '):
                    group = s.path
                    break

            row = db.Query(Archive).filter('url', url).get()
            if not row:
                row = Archive()
            row.channel = 'Kanal2'
            row.group = group
            row.date = date
            row.title = title
            row.episode = episode
            row.url = url
            row.description = description
            row.info_from = xml_url
            row.put()
            logging.debug('%s %s -> %s' % (date.strftime('%d.%m.%Y %H:%M'), title, group))


app = webapp2.WSGIApplication([
        ('/update/live', UpdateLive),
        ('/update/group', UpdateGroup),
        ('/update/archive', UpdateArchive),
        ('/update/etv/(.*)', UpdateETV),
        ('/update/err', UpdateERR),
        ('/update/kanal2', UpdateKanal2),
    ], debug=True)
