# -*- coding: utf-8 -*-

import os
import webapp2
import jinja2
from datetime import *
from operator import itemgetter

from google.appengine.ext import db
from google.appengine.api import channel

from database import *


class ShowLive(webapp2.RequestHandler):
    def get(self):
        if not Authorize(self):
            return

        items = [[
            {'url': '/archive', 'icon': 'A', 'info': 'Arhiiv'}
            ], [
            {'url': 'http://193.40.133.138:1935/live/etv/playlist.m3u8', 'type': 'video', 'id': u'etv', 'title': u'ETV'},
            {'url': 'http://193.40.133.138:1935/live/etv2/playlist.m3u8', 'type': 'video', 'id': u'etv2', 'title': u'ETV 2'}
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


        token = channel.create_channel('raadio')

        jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'templates')))
        template = jinja_environment.get_template('show.html')
        self.response.out.write(template.render({
            'items': items,
            'token': token,
        }))


class ShowArchive(webapp2.RequestHandler):
    def get(self):
        if not Authorize(self):
            return

        live = [{'url': '/', 'icon': 'L', 'info': 'Live'}]

        recent = []
        for i in db.Query(Archive).order('-date').fetch(5):
            recent.append({
                'url': i.url,
                'title': i.title,
                'info': i.date.strftime('%d.%m.%Y %H:%M'),
                'type': 'video',
            })

        groups = {}
        for s in db.Query(Show).order('title').fetch(1000):
            groups[s.path] = {
                'url': '/archive/%s' % s.path,
                'title': s.title,
                'info': db.Query(Archive, keys_only=True).filter('group', s.path).count()
            }
        groups = sorted(groups.values(), key=itemgetter('title'))


        jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'templates')))
        template = jinja_environment.get_template('show.html')
        self.response.out.write(template.render({
            'items': [live, recent, groups],
        }))


class ShowGroup(webapp2.RequestHandler):
    def get(self, group):
        if not Authorize(self):
            return

        items = []
        for i in db.Query(Archive).filter('group', group).order('-date').fetch(1000):
            items.append({
                'url': i.url,
                'title': i.title,
                'info': i.date.strftime('%d.%m.%Y %H:%M'),
                'type': 'video',
            })
        if group == 'other':
            items = sorted(items, key=itemgetter('title'))

        jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'templates')))
        template = jinja_environment.get_template('show.html')
        self.response.out.write(template.render({
            'items': [items],
            'back': '/archive',
        }))


app = webapp2.WSGIApplication([
        ('/', ShowLive),
        ('/archive', ShowArchive),
        ('/archive/(.*)', ShowGroup),
    ], debug=True)
