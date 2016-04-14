#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import re
import channel
import HTMLParser

id2skip = [str(x) for x in [5683,2913,5614,5688,156]]

class Channel(channel.Channel):
    def get_main_url(self):
        return 'http://www.rtbf.be'
    
    def get_categories(self, skip_empty_id = True):
        #channel.addDir('Directs', 'DefaultVideo.png', channel_id=self.channel_id, action='get_lives')
        data = channel.get_url(self.main_url + '/auvio/emissions')
        regex = r""",([^-]+-original.png)[^/]*/>\s*\n\s*</div>\s*\n\s*</figure>\s*\n\s*<header[^>]+>\s*\n\s*<span[^<]+</span>\s*\n\s*<a href="([^"]+)"\s*>\s*\n\s*<h4[^>]+>([^<]+)"""
        for icon, url, name in re.findall(regex, data):
            id = url.split('?id=')[1]
            if skip_empty_id and id in id2skip:
                continue
            channel.addDir(name, icon, channel_id=self.channel_id, url=url, action='show_videos', id=id)

    def get_lives(self, datas):
        def parse_lives(data):
            regex = r"""href="http://www.rtbf.be/livecenter/([^"]+)"><img class="[^"]+" src="([^"]+)" alt="([^"]+).""" #*\3.*\3.*class="date">([^<]+).*is-live.*\1
            for url, icon, name in re.findall(regex, data, flags=re.DOTALL):
                print "found"
                vurl = channel.array2url(channel_id=self.channel_id, url=url, action='play_live')
                channel.addLink(name.replace('&#039;', "'").replace('&#034;', '"') , vurl, icon) # + ' - ' + date
        live_url = self.main_url + '/livecenter/'
        data = channel.get_url(live_url)
        parse_lives(data)
        data = channel.get_url(live_url + '?category=&page=2&client=')
        parse_lives(data)
    
    def get_videos(self, datas):
        url = datas.get('url')
        data = channel.get_url(url)
        regex = r""">([^<]+)</time>\s*\n\s*<h3[^<]*<a href="([^"]+)"[^>]*>([^<]+)</a></h3>"""
        for date, url, title in re.findall(regex, data):
            title = title + ' - ' + date
            vurl = channel.array2url(channel_id=self.channel_id, url=url, action='play_video')
            channel.addLink(title.replace('&#039;', "'").replace('&#034;', '"'), vurl, None)
    
    def get_videos_old(self, datas):
        #from datetime import datetime
        url = datas.get('url')
        vid_id = datas.get('vid_id')
        md5 = datas.get('md5')
        if not vid_id:
            vid_id, md5 = self.get_video_id(url)
        if not vid_id:
            return
        page = datas.get('page', 1)
        #http://www.rtbf.be/video/detail/ajax/av?page=1&timeFilter=all&orderBy=publish_view&videoId=1856226&returnMode=program&categoryId=&md5=00f9cfd447930fa1742d5d9f3e29e45cf083609f
        data = channel.get_url(self.main_url + "/video/detail/ajax/av?page=" + str(page) + "&timeFilter=all&orderBy=publish_view&videoId=" + str(vid_id) + "&returnMode=program&categoryId=&md5=" + str(md5))
        #data = channel.get_url(self.main_url + "/video/detail/ajax/av?page=" + str(page) + "&timeFilter=all&orderBy=more_recent&videoId=" + str(vid_id) + "&returnMode=program&categoryId=&md5=" + str(md5))
        #regex = r"""video/detail_[^?]+\?id=(\d+)".+ src="([^"]+).+\n.+rel="">([^<]+).+\n.+\n.+\n.+<strong>([^<]+)"""
        regex = r"""video/detail_[^?]+\?id=(\d+)".+ src="([^"]+).+\n.+>([^<]+)(.+\n){3,4}.+<strong>(\d\d/\d\d/\d{4})"""
        #regex = r"""(?s)\?id=(\d+)&c[^>]+><img class="thumb" src="([^"]+).+?<h3><[^>]+>([^<]+)</a></h3>\s+<span[^>]+><a[^>]+>([^<]+)"""
        for id, img, title, tt, date in re.findall(regex, data):
            title = title + ' - ' + date
            vurl = channel.array2url(channel_id=self.channel_id, url=id, action='play_video')
            channel.addLink(title.replace('&#039;', "'").replace('&#034;', '"'), vurl, img)

        next_page = re.search(r"""rel="(\d+)">Suivante""", data)
        if next_page is not None:
            page = next_page.group(1)
            channel.addDir('Page nr ' + page, self.icon, channel_id=self.channel_id, vid_id=vid_id, action='show_videos', page=page, md5=md5)
            
    def get_video_id_old(self, url):
        rawstr = r"""id="hidVideoId" value="(\d+)"""
        data = channel.get_url(self.main_url + '/auvio/emissions/detail_' + url)
        id = re.search(rawstr, data)
        if id is not None:
            video_id = id.group(1)
            rawstr = r"""hidMD5"\s*value="([a-f0-9]+)"""
            res = re.search(rawstr, data)
            if res:
                md5 = res.group(1)
                return video_id, md5
        return False, False
                
    def play_video(self, datas):
        url = datas.get('url')
        data = channel.get_url(url)
        regex = r"""src="(http://www.rtbf.be/auvio/embed/media[^"]+)"""
        iframe_url = re.findall(regex, data)[0]
        data = channel.get_url(iframe_url)
        regex = r"""data-media="([^"]+)"""
        media = re.findall(regex, data)[0]
        
        h = HTMLParser.HTMLParser()
        media_json = h.unescape(media)
        regex = r""""high":"([^"]+)"""
        video_url = re.findall(regex, media_json)[0]
        channel.playUrl(video_url)
    
    def play_live(self, datas):
        url = datas.get('url')
        rtmp = self.get_live_rtmp(self.main_url + "/livecenter/" + url)
        channel.playUrl(rtmp)
    
    def get_live_rtmp(self, page_url):
        data = channel.get_url(page_url)
        regex = r"""streamName&quot;:&quot;([^&]+)"""
        stream_name = re.search(regex, data)
        if stream_name is None:
            return None
        stream_name = stream_name.group(1)
        token_json_data = channel.get_url(self.main_url + '/api/media/streaming?streamname=' + stream_name, referer=page_url)
        token = token_json_data.split('":"')[1].split('"')[0]
        swf_url = 'http://static.infomaniak.ch/livetv/playerMain-v4.2.41.swf?sVersion=4%2E2%2E41&sDescription=&bLd=0&sTitle=&autostart=1'
        rtmp = 'rtmp://rtmp.rtbf.be/livecast'
        page_url = 'http://www.rtbf.be'
        play = '%s?%s' % (stream_name, token)
        rtmp += '/%s swfUrl=%s pageUrl=%s tcUrl=%s' % (play, swf_url, page_url, rtmp)
        #xbmc.log('stream: ' + rtmp)
        return rtmp
        """Correct this
stream=1
sname=stream7?
server=rtmp://rtmp.rtbf.be
dir=livecast

stream=1
sname=laune?4164b27a0411cdfd4e031a55698d51
server=rtmp://rtmp.rtbf.be
dir=livecast

play('stream7?')
        
        
        """    

if __name__ == "__main__":
    import sys
    args = sys.argv
    if len(args) == 2:
        action = args[1]
        if action == 'scan_empty':
            Channel({'channel_id': 'rtbf', 'action': 'scan_empty'})
        elif action == 'get_lives':
            Channel({'channel_id': 'rtbf', 'action': 'get_lives'})
        else:
            Channel({'channel_id': 'rtbf', 'action': 'show_videos', 'url':args[1]})
    else:
        Channel({'channel_id': 'rtbf', 'action': 'show_categories'})
