# -*- coding: iso-8859-1 -*- 
import urllib, os, sys

import channel

#if channel.in_xbmc:
    
    #icon = xbmc.translatePath(os.path.join(__home__, 'resources/rtl-tvi.png'))

channels = {'rtltvi': {'name': 'RTL-TVI', 'icon': 'rtl-tvi.png', 'module': 'rtl'},
            'clubrtl': {'name': 'Club RTL', 'icon': 'club-rtl.png', 'module': 'rtl'},
            'plugrtl': {'name': 'Plug RTL', 'icon': 'plug-rtl.png', 'module': 'rtl'},
            'rtbf': {'name': 'RTBF', 'icon': 'rtbf-all.png'},
            'tvcom': {'name': 'TV Com', 'icon': 'tvcom.jpg'},
            'vtm': {'name': 'VTM', 'icon': 'vtm.jpg'},
            'een': {'name': 'EEn', 'icon': 'een.png'},
            }

def show_channels():
    for channel_id, ch in channels.iteritems():
        if channel.in_xbmc:
            icon = xbmc.translatePath(os.path.join(channel.home, 'resources/' + ch['icon']))
            channel.addDir(ch['name'], icon, channel_id=channel_id, action='show_categories')
        else:
            print ch['name'], channel_id, 'show_categories'
    channel.addDir('Settings', None, action='settings')
     
def get_params():
    param = {}
    if len(sys.argv) < 3:
        return {}
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        print cleanedparams
        pairsofparams = cleanedparams.split('&')
        print pairsofparams
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                try:
                    param[splitparams[0]] = urllib.unquote_plus(splitparams[1])
                except:
                    pass
    return param
print "==============================="
print "  Video Belgium"
print "==============================="
print

params = get_params()

action = params.get('action', False)
channel_id = params.get('channel_id')
print 'channel_id:', channel_id

if action is False:
    show_channels()
    channel.xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif action == 'settings':
    import xbmcaddon
    addon = xbmcaddon.Addon()
    addon.openSettings()
elif channel_id:
    context = channels[channel_id]
    context.update(params)
    import sys
    channel_module_name = context.get('module', channel_id)
    __import__(channel_module_name)
    sys.modules[channel_module_name].Channel(context)
    channel.xbmcplugin.endOfDirectory(int(sys.argv[1]))
