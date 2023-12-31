# -*- coding: utf-8 -*-
# Video Playback Cache By DieFeM
# Based on the following guide
# https://kodi.wiki/view/HOW-TO:Modify_the_video_cache

from channelselector import get_thumb
from core.item import Item
import xml.etree.ElementTree as ET
from core import filetools, servertools
from platformcode import logger, config, platformtools
import sys
import xbmc
import xbmcgui
from re import sub

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

newtags = config.get_platform(True)['num_version'] >= 17
CACHETAG = 'cache' if newtags else 'network'
MEMORYTAG = 'memorysize' if newtags else 'cachemembuffersize'
FACTORTAG = 'readfactor' if newtags else 'readbufferfactor'
MODETAG = 'buffermode'


def mainlist(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(module="custom", title=config.get_localized_string(60404), action="video_cache_config",
                         config="downloads", folder=False, thumbnail=get_thumb("setting_0.png")))

    itemlist.append(Item(module="custom", title="Test Links", action="test_links",
                         config="downloads", folder=False, thumbnail=get_thumb("setting_0.png")))
    return itemlist


def test_links(item):
    dialog = xbmcgui.Dialog()
    d = dialog.input('Enter link', type=xbmcgui.INPUT_ALPHANUM)
    servername = servertools.get_server_from_url(d)
    dialog.textviewer('Server Name', servername)


def video_cache_config(item):
    settings = get_cache_settings()
    cache = get_cache_elem(get_root_elem(get_xml_path()))

    list_controls = [
        {
            "id": MODETAG,
            "type": "list",
            "label": MODETAG,
            "default": get_selected(MODETAG,   settings, cache, '0'),
            "enabled": True,
            "visible": True,
            "lvalues": list(settings[MODETAG].values())
        },
        {
            "id": MEMORYTAG,
            "type": "list",
            "label": MEMORYTAG,
            "default": get_selected(MEMORYTAG, settings, cache, '20971520'),
            "enabled": True,
            "visible": True,
            "lvalues": list(settings[MEMORYTAG].values())
        },
        {
            "id": FACTORTAG,
            "type": "list",
            "label": FACTORTAG,
            "default": get_selected(FACTORTAG, settings, cache, '4'),
            "enabled": True,
            "visible": True,
            "lvalues": list(settings[FACTORTAG].values())
        }
    ]

    platformtools.show_channel_settings(list_controls=list_controls, callback='save_setting_cache', item=item,
                                        caption=config.get_localized_string(60404), custom_button={'visible': False})


def save_setting_cache(item, dict_data_saved):
    # logger.info(dict_data_saved, True)
    settings = get_cache_settings()
    xml_path = get_xml_path()
    root = get_root_elem(xml_path)
    cache = get_cache_elem(root)

    set_data(MODETAG,   settings, cache, dict_data_saved)
    set_data(MEMORYTAG, settings, cache, dict_data_saved)
    set_data(FACTORTAG, settings, cache, dict_data_saved)

    encoding = 'unicode' if PY3 else 'utf-8'
    xmlstr = ET.tostring(root, encoding=encoding)
    xmlstr = prettyprint(xmlstr)
    # logger.info(xmlstr, True)
    with open(xml_path, "w") as f:
        f.write(xmlstr)


def get_xml_path():
    return filetools.translatePath('special://profile/advancedsettings.xml')


def get_root_elem(xml_path):
    if filetools.exists(xml_path):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            clean_tails(root)
        except:
            root = ET.Element("advancedsettings")
    else:
        root = ET.Element("advancedsettings")

    root.set('version', '1.0')
    return root


def get_cache_elem(root):
    cache = root.find(CACHETAG)
    if cache is None:
        cache = ET.SubElement(root, CACHETAG)
    return cache


def set_data(tag, settings, cache, data):
    item = cache.find(tag)
    if item is None:
        item = ET.SubElement(cache, tag)
    item.text = get_dict_by_index(settings[tag], int(data[tag]))[0]


def get_selected(tag, settings, cache, default):
    item = cache.find(tag)
    if item is None:
        item = ET.SubElement(cache, tag)
        item.text = default
    return get_dict_index(settings[tag], item.text)


def get_cache_settings():
    settings = { MODETAG:  {'0': 'Buffer all internet filesystems (default)', 
                            '1': 'Buffer all filesystems, both internet and local (recommended)', 
                            '2': 'Only buffer true internet filesystems (streams)', 
                            '3': 'No buffer', 
                            '4': 'All network filesystems (incl. smb, nfs, etc.)'},
                MEMORYTAG: {'20971520':   '20MB buffer, requires 60MB of free RAM (default)',
                            '52428800':   '50MB buffer, requires 150MB of free RAM', 
                            '104857600':  '100MB buffer, requires 300MB of free RAM', 
                            '139460608':  '133MB buffer, requires 400MB of free RAM (recommended)',
                            '278921216':  '266MB buffer, requires 800MB of free RAM',
                            '349175808':  '333MB buffer, requires 1GB of free RAM',
                            '1073741824': '1GB buffer, requires 3GB of free RAM',
                            '2863311530': '2.6GB buffer, requires 8GB of free RAM',
                            '0':          'Use local drive, requires 16GB+ of free space.'},
                FACTORTAG: {'4':  '4X fill-rate (default)', 
                            '10': '10X fill-rate', 
                            '20': '20X fill-rate (recommended)', 
                            '30': '30X fill-rate', 
                            '40': '40X fill-rate'}
               }

    # free drive in GB
    free_drv = int(sub('\s*[^\d]+$', '', xbmc.getInfoLabel('System.FreeSpace'))) // 1024
    # free mem in Bytes
    free_mem = int(sub('\s*[^\d]+$', '', xbmc.getInfoLabel('System.FreeMemory'))) * 1048576 

    if free_drv < 16:
        del settings[MEMORYTAG]['0']

    for size in list(settings[MEMORYTAG]):
        if (int(size) * 3) > free_mem:
            del settings[MEMORYTAG][size]

    # logger.info('free_drv: ' + str(free_drv) +', free_mem: ' + str(free_mem), True)
    return settings


def clean_tails(root):
    for elem in root.iter():
        if elem.tail: elem.tail = elem.tail.strip()
        if len(elem):
            if elem.text: elem.text = elem.text.strip()


def prettyprint(xmlstr):
    from xml.dom import minidom
    pretty = minidom.parseString(xmlstr).toprettyxml(indent="\t")
    # Borrar cabecera
    return "\n".join(pretty.splitlines()[1:])


def get_dict_index(d, k):
    try:
        if PY3:
            i = list(d.keys()).index(k)
        else:
            i = d.keys().index(k)
    except:
        i = 0
    return i


def get_dict_by_index(d, i):
    try:
        if PY3:
            l = list(d.items())[i]
        else:
            l = d.items()[i]
    except:
        l = {}
    return l