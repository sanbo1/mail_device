#coding:utf8
import sys
import codecs
import base64
from googleapiclient import discovery
import httplib2
import os

import apiclient
import oauth2client
import argparse
flags = argparse.ArgumentParser(
    parents=[oauth2client.tools.argparser]
).parse_args()

import base64
from email.mime.text import MIMEText
from email.utils import formatdate
import traceback

import pyaudio
import time
import wave

import requests
import json


#APIキーを設定
rf = open('.credentials/api_key', 'r')
key = rf.read()
rf.close()

#音声認識に使うファイル名
#speech_file = "sample.wav"
speech_file = "test.wav"

# チャンク数を指定
CHUNK = 1024
filename = "result.wav"

#URL情報
DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')

#APIの情報を返す関数
def get_speech_service():
    http = httplib2.Http()
    return discovery.build(
        'speech', 'v1', http=http, discoveryServiceUrl=DISCOVERY_URL, developerKey=key)

def get_texttospeech_service():
    http = httplib2.Http()
    return discovery.build(
        'texttospeech', 'v1', http=http, discoveryServiceUrl=DISCOVERY_URL, developerKey=key)

def get_translation_service():
    http = httplib2.Http()
    return discovery.build(
        'translation', 'v2', http=http, discoveryServiceUrl=DISCOVERY_URL, developerKey=key)
        #'translation', 'v2', http=http, discoveryServiceUrl=DISCOVERY_URL+'&target="en"', developerKey=key)


#メールアドレスを読み込み
rf = open('.credentials/mail_from', 'r')
MAIL_FROM = rf.read().strip()
rf.close()
rf = open('.credentials/mail_to', 'r')
MAIL_TO = rf.read().strip()
rf.close()


def create_text_to_speech_file(speech_text):
    rf = open(filename, 'w')

    #音声合成
    tospeech = get_texttospeech_service()
    service_request = tospeech.text().synthesize(
        body={
            'input': {
                'text': speech_text
                },
            'voice': {
                #'languageCode': 'ja-JP', #日本語に設定
                'languageCode': 'en-US', #英語に設定
            },
            'audioConfig': {
                'audioEncoding': 'LINEAR16',
                }
            })

    #SpeechAPIによる認識結果を保存
    speech_response = service_request.execute()

    #print(speech_response)

    wav_response = base64.b64decode(speech_response["audioContent"])
    rf.write(wav_response)
    rf.close()


def get_speech_text():
    #音声ファイルを開く
    with open(speech_file, 'rb') as speech:
        speech_content = base64.b64encode(speech.read())

    #APIの情報を取得して、音声認識を行う
    service = get_speech_service()
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

    # デフォルトの文字コードを出力する．
    print 'defaultencoding:', sys.getdefaultencoding()

    #見やすいようにコンソール画面で出力
    speech_text = ""
    for i in response["results"]:
        print(i)
        speech_text += i["alternatives"][0]["transcript"]
        confidence =  i["alternatives"][0]["confidence"]
        print(speech_text,"confidence:" , confidence)

        print(type(speech_text))
        print(speech_text.encode('utf-8'))

    return speech_text.encode('utf-8')


def get_text_jp_to_en(speech_text):
    #音声合成
    translation = get_translation_service()
    #print(dir(translation))
    #print(dir(translation.translations))
    #print(dir(translation.languages))
    #print(dir(discovery.build))
    print(speech_text)
    #service_request = translation.translations().translate(
    #    body={
    #        #'q': speech_text,
    #        'q': "こんにちは",
    #        'source': 'ja',
    #        'target': 'en',
    #        'format': 'text'
    #        }
    #    #{
    #    #'q': "こんにちは",
    #    #'source': 'ja',
    #    #'target': 'en',
    #    #'format': 'text'
    #    #}
    #    )

    #translations = translation.translations()
    #print(dir(translations))
    #translations.setQ(speech_text)

    #print(dir(service_request))
    #print(service_request.body)
    #print(service_request.uri)
    #print(service_request.http)
    #print(service_request.headers)
    #print(service_request.method)

    #SpeechAPIによる認識結果を保存
    #translation_response = service_request.execute()
    payload={
            'q': speech_text,
            #'q': "こんにちは",
            'source': 'ja',
            'target': 'en',
            'format': 'text'
        }
    #translation_url = DISCOVERY_URL.replace('{api}', 'translation').replace('{apiVersion}', 'v2')
    #print(translation_url)
    #translation_response = requests.post(DISCOVERY_URL.replace('{api}', 'translation').replace('{apiVersion}', 'v2'), params=payload)
    service_request = translation.translations().translate(body={})
    print(service_request.uri)
    translation_response = requests.post(service_request.uri, params=payload)


    print(translation_response)
    print(dir(translation_response))
    print(translation_response.text)
    res_json = json.loads(translation_response.text)
    print(res_json)
    #print(res_json[u'data'][u'translations'][u'translatedText'])
    res_text = res_json['data']['translations'][0]['translatedText']
    print(res_text)

    #wav_response = base64.b64decode(translation_response["audioContent"])
    #rf.write(wav_response)
    #rf.close()

    return res_text


def main():
    try:
        speech_text = get_speech_text()

        print(speech_text)
        res_text = get_text_jp_to_en(speech_text)
        print(res_text)

        create_text_to_speech_file(res_text)
        #create_text_to_speech_file(speech_text)

        ##########################################
        wf = wave.open(filename, 'rb')

        # PyAudioのインスタンスを生成
        p = pyaudio.PyAudio()

        # Streamを生成
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        """
         format: ストリームを読み書きする際のデータ型
         channels: モノラルだと1、ステレオだと2、それ以外の数字は入らない
         rate: サンプル周波数
         output: 出力モード
        """

        # データを1度に1024個読み取る
        data = wf.readframes(CHUNK)

        # 実行
        while data != '':
            # ストリームへの書き込み
            stream.write(data)
            # 再度1024個読み取る
            data = wf.readframes(CHUNK)

        # ファイルが終わったら終了処理
        stream.stop_stream()
        stream.close()

        p.terminate()

    except apiclient.errors.HttpError:
        print("------start trace------")
        traceback.print_exc()
        print("------end trace------")


if __name__ == "__main__":
    main()
