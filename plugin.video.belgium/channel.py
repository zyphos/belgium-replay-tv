#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import urllib
import urllib2
import re
import os
import os.path
import sys
import pickle
from htmlentitydefs import name2codepoint

try:
    import xbmcplugin, xbmcgui, xbmcaddon, xbmc
    in_xbmc = True
    addon = xbmcaddon.Addon(id='plugin.video.belgium')
    home = addon.getAddonInfo('path')
    userdata_path = xbmc.translatePath(addon.getAddonInfo('profile') ).decode("utf-8")
    print 
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
    args['name'] = name
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

class History(object):
    """Store last 10 channel and category you view video
    history = [('channel_id','category_name', 'category_url')]
    """
    def __init__(self):
        self.filename = userdata_path + 'history.dump'
    
    def update(self, context):
        if 'category_id' not in context or 'category_url' not in context or 'category_name' not in context:
            return 
        channel_id = context['channel_id']
        category_id = context['category_id']
        category_name = context['category_name']
        category_url = context['category_url']
        
        categories = self._read()
        # 1. check if already set
        pos = None
        for i, category in enumerate(categories):
            c_channel_id, c_id, c_name, c_url = category
            if c_channel_id == channel_id and c_id == category_id:
                pos = i
                break
        if pos is None:
            # Not found, add it
            categories.insert(0, (channel_id, category_id, category_name, category_url))
            categories = categories[:10] # Limit to 10
            self._write(categories)
        elif pos != 0: # 0 = nothing to do
            categories.insert(0, categories.pop(pos))
            self._write(categories)

    def show(self, channels):
        categories = self._read()
        for channel_id, category_id, category_name, category_url in categories:
            iconimage = None
            channel_name = channels[channel_id]['name']
            addDir('%s - %s' % (channel_name, category_name), iconimage, channel_id=channel_id, url=category_url, action='show_videos', id=category_id)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
    def _read(self):
        if not os.path.isfile(self.filename):
            return []
        with open(self.filename, 'r') as f:
            categories = pickle.load(f)
        return categories
    
    def _write(self, categories):
        with open(self.filename, 'w') as f:
            pickle.dump(categories, f)
    
class Channel(object):
    def __init__(self, context):
        self.channel_id = context.get('channel_id')
        self.main_url = self.get_main_url()
        if in_xbmc:
            self.icon = xbmc.translatePath(os.path.join(home, 'resources/' + context['icon']))
        else:
            self.icon = context.get('icon')
        action = context.get('action')
        print 'action:', action
        print 'context:'
        print context
        print
        if action == 'show_categories':
            self.get_categories()
        elif action == 'show_subcategories':
            self.get_subcategories(context)
        elif action == 'show_videos':
            self.get_videos(context)
        elif action == 'play_video':
            History().update(context)
            self.play_video(context)
        elif action == 'get_lives':
            self.get_lives(context)
        elif action == 'play_live':
            self.play_live(context)
        elif action == 'scan_empty':
            self.scan_empty(context)
            
    def set_main_url(self):
        return ''
            
    def get_categories(self, skip_empty_id = True):
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
