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
        'find':  u'ajavaod',
        'group':  'ajavaod',
        'name':  u'Ajavaod'
    }, {
        'find':  u'aktuaalne kaamera',
        'group':  'aktuaalnekaamera',
        'name':  u'Aktuaalne kaamera'
    }, {
        'find':  u'arktikast antarktikasse',
        'group':  'arktikastantarktikasse',
        'name':  u'Arktikast Antarktikasse'
    }, {
        'find':  u'batareja',
        'group':  'batareja',
        'name':  u'Batareja'
    }, {
        'find':  u'eesti lood',
        'group':  'eestilood',
        'name':  u'Eesti lood'
    }, {
        'find':  u'jüri üdi klubi',
        'group':  'jyriydiklubi',
        'name':  u'Jüri Üdi klubi'
    }, {
        'find':  u'kapital',
        'group':  'kapital',
        'name':  u'Kapital'
    }, {
        'find':  u'nöbinina',
        'group':  'nobinina',
        'name':  u'Nöbinina'
    }, {
        'find':  u'osoon',
        'group':  'osoon',
        'name':  u'Osoon'
    }, {
        'find':  u'pealtnägija',
        'group':  'pealtnagija',
        'name':  u'Pealtnägija'
    }, {
        'find':  u'puutepunkt',
        'group':  'puutepunkt',
        'name':  u'Puutepunkt'
    }, {
        'find':  u'ringvaade',
        'group':  'ringvaade',
        'name':  u'Ringvaade'
    }, {
        'find':  u'teatrivara',
        'group':  'teater',
        'name':  u'Teater'
    }, {
        'find':  u'telelavastus',
        'group':  'teater',
        'name':  u'Teater'
    }, {
        'find':  u'lastelavastus',
        'group':  'teater',
        'name':  u'Teater'
    }, {
        'find':  u'terevisioon',
        'group':  'terevisioon',
        'name':  u'Terevisioon'
    }, {
        'find':  u'välisilm',
        'group':  'valisilm',
        'name':  u'Välisilm'
    }, {
        'find':  u'õnne 13',
        'group':  'onne13',
        'name':  u'Õnne 13'
    }, {
        'find':  u'ajalik ja ajatu',
        'group':  'ajalikjaajatu',
        'name':  u'Ajalik ja ajatu'
    }, {
        'find':  u'lastetuba',
        'group':  'lastetuba',
        'name':  u'Lastetuba'
    }, {
        'find':  u'meie inimesed',
        'group':  'meieinimesed',
        'name':  u'Meie inimesed'
    }, {
        'find':  u'püramiidi tipus',
        'group':  'pyramiiditipus',
        'name':  u'Püramiidi tipus'
    }, {
        'find':  u'vabariigi kodanikud',
        'group':  'vabariigikodanikud',
        'name':  u'Vabariigi kodanikud'
    }, {
        'find':  u'op!',
        'group':  'op',
        'name':  u'OP!'
    }, {
        'find':  u'luuletus',
        'group':  'luuletus',
        'name':  u'Luuletus'
    }, {
        'find':  u'100 luulepärli',
        'group':  'luuletus',
        'name':  u'Luuletus'
    }, {
        'find':  u'riigikogu infotund',
        'group':  'riigikoguinfotund',
        'name':  u'Riigikogu infotund'
    }, {
        'find':  u'rakett 69',
        'group':  'rakett69',
        'name':  u'Rakett 69'
    }, {
        'find':  u'eesti top 7',
        'group':  'eestitop7',
        'name':  u'Eesti TOP 7'
    }, {
        'find':  u'xxxxxx',
        'group':  'other',
        'name':  u'. . .'
    }]


class Archive(db.Model):
    _added   = db.DateTimeProperty(auto_now_add = True)
    _changed = db.DateTimeProperty(auto_now = True)
    channel  = db.StringProperty()
    group    = db.StringProperty()
    date     = db.DateTimeProperty()
    title    = db.StringProperty()
    url      = db.StringProperty()


class ShowArchive(webapp2.RequestHandler):
    def get(self):
        recent = []
        for i in db.Query(Archive).order('-date').fetch(5):
            recent.append({
                'url': 'http://%s/playlist.m3u8' % i.url.replace('rtsp://media.err.ee:80/', 'media.err.ee/').replace('/M/', '/').replace('_definst_/', '/').replace('//', '/'),
                'title': i.title,
                'info': i.date.strftime('%d.%m.%Y %H:%M'),
                'type': 'video',
            })

        groups = {}
        for s in SHOWS:
            if db.Query(Archive, keys_only=True).filter('group', s['group']).get():
                groups[s['group']] = {
                    'url': '/archive/%s' % s['group'],
                    'title': s['name'],
                }
        groups = sorted(groups.values(), key=itemgetter('title'))

        jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'templates')))
        template = jinja_environment.get_template('items.html')
        self.response.out.write(template.render({
            'items': [recent, groups],
            'back': '/',
        }))


class ShowGroup(webapp2.RequestHandler):
    def get(self, group):
        items = []
        for i in db.Query(Archive).filter('group', group).order('-date').fetch(100):
            items.append({
                'url': 'http://%s/playlist.m3u8' % i.url.replace('rtsp://media.err.ee:80/', 'media.err.ee/').replace('/M/', '/').replace('_definst_/', '/').replace('//', '/'),
                'title': i.title,
                'info': i.date.strftime('%d.%m.%Y %H:%M'),
                'type': 'video',
            })

        jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'templates')))
        template = jinja_environment.get_template('items.html')
        self.response.out.write(template.render({
            'items': [items],
            'back': '/archive',
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
                    if title.lower().find(s['find']) > -1:
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
        ('/archive', ShowArchive),
        ('/archive/update', UpdateArchive),
        ('/archive/(.*)', ShowGroup),
    ], debug=True)
