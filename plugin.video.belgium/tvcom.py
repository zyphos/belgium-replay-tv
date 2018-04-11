#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import re
import channel
 
class Channel(channel.Channel):
    def get_main_url(self):
        return 'http://www.tvcom.be'
    
    def get_categories(self):
        data = channel.get_url('%s/emissions' % self.main_url)
        regex = r"""<a\s+href="\.([^"]+)">\s+<img src="([^"]+)[^<]+<[^<]+<[^<]+<[^<]+<[^<]+<[^<]+<h3>([^<]+)"""
        for url, img, name in re.findall(regex, data):
            icon = self.main_url + '/' + img
            channel.addDir(name, icon, channel_id=self.channel_id, url=url, action='show_videos')

    def get_videos(self, datas):
        # TODO: handle multi page
        url = datas.get('url')
        data = channel.get_url(self.main_url + url)
        
        regex = r"""<a\s+href="([^"]+)"\s*>\s+<img[^s]+src="([^"]+)"\s+alt="([^"]+)"""
        for vurl, img, title in re.findall(regex, data):
            title = title.strip()
            if title[:5] == 'TVCOM':
                continue
            if title[:4] == 'test':
                title = title[4:]
            vurl = channel.array2url(channel_id=self.channel_id, url=vurl, action='play_video')
            channel.addLink(title, vurl, img)
    
    def play_video(self, datas):
        url = datas.get('url')
        video_page_url = url
        data = channel.get_url(video_page_url)
        regex = r"""https://static\.tvcom\.be/videos/[^.]+\.mp4"""
        video_url = re.findall(regex, data)[0]
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
