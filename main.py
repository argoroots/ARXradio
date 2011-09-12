import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import channel
from google.appengine.api import urlfetch
from BeautifulSoup import BeautifulStoneSoup
from BeautifulSoup import *
from django.utils import simplejson
from random import randint


class ShowPage(webapp.RequestHandler):
    def get(self):
        token = channel.create_channel('raadio')
        path = os.path.join(os.path.dirname(__file__), 'template.html')
        self.response.out.write(template.render(path, {'token': token}))


class UpdateInfo(webapp.RequestHandler):
    def get(self):
        json = {}

        json['etv']     = get_info('http://otse.err.ee/xml/live-etv.html', '$(\'#onair\').html(\'', '\');$(\'#onairdesc')
        json['etv2']    = get_info('http://otse.err.ee/xml/live-etv2.html', '$(\'#onair\').html(\'', '\');$(\'#onairdesc')

        json['viker']   = get_info('http://otse.err.ee/xml/live-vikerraadio.html', '$(\'#onair\').html(\'', '\');$(\'#onairdesc')
        json['klassika']= get_info('http://otse.err.ee/xml/live-klassikaraadio.html', '$(\'#onair\').html(\'', '\');$(\'#onairdesc')
        json['r2']      = get_info('http://otse.err.ee/xml/live-r2.html', '$(\'#onair\').html(\'', '\');$(\'#onairdesc')
        json['r4']      = get_info('http://otse.err.ee/xml/live-r4.html', '$(\'#onair\').html(\'', '\');$(\'#onairdesc')
        json['tallinn'] = get_info('http://otse.err.ee/xml/live-raadiotallinn.html', '$(\'#onair\').html(\'', '\');$(\'#onairdesc')

        json['elmar']   = get_info('http://www.elmar.ee/', '<div class="onair">', '</div>')
        json['kuku']    = get_info('http://www.kuku.ee/', '<span class="pealkiri">Hetkel eetris</span>', '</a>')
        json['mania']   = get_info('http://www.mania.ee/eeter.php?rnd='+str(randint(1, 1000000)), '<font color=\'ffffff\'>', '</font>')
        json['sky']     = get_info('http://www.skyplus.fm/ram/nowplaying_main.html?rnd='+str(randint(1, 1000000)), '<span class="hetkeleetris">', '</span>')
        json['r3']      = get_info('http://www.raadio3.ee/ram/nowplaying_main.html?rnd='+str(randint(1, 1000000)), '<span class="eetris2">', '</body>')
        json['star']    = get_info('http://rds.starfm.ee/jsonRdsInfo.php?Name=Star&rnd='+str(randint(1, 1000000)), '({"currentArtist":"', '","nextArtist"').replace('","currentSong":"', ' - ')
        json['power']   = get_info('http://rds.power.ee/jsonRdsInfo.php?Name=Power&rnd='+str(randint(1, 1000000)), '({"currentArtist":"', '","nextArtist"').replace('","currentSong":"', ' - ')

        json_str = simplejson.dumps(json)
        channel.send_message('raadio', json_str)

        self.response.headers['Content-type'] = 'application/json'
        self.response.out.write(json_str)


class ChannelConnection(webapp.RequestHandler):
    def post(self, type):
        type = type.strip('/')


def get_info(url, before, after):
    try:
        string = urlfetch.fetch(url, deadline=10).content.split(before)[1].split(after)[0].decode('utf-8')
        string = ' '.join(BeautifulStoneSoup(string, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).findAll(text=True))
        return unicode(string).strip()
    except:
        return ''


def main():
    application = webapp.WSGIApplication([
        ('/', ShowPage),
        ('/update', UpdateInfo),
        ('/_ah/channel/(.*)', ChannelConnection),
    ], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
