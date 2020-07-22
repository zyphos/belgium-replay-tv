#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import re
import channel
import HTMLParser
import json

import xbmcaddon

id2skip = []

class Channel(channel.Channel):
    def get_main_url(self):
        return 'https://www.rtbf.be'
    
    def get_categories(self, skip_empty_id = True, return_result=False):
        channel.addDir('Directs', 'DefaultVideo.png', channel_id=self.channel_id, action='get_lives')
        data = channel.get_url(self.main_url + '/auvio/emissions')
        regex = r"""<h4\s+class="rtbf-media-item__title">\s*<a\s+href="([^"]+)[^>]+>\s*([^<]+)"""
        result = []
        icon = None
        for url, name in re.findall(regex, data):
            if name and name[0] == '#':
                continue
            id = url.split('?id=')[1]
            if skip_empty_id and id in id2skip:
                continue
            channel.addDir(name, icon, channel_id=self.channel_id, url=url, action='show_videos', id=id)
            if return_result:
                result.append({'name': name,
                               'icon': icon,
                               'channel_id': self.channel_id,
                               'url': url,
                               'action': 'show_videos',
                               'id': id})
        return result

    def get_lives(self, datas):
        def parse_lives(data):
            regex = r""",([^,]+?\.(?:jpg|gif|png|jpeg))\s648w"[^/]*/>(?s).*?"rtbf-media-item__title">\s*<a href="([^"]+)"\s*title="([^"]+)"""
            for icon, url, name in re.findall(regex, data, flags=re.DOTALL):
                print "found"
                vurl = channel.array2url(channel_id=self.channel_id, url=url, action='play_live')
                channel.addLink(name.replace('&#039;', "'").replace('&#034;', '"') , vurl, icon) # + ' - ' + date
        live_url = self.main_url + '/auvio/direct/'
        data = channel.get_url(live_url)
        parse_lives(data)

    
    def get_videos(self, datas, return_result=False):
        category_url = datas.get('url')
        category_name = datas.get('name')
        category_id = datas.get('id')
        data = channel.get_url(category_url)
        regex = r"""data-card="([^"]+)"""
        result = []
        h = HTMLParser.HTMLParser()
        for data_card in re.findall(regex, data):
            data_card_json = h.unescape(data_card)
            data_card_dict = json.loads(data_card_json)
            date = '/'.join(data_card_dict['date']['full'][:10].split('-')[::-1])
            title = data_card_dict['title']
            full_title = title + ' - ' + date
            img = data_card_dict['illustration'].get('format770',None)
            url = data_card_dict['url']
            vurl = channel.array2url(channel_id=self.channel_id, url=url, action='play_video', category_id=category_id, category_url=category_url, category_name=category_name)
            full_title = full_title.replace('&#039;', "'").replace('&#034;', '"')
            channel.addLink(full_title, vurl, img)
            if return_result:
                result.append({'name': full_title,
                               'channel_id': self.channel_id,
                               'url': url,
                               'action': 'play_video'})
        return result
                
    def play_video(self, datas):
        url = datas.get('url')
        print '====play video==='
        print url
        data = channel.get_url(url)
        #regex = r"""src="(https://www.rtbf.be/auvio/embed/internal/media[^"]+)"""
        #iframe_url = re.findall(regex, data)[0]
        #data = channel.get_url(iframe_url)
        #regex = r"""data-media="([^"]+)"""
        #media = re.findall(regex, data)[0]
        #
        #h = HTMLParser.HTMLParser()
        #media_json = h.unescape(media)
        #qualities = {'720p': 'high',
        #             '480p': 'web',
        #             '234p': 'mobile'}
        addon = xbmcaddon.Addon()
        setting_quality = addon.getSetting('rtbf_quality')
        if not setting_quality:
            setting_quality = '1080p'
        # <meta itemprop="contentUrl" content="http://rtbf-vod.l3.freecaster.net/vod/rtbf/geo/open/p/pE4pbU1ncE_720p.mp4">
        media_regex = r"""content="([^_"]+_\d+p.mp4)"""
        print media_regex
        video_url = re.findall(media_regex, data)[0]
        print video_url
        prefix, suffix = video_url.rsplit('_',1)
        found_quality = int(suffix.split('p',1)[0])
        if found_quality >= int(setting_quality[:-1]):
            video_url = '%s_%s.mp4' % (prefix, setting_quality)
        print video_url
        channel.playUrl(video_url)


    def play_live(self, datas):
        url = datas.get('url')
        data = channel.get_url(url)
        regex = r"""src="(https://www.rtbf.be/auvio/embed/direct[^"]+)"""
        iframe_url = re.findall(regex, data)[0]
        rtmp = self.get_live_rtmp(iframe_url)
        channel.playUrl(rtmp)



    def get_live_rtmp(self, page_url):
        print "live stream!"
        data = channel.get_url(page_url)
        regex = r"""streamName&quot;:&quot;([^&]+)"""
        stream_name = re.search(regex, data)
        if stream_name is None:
            return None
        stream_name = stream_name.group(1)
        print "stream name: >" + stream_name + "<"
        if stream_name == 'freecaster':
            print "freecaster stream"
            regex = r"""streamUrl&quot;:&quot;([^&]+)"""
            freecaster_stream =  re.search(regex, data)
            freecaster_stream = freecaster_stream.group(1)
            freecaster_stream=freecaster_stream.replace("\\", "") 
            channel.playUrl(freecaster_stream)
        else:
            print "not a freecaster stream"
            regex = r"""streamUrlHls&quot;:&quot;([^&]+)"""
            hls_stream_url = re.search(regex,data)
            if hls_stream_url is not None:
                print "HLS stream"
                stream_url = hls_stream_url.group(1).replace("\\", "")
                data = channel.get_url(stream_url)
                best_resolution_path = data.split("\n")[-2]
                hls_stream_url = stream_url[:stream_url.rfind('open')] + best_resolution_path[5:]
                print "HLS stream url: >" + hls_stream_url + "<"
                channel.playUrl(hls_stream_url)
            else:
                regex = r"""streamUrl&quot;:&quot;([^&]+)"""
                stream_url = re.search(regex,data)
                if stream_url is not None:
                    stream_url = stream_url.group(1)
                    stream_url = stream_url.replace("\\", "")
                    print "strange stream" 
                    print "stream url: >" + stream_url + "<"
                    channel.playUrl(stream_url)
                else:
                    print "normal stream"
                    token_json_data = channel.get_url(self.main_url + '/api/media/streaming?streamname=' + stream_name, referer=page_url)
                    token = token_json_data.split('":"')[1].split('"')[0]
                    swf_url = 'http://static.infomaniak.ch/livetv/playerMain-v4.2.41.swf?sVersion=4%2E2%2E41&sDescription=&bLd=0&sTitle=&autostart=1'
                    rtmp = 'rtmp://rtmp.rtbf.be/livecast'
                    page_url = 'http://www.rtbf.be'
                    play = '%s?%s' % (stream_name, token)
                    rtmp += '/%s swfUrl=%s pageUrl=%s tcUrl=%s' % (play, swf_url, page_url, rtmp)
                    return rtmp
    
    def generate_id2skip(self):
        id2skip = []
        print 'Generating ID 2 skip...'
        print 'Retrieving categories...'
        categories = self.get_categories(skip_empty_id=False, return_result=True)
        nb_cat = len(categories) - 1 
        i = 0
        if nb_cat == 0:
            raise Exception('Error: no categories found !')
        for category in categories[1:]: # Skip direct
            i += 1
            print 'Retrieving videos %s/%s: %s' % (i, nb_cat, category['name'])
            videos = self.get_videos(category, return_result=True)
            if not videos:
                id2skip.append(category['id'])
            if i == 10 and len(id2skip) == i:
                raise Exception('Error: no videos found !')

        if len(id2skip) == nb_cat:
            raise Exception('Error: no videos found !')
        return id2skip

if __name__ == "__main__":
    import sys
    ch = Channel({'action': 'test', 'channel_id':'rtbf'})
    id2skip = ch.generate_id2skip()
    print 'id2skip =', id2skip
