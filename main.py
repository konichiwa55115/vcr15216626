#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from multiprocessing import Process
import os
import pathlib
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
import yaml
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', type=str, help='Path to config file', default='config.yaml')
    parser.add_argument('-d', '--dir', type=str, help='Path to working directory', default='.')
    return parser.parse_args()


def get_config(config_path):
    with open(config_path, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            interval = config.get('interval')
            if interval is None or type(interval) != int:
                return None, '`interval` must be a positive integer'
            channels = config.get('channels', [])
            if type(channels) != list:
                return None, '`channels` must be a list'
            for c in channels:
                if type(c.get('id')) != str:
                    return None, '`channels[].id must be a string'
                save_to = c.get('save_to')
                if type(save_to) == str:
                    try:
                        pathlib.Path(save_to).mkdir(parents=True, exist_ok=True)
                    except:
                        return None, '`channels[].save_to must be a writable directory path'
                else:
                    return None, '`channels[].save_to must be a writable directory path'
            return config, None
        except:
            return None, 'Cannot load config.yaml'


def record_live_stream(video_url, save_to, title):
    print(f'[INFO] start recording {title}: {video_url}')
    os.chdir(os.path.join(os.getcwd(), save_to))
    with YoutubeDL(params={'quiet': True}) as ytb_dl:
        ytb_dl.download([video_url])
    print(f'[INFO] finished recording {title}: {video_url}')


class YouVCRSilentLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


def main():
    args = parse_arg()
    config, err = get_config(args.conf)
    if err is not None:
        print(f'[ERROR] {err}')
        sys.exit(1)
    os.chdir(args.dir)

    videos_seen = {}
    if os.path.exists('videos_seen.yaml'):
        with open('videos_seen.yaml', 'r') as videos_seen_file:
            videos_seen = yaml.safe_load(videos_seen_file)
            if type(videos_seen) != dict:
                videos_seen = {}

    silent_logger = YouVCRSilentLogger()
    while True:
        print('[INFO] Checking for videos to download')
        for c in config['channels']:
            channel_id = c['id']
            req = urllib.request.Request(
                f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}',
                headers={'User-Agent': 'FeedFetcher-Google; (+http://www.google.com/feedfetcher.html)'}
            )
            xml_string = urllib.request.urlopen(req).read().decode('utf-8')
            root = ET.fromstring(xml_string)
            videos = []
            for child in list(root):
                if child.tag.endswith('}entry'):
                    video = {}
                    for child_child in list(child):
                        if child_child.tag.endswith('}videoId'):
                            video['id'] = child_child.text
                        if child_child.tag.endswith('}title'):
                            video['title'] = child_child.text
                    videos.append(video)

            with YoutubeDL(params={'quiet': True, 'logger': silent_logger}) as ytb_dl:
                for video in videos:
                    video_id = video["id"]
                    if videos_seen.get(video_id) is None:
                        url = f'https://www.youtube.com/watch?v={video_id}'
                        try:
                            res = ytb_dl.extract_info(url, download=False, force_generic_extractor=False)
                            if res['is_live']:
                                p = Process(target=record_live_stream, args=(url, c['save_to'], video['title']))
                                p.start()
                            videos_seen[video_id] = True
                        except DownloadError as err:
                            scheduled = "This live event will begin in"
                            if scheduled in err.args[0]:
                                start = err.args[0].index(scheduled)
                                print(f"[INFO] Found scheduled live: {url}.", err.args[0][start:])
                            else:
                                print(err.args[0])
                        except Exception as err:
                            print(f"[ERROR]: {err}")
        with open('videos_seen.yaml', 'w') as videos_seen_file:
            yaml.dump(videos_seen, videos_seen_file)
        time.sleep(config['interval'])
        new_config, err = get_config(args.conf)
        if err is not None:
            print(err)
        else:
            config = new_config


if __name__ == "__main__":
    main()
