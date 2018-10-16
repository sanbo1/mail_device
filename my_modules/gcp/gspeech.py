# -*- coding: utf-8 -*-

import httplib2
import os
import base64
import email

from apiclient import discovery, errors
import oauth2client
from oauth2client import client
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
def get_speech_service(key):
    http = httplib2.Http()
    return discovery.build(
        'speech', 'v1', http=http, discoveryServiceUrl=DISCOVERY_URL, developerKey=key)

def get_texttospeech_service(key):
    http = httplib2.Http()
    return discovery.build(
        'texttospeech', 'v1', http=http, discoveryServiceUrl=DISCOVERY_URL, developerKey=key)


class GspeechClient(object):

    def __init__(self):
        script_dir =os.path.abspath(os.path.dirname(__file__))
        self.credential_dir = os.path.join(script_dir, ".credentials")

        if not os.path.exists(self.credential_dir):
            os.makedirs(self.credential_dir)

        #APIキーを設定
        rf = open(os.path.join(self.credential_dir, "api_key"), 'r')
        self.KEY = rf.read().strip()
        rf.close()

    #音声をテキストに変換
    def get_speech_to_text(self, speech_file):
        #音声ファイルを開く
        with open(speech_file, 'rb') as speech:
            speech_content = base64.b64encode(speech.read())

        #APIの情報を取得して、音声認識を行う
        service = get_speech_service(self.KEY)
        service_request = service.speech().recognize(
            body={
                'config': {
                    'encoding': 'LINEAR16',
                    'sampleRateHertz': 16000,
                    'languageCode': 'ja-JP', #日本語に設定
                    'enableWordTimeOffsets': 'false',
                },
                'audio': {
                    'content': speech_content.decode('UTF-8')
                    }
                })

        #SpeechAPIによる認識結果を保存
        response = service_request.execute()
        print(type(response))
        print(response)
        if not response.has_key("results"):
            print("no response")
            return ""

        #見やすいようにコンソール画面で出力
        speech_text = ""
        for i in response["results"]:
            speech_text += i["alternatives"][0]["transcript"]
            confidence =  i["alternatives"][0]["confidence"]
            print(speech_text,"confidence:" , confidence)

            print(speech_text.encode('utf-8'))

        return speech_text.encode('utf-8')


    #テキストを音声に変換
    def get_text_to_speech(self, speech_text, file_name):
        rf = open(file_name, 'w')

        #音声合成
        tospeech = get_texttospeech_service(self.KEY)
        service_request = tospeech.text().synthesize(
            body={
                'input': {
                    'text': speech_text
                    },
                'voice': {
                    'languageCode': 'ja-JP',           #日本語に設定
                    'name':         'ja-JP-Wavenet-A', #Wave-Net(高音質版を指定)
                },
                'audioConfig': {
                    'audioEncoding': 'LINEAR16',
                    }
                })

        #SpeechAPIによる認識結果を保存
        speech_response = service_request.execute()

        wav_response = base64.b64decode(speech_response["audioContent"])
        rf.write(wav_response)
        rf.close()


    #テキストを音声に変換
    def get_text_to_en_speech(self, speech_text, file_name):
        rf = open(file_name, 'w')

        #音声合成
        tospeech = get_texttospeech_service(self.KEY)
        service_request = tospeech.text().synthesize(
            body={
                'input': {
                    'text': speech_text
                    },
                'voice': {
                    'languageCode': 'en-US',           #英語に設定
                },
                'audioConfig': {
                    'audioEncoding': 'LINEAR16',
                    }
                })

        #SpeechAPIによる認識結果を保存
        speech_response = service_request.execute()

        wav_response = base64.b64decode(speech_response["audioContent"])
        rf.write(wav_response)
        rf.close()




