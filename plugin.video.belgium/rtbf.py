#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import re
import channel
import HTMLParser

id2skip = [str(x) for x in [5683,2913,5614,5688,156]]

class Channel(channel.Channel):
    def get_main_url(self):
        return 'https://www.rtbf.be'
    
    def get_categories(self, skip_empty_id = True):
        channel.addDir('Directs', 'DefaultVideo.png', channel_id=self.channel_id, action='get_lives')
        data = channel.get_url(self.main_url + '/auvio/emissions')
        regex = r""",([^\,]+-original.(?:jpg|gif|png|jpeg))[^/]*/>\s*\n\s*</div>\s*\n\s*</figure>\s*\n\s*<header[^>]+>\s*\n\s*<span[^<]+</span>\s*\n\s*<a href="([^"]+)"\s*>\s*\n\s*<h4[^>]+>([^<]+)"""
        for icon, url, name in re.findall(regex, data):
            id = url.split('?id=')[1]
            if skip_empty_id and id in id2skip:
                continue
            channel.addDir(name, icon, channel_id=self.channel_id, url=url, action='show_videos', id=id)

    def get_lives(self, datas):
        def parse_lives(data):
            regex = r""",([^,]+?\.(?:jpg|gif|png))\s648w"[^/]*/>(?s).*?"rtbf-media-item__title">\s*<a href="([^"]+)"\s*title="([^"]+)"""
            for icon, url, name in re.findall(regex, data, flags=re.DOTALL):
                print "found"
                vurl = channel.array2url(channel_id=self.channel_id, url=url, action='play_live')
                channel.addLink(name.replace('&#039;', "'").replace('&#034;', '"') , vurl, icon) # + ' - ' + date
        live_url = self.main_url + '/auvio/direct/'
        data = channel.get_url(live_url)
        parse_lives(data)

    
    def get_videos(self, datas):
        url = datas.get('url')
        data = channel.get_url(url)
        regex = r""">([^<]+)</time>\s*\n\s*<h3[^<]*<a href="([^"]+)"[^>]*>([^<]+)</a></h3>"""
        for date, url, title in re.findall(regex, data):
            title = title + ' - ' + date
            vurl = channel.array2url(channel_id=self.channel_id, url=url, action='play_video')
            channel.addLink(title.replace('&#039;', "'").replace('&#034;', '"'), vurl, None)
    
   
                
    def play_video(self, datas):
        url = datas.get('url')
        data = channel.get_url(url)
        regex = r"""src="(https://www.rtbf.be/auvio/embed/media[^"]+)"""
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
        data = channel.get_url(url)
        regex = r"""src="(https://www.rtbf.be/auvio/embed/direct[^"]+)"""
        iframe_url = re.findall(regex, data)[0]
        rtmp = self.get_live_rtmp(iframe_url)
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
