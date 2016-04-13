#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import re

import channel

class Channel(channel.Channel):
    def get_main_url(self):
        return 'http://www.een.be'

    def get_categories(self):
        data = channel.get_url(self.main_url + '/mediatheek')
        regex = r"""value="(\d+)">([^<]+)"""
        for url, name in re.findall(regex, data):
            channel.addDir(name, self.icon, channel_id=self.channel_id, url=url, action='show_videos')
                
    def get_videos(self, datas):
        url = datas.get('url')
        page = datas.get('page', False)
        if page:
            page_txt = '&page=' + str(page)
        else:
            page_txt = ''
        data = channel.get_url(self.main_url + '/mediatheek/tag/' + url + page_txt)
        regex = r""" id="video-(\d+)"><img src="([^"]+)" /></a>\s*<h5><a[^>]+>([^<]+)"""
        for id, img, title in re.findall(regex, data):
            vurl = channel.array2url(channel_id=self.channel_id, url=id, action='play_video')
            channel.addLink(title, vurl, img)
        next_page = re.search(r"""\?page=(\d+)" class="pager-next active" title="Ga naar volg""", data)
        if next_page is not None:
            page = next_page.group(1)
            channel.addDir('Page nr ' + page, self.icon, channel_id=self.channel_id, url=url, action='show_videos', page=page)
            
    def play_video(self, datas):
        id = datas.get('url')
        regex = """provider: 'video', file: '([^']+)"""
        data = channel.get_url(self.main_url + '/mediatheek/ajax/video/' + id)
        for url in re.findall(regex, data):
            if url.split('.')[-1] == '3gp':
                return channel.playUrl(url)

if __name__ == "__main__":
    import sys
    args = sys.argv
    if len(args) == 3:
        Channel({'channel_id': 'een', 'action': 'play_video', 'url':args[1]})
    elif len(args) == 2:
        Channel({'channel_id': 'een', 'action': 'show_videos', 'url':args[1]})
    else:
        Channel({'channel_id': 'een', 'action': 'show_categories'})
