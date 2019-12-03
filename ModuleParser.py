#!/usr/bin/env python3

import requests
import re
import json


class IG_stories_and_post_Parser:

    def __init__(self, url, headers):
        self.__url = url
        self.__headers = headers
        self.__page = requests.get(self.__url, params=self.__headers)
        self.IGTVs = {}
        self.posts = {}

    @property
    def url(self):
        return self.__url

    @property
    def headers(self):
        return self.__headers

    @headers.setter
    def headers(self, headers):
        self.__headers = headers

    def __parse_posts(self):
        page_script_pattern = re.compile(r'window._sharedData = ([\S\s]*?);</script>')
        json_script = json.loads(re.findall(page_script_pattern, self.__page.text)[0])
        for edge in json_script['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media'][
            'edges']:
            self.posts[edge['node']['taken_at_timestamp']] = self.__url + 'p/{0}'.format(edge['node']['shortcode'])
        return self.posts.keys()

    def __parse_IGTV(self):
        page_script_pattern = re.compile(r'window._sharedData = ([\S\s]*?);</script>')
        json_script = json.loads(re.findall(page_script_pattern, self.__page.text)[0])
        for edge in json_script['entry_data']['ProfilePage'][0]['graphql']['user']['edge_felix_video_timeline'][
            'edges']:
            self.IGTVs[edge['node']['taken_at_timestamp']] = self.__url + 'tv/{0}'.format(edge['node']['shortcode'])
        return self.IGTVs.keys()

    def get_last_post(self):
        self.__parse_posts()
        return self.posts[max(self.posts.keys())] if self.posts else None

    def get_last_video(self):
        self.__parse_IGTV()
        return self.IGTVs[max(self.IGTVs)] if self.IGTVs else None
