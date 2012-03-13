# -*- coding: utf-8 -*-

import os
import webapp2
import jinja2
import json
import random

from google.appengine.api import channel
from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulStoneSoup
from BeautifulSoup import *


class ShowRadio(webapp2.RequestHandler):
    def get(self):
        try:
            token = channel.create_channel('raadio')
        except:
            token = False
        jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'templates')))
        template = jinja_environment.get_template('radio.html')
        self.response.out.write(template.render({'token': token}))


class UpdateRadio(webapp2.RequestHandler):
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


def get_info(url, before, after):
    try:
        string = urlfetch.fetch(url, deadline=10).content.split(before)[1].split(after)[0].decode('utf-8')
        string = ' '.join(BeautifulStoneSoup(string, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).findAll(text=True))
        return unicode(string).strip()
    except:
        return ''


app = webapp2.WSGIApplication([
        ('/', ShowRadio),
        ('/update', UpdateRadio),
        ('/_ah/channel/(.*)', ChannelConnection),
    ], debug=True)
