# -*- coding: utf-8 -*-

import httplib2
import os
import base64
import requests
import json

from apiclient import discovery, errors
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


#URL情報
DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')

#APIの情報を返す関数
def get_translation_service(key):
    http = httplib2.Http()
    return discovery.build(
        'translation', 'v2', http=http, discoveryServiceUrl=DISCOVERY_URL, developerKey=key)


class GtranslationClient(object):

    def __init__(self):
        script_dir =os.path.abspath(os.path.dirname(__file__))
        self.credential_dir = os.path.join(script_dir, ".credentials")

        if not os.path.exists(self.credential_dir):
            os.makedirs(self.credential_dir)

        #APIキーを設定
        rf = open(os.path.join(self.credential_dir, "api_key"), 'r')
        self.KEY = rf.read().strip()
        rf.close()

    #日本語テキストを英語テキストに変換
    def get_text_jp_to_en(self, speech_text):
        #翻訳
        translation = get_translation_service(self.KEY)
        print(speech_text)

        #URLの取得
        service_request = translation.translations().translate(body={})
        print(service_request.uri)

        payload={
                'q': speech_text,
                'source': 'ja',
                'target': 'en',
                'format': 'text'
            }
        translation_response = requests.post(service_request.uri, params=payload)

        res_json = json.loads(translation_response.text)
        res_text = res_json['data']['translations'][0]['translatedText']
        print(res_text)

        return res_text



