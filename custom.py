# -*- coding: utf-8 -*-
# Video Playback Cache By DieFeM
# Based on the following guide
# https://kodi.wiki/view/HOW-TO:Modify_the_video_cache

from channelselector import get_thumb
from core.item import Item
from platformcode import config, logger
import xml.etree.ElementTree as ET
from core import filetools
from platformcode import logger, config, platformtools
import sys

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

    return itemlist


def video_cache_config(item):
    xml_path = get_xml_path()

    if filetools.exists(xml_path):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except:
            root = ET.Element("advancedsettings")
    else:
        root = ET.Element("advancedsettings")

    cache = root.find(CACHETAG)
    if cache is None:
        cache = ET.SubElement(root, CACHETAG)

    buffermode = cache.find(MODETAG)
    if buffermode is None:
        buffermode = ET.SubElement(cache, MODETAG)
        buffermode.text = '0'

    memorysize = cache.find(MEMORYTAG)
    if memorysize is None:
        memorysize = ET.SubElement(cache, MEMORYTAG)
        memorysize.text = '20971520'

    readfactor = cache.find(FACTORTAG)
    if readfactor is None:
        readfactor = ET.SubElement(cache, FACTORTAG)
        readfactor.text = '4'

    settings = get_cache_settings()

    buffermode_selected = get_dict_index(settings[MODETAG], buffermode.text)
    memorysize_selected = get_dict_index(settings[MEMORYTAG], memorysize.text)
    readfactor_selected = get_dict_index(settings[FACTORTAG], readfactor.text)

    list_controls = [
        {
            "id": MODETAG,
            "type": "list",
            "label": MODETAG,
            "default": buffermode_selected,
            "enabled": True,
            "visible": True,
            "lvalues": list(settings[MODETAG].values())
        },
        {
            "id": MEMORYTAG,
            "type": "list",
            "label": MEMORYTAG,
            "default": memorysize_selected,
            "enabled": True,
            "visible": True,
            "lvalues": list(settings[MEMORYTAG].values())
        },
        {
            "id": FACTORTAG,
            "type": "list",
            "label": FACTORTAG,
            "default": readfactor_selected,
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
    
    if filetools.exists(xml_path):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            cleanTails(root)
        except:
            root = ET.Element("advancedsettings")
    else:
        root = ET.Element("advancedsettings")

    cache = root.find(CACHETAG)
    if cache is None:
        cache = ET.SubElement(root, CACHETAG)

    buffermode = cache.find(MODETAG)
    if buffermode is None:
        buffermode = ET.SubElement(cache, MODETAG)
    i = dict_data_saved[MODETAG]
    data = get_dict_by_index(settings[MODETAG], int(i))
    buffermode.text = data[0]

    memorysize = cache.find(MEMORYTAG)
    if memorysize is None:
        memorysize = ET.SubElement(cache, MEMORYTAG)
    i = dict_data_saved[MEMORYTAG]
    data = get_dict_by_index(settings[MEMORYTAG], int(i))
    memorysize.text = data[0]

    readfactor = cache.find(FACTORTAG)
    if readfactor is None:
        readfactor = ET.SubElement(cache, FACTORTAG)
    i = dict_data_saved[FACTORTAG]
    data = get_dict_by_index(settings[FACTORTAG], int(i))
    readfactor.text = data[0]

    encoding = 'unicode' if PY3 else 'utf-8'
    xmlstr = ET.tostring(root, encoding=encoding)
    xmlstr = prettyprint(xmlstr)
    # logger.info(xmlstr, True)
    with open(xml_path, "w") as f:
        f.write(xmlstr)


def get_xml_path():
    userdata_path = filetools.translatePath('special://home/userdata')
    return filetools.join(userdata_path, 'advancedsettings.xml')


def get_cache_settings():
    return {MODETAG:   {'0': 'Buffer all internet filesystems (default)', 
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


def cleanTails(root):
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