#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import re
import channel
 
class Channel(channel.Channel):
    def get_main_url(self):
        return 'https://bx1.be'
    
    def get_categories(self):
        data = channel.get_url('%s/emissions/' % self.main_url)
        regex = r"""<a\s+href="([^"]+)"[^>]+>\s+<h3>([^<]+)</h3>\s+<figure>\s+<img\s+class[^ ]+\s+src="([^"]+)"""
        for url, name, icon in re.findall(regex, data):
            channel.addDir(name, icon, channel_id=self.channel_id, url=url, action='show_videos')

    def get_videos(self, datas):
        # TODO: handle multi page
        url = datas.get('url')
        data = channel.get_url(url)
        
        regex = r"""<a\s+href="([^"]+)"\s+title[^>]+>\s+<h3>([^<]+)<span[^>]+>([^<]+)</span></h3>\s+<figure>\s+<img[^s]+src="([^"]+)"""
        for vurl, title, date, img in re.findall(regex, data):
            title = "%s - %s" % (title.strip(), date.strip())
            vurl = channel.array2url(channel_id=self.channel_id, url=vurl, action='play_video')
            channel.addLink(title, vurl, img)
    
    def play_video(self, datas):
        url = datas.get('url')
        data = channel.get_url(url)
        regex = r""""(rtmps://[^"]+)"\s*\+\s*"([^"]+)"\s*\+\s*"([^"]+)"""
        video_url = ''.join(re.findall(regex, data)[0])
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
