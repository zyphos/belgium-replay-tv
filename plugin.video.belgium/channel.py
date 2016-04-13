#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import urllib, urllib2, re, os, sys, time, datetime
import sqlite3
from htmlentitydefs import name2codepoint

try:
    import xbmcplugin, xbmcgui, xbmcaddon, xbmc
    in_xbmc = True
    __settings__ = xbmcaddon.Addon(id='plugin.video.belgium')
    __language__ = __settings__.getLocalizedString
    home = __settings__.getAddonInfo('path')
except:
    in_xbmc = False 

def get_url(url, referer='http://www.google.com'):
    if not in_xbmc:
        print 'Get url:', url
    req = urllib2.Request(url)
    req.addheaders = [('Referer', referer),
            ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100101 Firefox/11.0 ( .NET CLR 3.5.30729)')]
    response = urllib2.urlopen(req)
    data = response.read()
    response.close()
    return data

def uniquify(list):
    new_list = []
    for e in list:
        if e not in new_list:
            new_list.append(e)
    return new_list

remove_accent_regex = re.compile(r"""&([a-zA-Z])(acute;|circ;|grave;)""")
def removehtml(txt):
    return remove_accent_regex.sub(r'\1', txt)

def clear_entity(txt):
    new_txt = ''
    for c in txt:
        if ord(c) > 128:
            new_txt += '.'
        else:
            new_txt += c
    return new_txt

def htmlentitydecode(s):
    s = clear_entity(s)
    return re.sub('&(%s);' % '|'.join(name2codepoint),
            lambda m: unichr(name2codepoint[m.group(1)]), s)

def time2str(t):
    time_division = [('s', 60), ('m', 60), ('h', 24)]
    time = []
    for symbol, duration in time_division:
        v = t % duration
        if v > 0:
            time.insert(0, str(v) + symbol)
        t = t / duration
    return ' '.join(time)

def addLink(name, url, iconimage, **kwargs):
    name = name.replace('&#039;', "'").replace('&#034;', '"')
    if not in_xbmc:
        print 'Title: [' + name + ']'
        print 'Img:', iconimage
        print 'Url:', url
        print
        return True
    if 'Title' not in kwargs:
        kwargs['Title'] = name
    ok = True
    liz = xbmcgui.ListItem(name, iconImage='DefaultVideo.png', thumbnailImage=iconimage)
    liz.setInfo(type='Video', infoLabels=kwargs)
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)
    return ok

def array2url(**args):
    vals = []
    for key, val in args.iteritems():
        vals.append(key + '=' + urllib.quote_plus(val))      
    return sys.argv[0] + "?" + '&'.join(vals)

def addDir(name, iconimage, **args):
    name = name.replace('&#039;', "'").replace('&#034;', '"')
    u = array2url(**args)
    if not in_xbmc:
        print 'Title: [' + name + ']'
        print 'Img:', iconimage
        print 'Url:', u
        for key in args:
            print key + ': ' + args[key]
        print
        return True
    
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={ "Title": name })
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

def playUrl(url):
    print 'Play url:', url
    if not in_xbmc:
        return True
    liz = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz)

class Database(object):
    def __init__(self, name):
        self.name = name
        profilePath = xbmc.translatePath(__settings__.getAddonInfo('profile'))
        if not os.path.exists(profilePath):
            os.makedirs(profilePath)
        self.databasePath = os.path.join(profilePath, name)
        sqlite3.register_adapter(datetime.datetime, self.adapt_datetime)
        sqlite3.register_converter('timestamp', self.convert_datetime)
        self.conn = sqlite3.connect(self.databasePath, detect_types=sqlite3.PARSE_DECLTYPES)
        self.create_tables()
    
    @staticmethod
    def adapt_datetime(ts):
        # http://docs.python.org/2/library/sqlite3.html#registering-an-adapter-callable
        return time.mktime(ts.timetuple())

    @staticmethod
    def convert_datetime(ts):
        try:
            return datetime.datetime.fromtimestamp(float(ts))
        except ValueError:
            return None
    
    def create_tables(self):
        cr = self.conn.cursor()
        cr.execute('CREATE TABLE IF NOT EXISTS category(id INTEGER PRIMARY KEY, parent_id INTEGER, url STR, icon STR, name STR, last_update TIMESTAMP)')
        cr.close()
    
    def get_cr(self):
        return self.conn.cursor()
    
    def add_cat(self, cr, name='', url=None, icon=None, parent_id=None):
        last_update = datetime.datetime.now()
        cr.execute('INSERT INTO category(parent_id, url, icon, name, last_update) VALUES(?, ?, ?, ?, ?)', [parent_id, url, icon, name, last_update])
    
    def reset_cat(self, cr=None):
        sql = 'DELETE FROM category WHERE 1'
        if cr is None:
            cr = self.conn.cursor()
            cr.execute(sql)
            cr.close()
            return
        cr.execute(sql)
    
    def get_cats(self, parent_id=None):
        cr = self.conn.cursor()
        cr.execute('SELECT url, icon, name, last_update FROM category WHERE parent_id=?', [parent_id])
        res = []
        for row in cr:
            res.append(row)
        cr.close()
        return res
        
    
class Channel(object):
    cache_db = None

    def __init__(self, context):
        self.channel_id = context.get('channel_id')
        self.main_url = self.get_main_url()
        if in_xbmc:
            self.icon = xbmc.translatePath(os.path.join(home, 'resources/' + context['icon']))
            if self.cache_db is not None:
                self.db = Database(self.cache_db)
        else:
            self.icon = context.get('icon')
        action = context.get('action')
        print 'action:', action
        print 'context:'
        print context
        print
        actions = {'show_categories': self.show_categories,
                   'show_subcategories': self.get_subcategories,
                   'show_videos': self.get_videos,
                   'play_video': self.play_video,
                   'get_lives': self.get_lives,
                   'play_live': self.play_live,
                   'scan_empty': self.scan_empty,
                   }
        if action in actions:
            actions[action](context)
            
    def set_main_url(self):
        return ''
    
    def show_categories(self, context, skip_empty_id = True):
        is_subcat = context.get('subcat') == '1'
        categories = self.get_categories(context, skip_empty_id)
        
        def show_them(cats):
            for category in cats:
                url, id, img, name = category
                name = htmlentitydecode(name)
                addDir(name, img, channel_id=self.channel_id, url=url, action='show_videos', id=id)
        if isinstance(categories, dict):
            if is_subcat:
                show_them(categories[categories.keys()[int(context.get('url'))]])
            else:
                for i, cat_name in enumerate(categories):
                    addDir(cat_name, 'DefaultVideo.png', channel_id=self.channel_id, url=str(i), action='show_categories', subcat='1')
        else:
            show_them(categories)
            
    def get_categories(self, datas, skip_empty_id = True):
        pass
    
    def get_subcategories(self, datas):
        pass
        
    def get_videos(self, datas):
        pass
    
    def play_video(self, datas):
        pass
    
    def get_lives(self, datas):
        pass
    
    def play_live(self, datas):
        pass
    
    def scan_empty(self, datas):
        cats = []
        def addCat(name, img, **kargs):
            cats.append(kargs)
        vids = []
        def addVid(title, vurl, img):
            vids.append(1)
        self_module = sys.modules[__name__]
        self_module.addDir = addCat
        self_module.addLink = addVid
        self.get_categories(False)
        new_id2skip = []
        i = 0
        nb = len(cats)
        cat_done = []
        for cat in cats:
            print i, '/', nb
            i += 1
            vids = []
            self.get_videos(cat)
            if not len(vids):
                new_id2skip.append(cat['id'])
            cat_done.append(cat['id'])
            print 'done: ' + ','.join(cat_done)
            print 'id2skip: ' + ','.join(new_id2skip)
