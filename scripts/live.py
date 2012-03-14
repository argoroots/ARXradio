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

        items = [[
            {'url': 'http://193.40.133.138:1935/live/etv/playlist.m3u8', 'type': 'video', 'id': u'etv', 'title': u'ETV'},
            {'url': 'http://193.40.133.138:1935/live/etv2/playlist.m3u8', 'type': 'video', 'id': u'etv2', 'title': u'ETV 2'},
            {'url': '/archive', 'icon': 'A', 'info': 'Arhiiv'},
            ], [
            {'url': 'http://193.40.133.138:1935/live/vikerraadio/playlist.m3u8', 'type': 'audio', 'id': u'viker', 'title': u'Vikerraadio'},
            {'url': 'http://193.40.133.138:1935/live/klassikaraadio/playlist.m3u8', 'type': 'audio', 'id': u'klassika', 'title': u'Klassikaraadio'},
            {'url': 'http://193.40.133.138:1935/live/raadio2/playlist.m3u8', 'type': 'audio', 'id': u'r2', 'title': u'Raadio 2'},
            {'url': 'http://193.40.133.138:1935/live/r2-2/playlist.m3u8', 'type': 'audio', 'id': u'r2.2', 'title': u'Raadio 2.2'},
            {'url': 'http://193.40.133.138:1935/live/raadiotallinn/playlist.m3u8', 'type': 'audio', 'id': u'tallinn', 'title': u'Tallinn'},
            ], [
            {'url': 'http://striiming.trio.ee:8008/elmar.mp3', 'type': 'audio', 'id': u'elmar', 'title': u'Elmar'},
            {'url': 'http://striiming.trio.ee:8008/kuku.mp3', 'type': 'audio', 'id': u'kuku', 'title': u'Kuku'},
            {'url': 'http://icecast.linxtelecom.com:8000/mania.mp3.m3u', 'type': 'audio', 'id': u'mania', 'title': u'Mania'},
            {'url': 'http://radio.zzz.ee/nommeraadio.m3u', 'type': 'audio', 'id': u'nõmme', 'title': u'Nõmme'},
            {'url': 'http://streamer.akaver.com/streamgen.php?stream=skyplus&format=mp3&quality=hi', 'type': 'audio', 'id': u'sky', 'title': u'Sky Plus'},
            {'url': 'http://striiming.trio.ee:8008/uuno.mp3', 'type': 'audio', 'id': u'uuno', 'title': u'Uuno'},
            {'url': 'http://streamer.akaver.com/streamgen.php?stream=raadio3&format=mp3&quality=hi', 'type': 'audio', 'id': u'r3', 'title': u'Raadio 3'},
            {'url': 'http://streamer.akaver.com/streamgen.php?stream=starfm&format=mp3&quality=hi', 'type': 'audio', 'id': u'star', 'title': u'Star FM'},
            {'url': 'http://streamer.akaver.com/streamgen.php?stream=powerhit&format=mp3&quality=hi', 'type': 'audio', 'id': u'power', 'title': u'Power Hit'},
            ], [{'url': 'http://www.netiraadio.ee:8000/folgisobrad', 'type': 'audio', 'id': u'folk', 'title': u'Folgisõbrad'},
            {'url': 'http://www.netiraadio.ee:8000/jazzivarvid', 'type': 'audio', 'id': u'jazz', 'title': u'Jazzi värvid'},
            {'url': 'http://www.netiraadio.ee:8000/klubibiit', 'type': 'audio', 'id': u'klubi', 'title': u'Klubi biit'},
            {'url': 'http://www.netiraadio.ee:8000/kuldsedajad', 'type': 'audio', 'id': u'kuldne', 'title': u'Kuldsed ajad'},
            {'url': 'http://www.netiraadio.ee:8000/puhastraat', 'type': 'audio', 'id': u'traat', 'title': u'Puhas traat'},
            {'url': 'http://www.netiraadio.ee:8000/sinuhetked', 'type': 'audio', 'id': u'sinu', 'title': u'Sinu hetked'},
            {'url': 'http://www.netiraadio.ee:8000/teistsugune', 'type': 'audio', 'id': u'teistsugune', 'title': u'Teistsugune'},
            {'url': 'http://www.netiraadio.ee:8000/tumedadlood', 'type': 'audio', 'id': u'tume', 'title': u'Tumedad lood'},
        ]]

        jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'templates')))
        template = jinja_environment.get_template('items.html')
        self.response.out.write(template.render({
            'items': items,
            'token': token,
        }))


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
