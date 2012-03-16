# -*- coding: utf-8 -*-

import os
import webapp2
import jinja2
import logging
from datetime import *
from operator import itemgetter

from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue

from BeautifulSoup import BeautifulStoneSoup
from BeautifulSoup import *

from users import *


class Archive(db.Model):
    _added      = db.DateTimeProperty(auto_now_add = True)
    _changed    = db.DateTimeProperty(auto_now = True)
    channel     = db.StringProperty()
    group       = db.StringProperty()
    date        = db.DateTimeProperty()
    title       = db.StringProperty()
    episode     = db.StringProperty()
    url         = db.StringProperty()
    description = db.TextProperty()
    info_from   = db.StringProperty()


class Show(db.Expando):
    title       = db.StringProperty()
    path        = db.StringProperty()
    find        = db.StringProperty()
    find_order  = db.IntegerProperty(default=9)


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
        template = jinja_environment.get_template('items.html')
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
        template = jinja_environment.get_template('items.html')
        self.response.out.write(template.render({
            'items': [items],
            'back': '/archive',
        }))


class UpdateGroup(webapp2.RequestHandler):
    def get(self):
        taskqueue.Task(url='/archive/u_group').add()

    def post(self):
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        for i in db.Query(Archive).filter('group', 'other').fetch(1000):
            group = 'other'
            for s in db.Query(Show).order('find_order').fetch(1000):
                if i.title.startswith(tuple(s.find.split(' @ '))) or i.title in s.find.split(' @ '):
                    i.group = s.path
                    i.put()
                    logging.debug('%s -> %s\n' % (i.title, s.title))
                    break


class UpdateETV(webapp2.RequestHandler):
    def get(self, d):
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        channel_url = 'http://etv.err.ee/arhiiv.php?sort=paev&paev=%s' % d
        soup = BeautifulSoup(urlfetch.fetch(channel_url, deadline=60).content)
        soup = soup.find('div', attrs={'class': 'right_col_sees'})
        soup = soup.find('div', attrs={'class': 'fake_href_list'})
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

        previous = datetime.strptime(d, '%Y-%m-%d')-timedelta(1)
        taskqueue.Task(url='/archive/u_etv/%s' % previous.strftime('%Y-%m-%d'), method='GET').add(queue_name='etv')


class UpdateArchive(webapp2.RequestHandler):
    def get(self):
        taskqueue.Task(url='/archive/u_kanal2', params={'url': 'http://kanal2.ee/vaatasaateid'}).add()

        for channel, channel_url in {'ETV':'http://m.err.ee/arhiiv/etv/', 'ETV2':'http://m.err.ee/arhiiv/etv2/'}.iteritems():
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


class UpdateKanal2(webapp2.RequestHandler):
    def get(self):
        urls = [
            # 'http://kanal2.ee/vaatasaateid',
            # 'http://kanal2.ee/vaatasaateid/?page=1',
            # 'http://kanal2.ee/vaatasaateid/?page=3',
            # 'http://kanal2.ee/vaatasaateid/?page=4',
            # 'http://kanal2.ee/vaatasaateid/?page=5',
            # 'http://kanal2.ee/vaatasaateid/Eesti-koige-koige',
            # 'http://kanal2.ee/vaatasaateid/Eesti-koige-koige?page=1',
            # 'http://kanal2.ee/vaatasaateid/Eesti-koige-koige?page=2',
            # 'http://kanal2.ee/vaatasaateid/Eestlane-ja-venelane',
            # 'http://kanal2.ee/vaatasaateid/Eestlane-ja-venelane?page=1',
            # 'http://kanal2.ee/vaatasaateid/Eestlane-ja-venelane?page=2',
            # 'http://kanal2.ee/vaatasaateid/Eestlane-ja-venelane?page=3',
            # 'http://kanal2.ee/vaatasaateid/Galileo',
            # 'http://kanal2.ee/vaatasaateid/Hooaeg',
            # 'http://kanal2.ee/vaatasaateid/Hooaeg?page=1',
            # 'http://kanal2.ee/vaatasaateid/Hooaeg?page=2',
            # 'http://kanal2.ee/vaatasaateid/Hooaeg?page=3',
            # 'http://kanal2.ee/vaatasaateid/Kaks-kanget-Venemaal',
            # 'http://kanal2.ee/vaatasaateid/Kalevipojad-1',
            # 'http://kanal2.ee/vaatasaateid/Kelgukoerad-1',
            # 'http://kanal2.ee/vaatasaateid/Kelgukoerad-1?page=1',
            # 'http://kanal2.ee/vaatasaateid/Kelgukoerad-1?page=2',
            # 'http://kanal2.ee/vaatasaateid/Kelgukoerad-1?page=3',
            # 'http://kanal2.ee/vaatasaateid/Kelgukoerad-1?page=4',
            # 'http://kanal2.ee/vaatasaateid/Kodusaade-1',
            # 'http://kanal2.ee/vaatasaateid/Kodusaade-1?page=1',
            # 'http://kanal2.ee/vaatasaateid/Kodusaade-1?page=2',
            # 'http://kanal2.ee/vaatasaateid/Kodusaade-1?page=3',
            # 'http://kanal2.ee/vaatasaateid/Kodutunne1',
            # 'http://kanal2.ee/vaatasaateid/Kodutunne1?page=1',
            # 'http://kanal2.ee/vaatasaateid/Kokasaade-Lusikas-1',
            # 'http://kanal2.ee/vaatasaateid/Kokasaade-Lusikas-1?page=1',
            # 'http://kanal2.ee/vaatasaateid/Kokasaade-Lusikas-1?page=2',
            # 'http://kanal2.ee/vaatasaateid/Kokasaade-Lusikas-1?page=3',
            # 'http://kanal2.ee/vaatasaateid/Krimi',
            # 'http://kanal2.ee/vaatasaateid/Krimi?page=1',
            # 'http://kanal2.ee/vaatasaateid/Krimi?page=2',
            # 'http://kanal2.ee/vaatasaateid/Krimi?page=3',
            # 'http://kanal2.ee/vaatasaateid/Krimi?page=4',
            # 'http://kanal2.ee/vaatasaateid/Krimi?page=5',
            # 'http://kanal2.ee/vaatasaateid/Pilvede-all',
            # 'http://kanal2.ee/vaatasaateid/Pilvede-all?page=1',
            # 'http://kanal2.ee/vaatasaateid/Pilvede-all?page=2',
            # 'http://kanal2.ee/vaatasaateid/Rooli-voim',
            # 'http://kanal2.ee/vaatasaateid/Rooli-voim?page=1',
            # 'http://kanal2.ee/vaatasaateid/Rooli-voim?page=2',
            # 'http://kanal2.ee/vaatasaateid/Rooli-voim?page=3',
            # 'http://kanal2.ee/vaatasaateid/Raakimata-lugu',
            # 'http://kanal2.ee/vaatasaateid/Raakimata-lugu?page=1',
            # 'http://kanal2.ee/vaatasaateid/Saare-sosinad',
            # 'http://kanal2.ee/vaatasaateid/Saladused-1',
            # 'http://kanal2.ee/vaatasaateid/Saladused-1?page=1',
            # 'http://kanal2.ee/vaatasaateid/Saladused-1?page=2',
            # 'http://kanal2.ee/vaatasaateid/Saladused-1?page=3',
            # 'http://kanal2.ee/vaatasaateid/Subboteja',
            # 'http://kanal2.ee/vaatasaateid/Subboteja?page=1',
            # 'http://kanal2.ee/vaatasaateid/Subboteja?page=2',
            # 'http://kanal2.ee/vaatasaateid/Subboteja?page=3',
            # 'http://kanal2.ee/vaatasaateid/Suur-lotokolmapaev',
            # 'http://kanal2.ee/vaatasaateid/Vosareporter-1',
            # 'http://kanal2.ee/vaatasaateid/Vosareporter-1?page=1',
            # 'http://kanal2.ee/vaatasaateid/Vosareporter-1?page=2',
            # 'http://kanal2.ee/vaatasaateid/Vosareporter-1?page=3',
            # 'http://kanal2.ee/vaatasaateid/Vosareporter-1?page=4',
            # 'http://kanal2.ee/vaatasaateid/Arapanija-1',
            # 'http://kanal2.ee/vaatasaateid/Arapanija-1?page=1',
            # 'http://kanal2.ee/vaatasaateid/Arapanija-1?page=2',
            # 'http://kanal2.ee/vaatasaateid/Uhikarotid-oed',
            # 'http://kanal2.ee/vaatasaateid/Uhikarotid-oed?page=1',
            # 'http://kanal2.ee/vaatasaateid/Uhikarotid-oed?page=2',
            # 'http://kanal2.ee/vaatasaateid/Reporter-',
            # 'http://kanal2.ee/vaatasaateid/Reporter-?page=1',
            # 'http://kanal2.ee/vaatasaateid/Reporter-?page=2',
            # 'http://kanal2.ee/vaatasaateid/Reporter',
            # 'http://kanal2.ee/vaatasaateid/Reporter?page=1',
            # 'http://kanal2.ee/vaatasaateid/Reporter?page=2',
            # 'http://kanal2.ee/vaatasaateid/Reporter?page=3',
            # 'http://kanal2.ee/vaatasaateid/Reporter?page=4',
            # 'http://kanal2.ee/vaatasaateid/Reporter?page=5',
            # 'http://kanal2.ee/vaatasaateid/Reporter?page=6',
            # 'http://kanal2.ee/vaatasaateid/Reporter?page=7',
        ]
        for url in urls:
             taskqueue.Task(url='/archive/u_kanal2', params={'url': url}).add()

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


app = webapp2.WSGIApplication([
        ('/archive', ShowArchive),
        ('/archive/update', UpdateArchive),
        ('/archive/u_group', UpdateGroup),
        ('/archive/u_etv/(.*)', UpdateETV),
        ('/archive/u_kanal2', UpdateKanal2),
        ('/archive/(.*)', ShowGroup),
    ], debug=True)
