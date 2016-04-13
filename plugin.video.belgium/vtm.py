#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import re
import channel

class Channel(channel.Channel):
    def get_main_url(self):
        return 'http://vtm.be'
    
    def get_categories(self, datas, skip_empty_id = True):
        data = channel.get_url(self.main_url + '/video/programma')
        regex = r"""<li><a href="([^"]+)">([^<]+)</a></li>"""
        for url, name in re.findall(regex, data):
            channel.addDir(name, '', channel_id=self.channel_id, url=url, action='show_videos')

    def get_videos(self, datas):
        url = datas.get('url')
        print url
        if url == 'http://vtm.be/het-nieuws/video':
            print 'Nieuw'
            return self.get_video_news()
        data = channel.get_url(url)
        regex = r"""<a href="([^"]+)">([^<]+)</a></h3>\s+<time[^>]+>([^<]+).+?<a href="\1"><img src="([^"]+)"""
        for url, title, date, img in re.findall(regex, data, re.DOTALL):
            title = title + ' - ' + date
            vurl = channel.array2url(channel_id=self.channel_id, url=url, action='play_video')
            channel.addLink(title, vurl, img)

        next_page = re.search(r"""href="([^?]+\?page=(\d+))">volgende""", data)
        if next_page is not None:
            url = next_page.group(1)
            page = str(int(next_page.group(2)) + 1)
            channel.addDir('Page nr ' + page, self.icon, channel_id=self.channel_id, action='show_videos', url=url)

    def get_video_news(self):
        url = 'http://nieuws.vtm.be/herbekijk'
        data = channel.get_url(url)
        regex = r"""href="([^"]+)"><img src="([^"]+)[^<]+</a>\s+</div>\s+<div[^<]+</div>\s+<h3[^>]+>\s+<span>\s+<a href[^>]+>([^<]+)"""
        for url, img, title in re.findall(regex, data):
            vurl = channel.array2url(channel_id=self.channel_id, url=url, action='play_video', news='1')
            channel.addLink(title, vurl, img)

    def play_video(self, datas):
        url = datas.get('url')
        if datas.get('news'):
            return self.play_video_news(url)
        data = channel.get_url(url)
        regex = r"""<source src="([^"]+)"""
        video = re.search(regex, data)
        if video is not None:
            vurl = video.group(1)
            channel.playUrl(vurl)
    
    def play_video_news(self, url):
        url = 'http://nieuws.vtm.be' + url
        data = channel.get_url(url)
        regex = r"""<source src="([^"]+)"""
        vurl = re.findall(regex, data)[0]
        channel.playUrl(vurl)

if __name__ == "__main__":
    import sys
    args = sys.argv
    if len(args) == 2:
        Channel({'channel_id': 'vtm', 'action': 'show_videos', 'url':args[1]})
    else:
        Channel({'channel_id': 'vtm', 'action': 'show_categories'})
