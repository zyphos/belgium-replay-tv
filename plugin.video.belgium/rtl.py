#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import re

import channel

channels = {'rtltvi': 'http://www.rtl.be/rtltvi',
            'clubrtl': 'http://www.clubrtl.be',
            'plugrtl': 'http://www.plugrtl.be'}

id2skip = [str(x) for x in [2601,4497,3098,4452,4509,1585,1103,4388,657,767,4296,4468,701]]
only_good_cat = {'2616': 'Le journal'}

class Channel(channel.Channel):
    def get_main_url(self):
        return 'http://www.rtl.be/' 
    
    def get_categories(self, datas, skip_empty_id = True):
        # Get all categories
        data = channel.get_url(self.main_url + self.channel_id + '/page/toutes-les-videos/237.aspx')
        regex = r"""(?i)""" + self.channel_id + r"""(/categorie/[^/]+/(\d+)\.aspx)[^>]+><img[^"]+"([^"]+)[^>]*></a>\s*<h3>([^<]+)"""
        all_categories = {}
        for url, id, img, name in re.findall(regex, data):
            all_categories[int(id)] = (url, id, img, name)
            #if skip_empty_id and id in id2skip:
            #    continue
            #if id not in only_good_cat or name.find(only_good_cat[id]) != -1:
            #    channels_data[url] = (name, img, id)
        
        # Get structure
        data = channel.get_url(self.main_url + self.channel_id + '/')
        data = data.split('class=SubmenuPopup ')[2]
        data = data.split('</DIV></li></ul>')[0]
        datas = data.replace('</H3>','<H3>').split('<H3>')[1:]
        categories = {}
        regex = r"""(?i)""" + self.channel_id + r"""/categorie/[^/]+/(\d+)\.aspx[^>]+>"""
        for i in range(len(datas)/2):
            title = datas[i*2]
            content = datas[i*2+1]
            subcats = []
            for id in re.findall(regex, content):
                subcats.append(all_categories[int(id)])
            categories[title] = subcats
        return categories
    
    def get_categories_old(self, datas, skip_empty_id = True):
        data = channel.get_url(self.main_url + self.channel_id + '/page/toutes-les-videos/237.aspx')
        regex = r"""(?i)""" + self.channel_id + r"""(/categorie/[^/]+/(\d+)\.aspx)[^>]+><img[^"]+"([^"]+)[^>]*></a>\s*<h3>([^<]+)"""
        print regex
        channels = []
        channels_data = {}
        for url, id, img, name in re.findall(regex, data):
            if skip_empty_id and id in id2skip:
                continue
            if id not in only_good_cat or name.find(only_good_cat[id]) != -1:
                channels_data[url] = (name, img, id)
        channels = channels_data.keys()
        channels.sort(lambda x, y: cmp(str.lower(channels_data[x][0]), str.lower(channels_data[y][0])))
        for url in channels:
            name, img, id = channels_data[url]
            name = channel.htmlentitydecode(name)
            channel.addDir(name, img, channel_id=self.channel_id, url=url, action='show_videos', id=id)

    def get_videos(self, datas):
        url = datas.get('url')
        if datas.get('direct', False):
            self.get_direct_videos()
            return
        data = channel.get_url(self.main_url + self.channel_id + url)
        regex = r"""<img src="([^"]+)"[^>]*><A class=[^']+'(\d+)[^>]+>[a-z0-9A-Z\s]+<BR>([^<]+)"""
        ids = []
        for img, id, title in re.findall(regex, data):
            if id in ids:
                continue
            ids.append(id)
            vurl = channel.array2url(channel_id=self.channel_id, url=id, action='play_video')
            channel.addLink(channel.htmlentitydecode(title), vurl, img)
        regex = r"""<A href="/""" + self.channel_id + """/video/(\d+)\.aspx[^"]*"[^>]*><img src="([^"]+?)"[^>]*></A>\s*?<H3>([^<]+)</H3>"""
        for id, img, title in re.findall(regex, data):
            if id in ids:
                continue
            ids.append(id)
            vurl = channel.array2url(channel_id=self.channel_id, url=id, action='play_video')
            channel.addLink(channel.htmlentitydecode(title), vurl, img)

    def get_direct_videos(self):
        url = 'http://www.rtl.be/rtltvi/page/les-directs-rtl-tvi/258.aspx'
        data = channel.get_url(url)
        regex = r"""OtherLiveItem(Big|)Img ><A href="http://www.rtl.be/[^/]+/[^/]+/[^/]+/(\d+)\.aspx"><img src="([^"]+)"[^>]+></A></DIV>\s+<[^>]+>([^<]+)</DIV>\s+<[^>]+>([^<]+)"""
        for big, id, img, title, time in re.findall(regex, data):
            title = channel.htmlentitydecode(title + ' - ' + time)
            vurl = channel.array2url(channel_id=self.channel_id, url=id, action='play_video', direct='1')
            channel.addLink(title, vurl, img)

    def play_video(self, datas):
        id = datas.get('url')
        if datas.get('direct'):
            id = self.get_direct_video_id(id)
        if channel.in_xbmc:
            from elementtree import ElementTree
        else:
            from xml.etree import ElementTree
        data = channel.get_url(self.main_url + self.channel_id + '/GetFlashParams.aspx?id=%s&bEmbed=0&sDummyPath=' % id)
        tree = ElementTree.fromstring(data)
        vpo = tree.find('VPO')
        title, img, url = vpo.find('Title').text, vpo.find('Thumbnail').text, vpo.find('URL').text
        channel.playUrl(url)
    
    def get_direct_video_id(self, id):
        url = 'http://www.rtl.be/rtltvi/live//' + id + '.aspx'
        data = channel.get_url(url)
        regex = r"""VideoID=(\d+)"""
        id = re.findall(regex, data)[0]
        return id


if __name__ == "__main__":
    import sys
    args = sys.argv
    if len(args) == 1:
        print 'rtltvi clubrtl plugrtl'
    elif len(args) == 3:
        if args[2] == 'direct':
            Channel({'channel_id': args[1], 'action': 'show_videos', 'direct': 1})
        elif args[2] == 'scan_empty':
            Channel({'channel_id': args[1], 'action': 'scan_empty'})
        else:
            Channel({'channel_id': args[1], 'action': 'show_subcategories', 'url':args[2]})
    elif len(args) == 4:
        if args[2] == 'play':
            Channel({'channel_id': args[1], 'action': 'play_video', 'url':args[3]})
        else:
            Channel({'channel_id': args[1], 'action': 'show_videos', 'url':args[3]})
    elif len(args) == 5:
        Channel({'channel_id': args[1], 'action': 'play_video', 'url':args[3], 'direct':'1'})
    else:
        Channel({'channel_id': args[1], 'action': 'show_categories'})
