#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import re
import channel
 
class Channel(channel.Channel):
    def get_main_url(self):
        return 'http://www.tvcom.be'
    
    def get_categories(self):
        data = channel.get_url(self.main_url)
        regex = r"""missions(.+?)</ul"""
        res = re.findall(regex, data)
        if not res:
            return
        cat_data = res[0]
        regex = r"""<a href="([^"]+)"><span>([^<]+)"""
        for url, name in re.findall(regex, cat_data):
            channel.addDir(name, self.icon, channel_id=self.channel_id, url=url, action='show_videos')

    def get_videos(self, datas):
        url = datas.get('url')
        data = channel.get_url(self.main_url + url)
        regex = r"""class="contentheading"[^>]+>([^<]+)</td>\s+</tr>\s+</table>\s+<table[^>]+>\s+<tr>\s+<td[^>]+>\s+<p><a href="([^"]+)[^>]+><img.+? src="([^"]+)"""
        for title, vurl, img in re.findall(regex, data):
            title = title.strip()
            vurl = channel.array2url(channel_id=self.channel_id, url=vurl, action='play_video')
            channel.addLink(title, vurl, self.main_url + img)
    
    def play_video(self, datas):
        url = datas.get('url')
        video_page_url = self.main_url + url
        data = channel.get_url(video_page_url)
        regex = r"""(http://www.tvcom.be/videos/.+?\.mp4)"""
        video_url = re.findall(regex, data)[0]
        video_url = video_url.replace(' ', '%20')
        channel.playUrl(video_url)

if __name__ == "__main__":
    import sys
    args = sys.argv
    if len(args) == 3:
        Channel({'channel_id': 'tvcom', 'action': 'play_video', 'url':args[1]})
    elif len(args) == 2:
        Channel({'channel_id': 'tvcom', 'action': 'show_videos', 'url':args[1]})
    else:
        Channel({'channel_id': 'tvcom', 'action': 'show_categories'})
