# -*- coding: utf-8 -*-

import os
import webapp2
import jinja2
from datetime import *
from operator import itemgetter

from google.appengine.ext import db
from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulStoneSoup
from BeautifulSoup import *


SHOWS = [{
        'find': 'ajavaod',
        'group': 'ajavaod',
        'name': 'Ajavaod'
    }, {
        'find': 'aktuaalne kaamera',
        'group': 'aktuaalnekaamera',
        'name': 'Aktuaalne kaamera'
    }, {
        'find':  'arktikast antarktikasse',
        'group': 'arktikastantarktikasse',
        'name':  'Arktikast Antarktikasse'
    }, {
        'find':  'batareja',
        'group': 'batareja',
        'name':  'Batareja'
    }, {
        'find':  'eesti lood',
        'group': 'eestilood',
        'name':  'Eesti lood'
    }, {
        'find':  'jüri üdi klubi',
        'group': 'jyriydiklubi',
        'name':  'Jüri Üdi klubi'
    }, {
        'find':  'kapital',
        'group': 'kapital',
        'name':  'Kapital'
    }, {
        'find':  'nöbinina',
        'group': 'nobinina',
        'name':  'Nöbinina'
    }, {
        'find':  'osoon',
        'group': 'osoon',
        'name':  'Osoon'
    }, {
        'find':  'pealtnägija',
        'group': 'pealtnagija',
        'name':  'Pealtnägija'
    }, {
        'find':  'puutepunkt',
        'group': 'puutepunkt',
        'name':  'Puutepunkt'
    }, {
        'find':  'ringvaade',
        'group': 'ringvaade',
        'name':  'Ringvaade'
    }, {
        'find':  'teatrivara',
        'group': 'teater',
        'name':  'Teater'
    }, {
        'find':  'telelavastus',
        'group': 'teater',
        'name':  'Teater'
    }, {
        'find':  'lastelavastus',
        'group': 'teater',
        'name':  'Teater'
    }, {
        'find':  'terevisioon',
        'group': 'terevisioon',
        'name':  'Terevisioon'
    }, {
        'find':  'välisilm',
        'group': 'valisilm',
        'name':  'Välisilm'
    }, {
        'find':  'õnne 13',
        'group': 'onne13',
        'name':  'Õnne 13'
    }, {
        'find':  'ajalik ja ajatu',
        'group': 'ajalikjaajatu',
        'name':  'Ajalik ja ajatu'
    }, {
        'find':  'lastetuba',
        'group': 'lastetuba',
        'name':  'Lastetuba'
    }, {
        'find':  'meie inimesed',
        'group': 'meieinimesed',
        'name':  'Meie inimesed'
    }, {
        'find':  'püramiidi tipus',
        'group': 'pyramiiditipus',
        'name':  'Püramiidi tipus'
    }, {
        'find':  'vabariigi kodanikud',
        'group': 'vabariigikodanikud',
        'name':  'Vabariigi kodanikud'
    }, {
        'find':  'op!',
        'group': 'op',
        'name':  'OP!'
    }, {
        'find':  'xxxxxx',
        'group': 'other',
        'name':  '...'
    }]


class Archive(db.Model):
    channel = db.StringProperty()
    group   = db.StringProperty()
    date    = db.DateTimeProperty()
    title   = db.StringProperty()
    url     = db.StringProperty()


class ShowArchive(webapp2.RequestHandler):
    def get(self, group):
        group = group.strip('/')
        if group:
            items = []
            for i in db.Query(Archive).filter('group', group).order('-date').fetch(100):
                items.append({
                    'url': 'http://%s/playlist.m3u8' % i.url.replace('rtsp://media.err.ee:80/', 'media.err.ee/').replace('/M/', '/').replace('_definst_/', '/').replace('//', '/'),
                    'date': i.date.strftime('%d.%m.%Y %H:%M'),
                    'title': i.title,
                    'is_video': True,
                })
            back = '/archive'
        else:
            items = {}
            for s in SHOWS:
                if db.Query(Archive, keys_only=True).filter('group', s['group']).get():
                    items[s['group']] = {
                        'url': '/archive/%s' % s['group'],
                        'title': s['name'].decode('utf-8'),
                    }
            items = sorted(items.values(), key=itemgetter('title'))
            back = '/'

        jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'templates')))
        template = jinja_environment.get_template('archive.html')
        self.response.out.write(template.render({
            'items': items,
            'back': back,
        }))


class UpdateArchive(webapp2.RequestHandler):
    def get(self):
        for channel, channel_url in {'ETV':'http://m.err.ee/arhiiv/etv/', 'ETV2':'http://m.err.ee/arhiiv/etv2/'}.iteritems():
            soup = BeautifulSoup(urlfetch.fetch(channel_url, deadline=60).content)
            for i in soup.findAll('a', attrs={'class': 'releated jqclip'}):
                url = i['href'].replace('\n', '').strip()
                title = i.contents[0].replace('\n', '').strip()
                date = datetime.strptime(i.find('span').contents[0].replace('\n', '').strip(), '%H:%M | %d.%m.%Y')
                group = 'other'
                for s in SHOWS:
                    if title.lower().find(s['find'].decode('utf-8')) > -1:
                        group = s['group']
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


app = webapp2.WSGIApplication([
        ('/archive/update', UpdateArchive),
        ('/archive(.*)', ShowArchive),
    ], debug=True)
