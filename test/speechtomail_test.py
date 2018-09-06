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


#APIキーを設定
rf = open('.credentials/api_key', 'r')
key = rf.read()
rf.close()

#音声認識に使うファイル名
#speech_file = "sample.wav"
speech_file = "test.wav"

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


# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
#SCOPES = "https://www.googleapis.com/auth/gmail.send"
SCOPES = 'https://mail.google.com/'
#CLIENT_SECRET_FILE = "client_secret.json"
CLIENT_SECRET_FILE = "maildeviceclient_secret.json"
APPLICATION_NAME = "MyGmailSender"

#MAIL_FROM = "example@gmail.com"
#MAIL_TO = "example+alias@gmail.com"

#メールアドレスを読み込み
rf = open('.credentials/mail_from', 'r')
MAIL_FROM = rf.read().strip()
rf.close()
rf = open('.credentials/mail_to', 'r')
MAIL_TO = rf.read().strip()
rf.close()

def get_credentials():
    script_dir =os.path.abspath(os.path.dirname(__file__))
    credential_dir = os.path.join(script_dir, ".credentials")

    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    #credential_path = os.path.join(credential_dir,
    #                               "my-gmail-sender.json")
    credential_path = os.path.join(credential_dir, "token.json")

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = oauth2client.client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = oauth2client.tools.run_flow(flow, store, flags)
        print("Storing credentials to " + credential_path)
    return credentials



def create_text_to_speech_file(speech_text):
    rf = open('result.wav', 'w')

    #音声合成
    tospeech = get_texttospeech_service()
    service_request = tospeech.text().synthesize(
        body={
            'input': {
                'text': speech_text
                },
            'voice': {
                'languageCode': 'ja-JP', #日本語に設定
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
        #print(i["alternatives"][0]["transcript"].decode('unicode-escape'),"confidence:" , i["alternatives"][0]["confidence"])
        speech_text += i["alternatives"][0]["transcript"]
        confidence =  i["alternatives"][0]["confidence"]
        #print(speech_text.decode('unicode-escape'),"confidence:" , confidence)
        #print(speech_text.encode('UTF-8'),"confidence:" , confidence)
        #print(speech_text.encode('ascii').decode('unicode-escape'),"confidence:" , confidence)
        #print(speech_text.encode('ascii'),"confidence:" , confidence)
        #print(speech_text.encode().decode("unicode_escape"),"confidence:" , confidence)
        print(speech_text,"confidence:" , confidence)

        print(type(speech_text))
        print(speech_text.encode('utf-8'))

    return speech_text


def create_message(mail_str):
    #message = MIMEText(mail_str)
    message = MIMEText(mail_str, 'plain', 'utf-8')    # 'plain' は JIS エンコード(iso-2022-jp) の意味(引数はutf-8をplainに変換)
    #message = MIMEText("test message")
    #message = MIMEText("")
    #message = MIMEText("テストメッセージ")
    message["from"] = MAIL_FROM
    message["to"] = MAIL_TO
    message["subject"] = "gmail api test"
    message["Date"] = formatdate(localtime=True)

    #print(message)

    byte_msg = message.as_string().encode(encoding="UTF-8")
    byte_msg_b64encoded = base64.urlsafe_b64encode(byte_msg)
    str_msg_b64encoded = byte_msg_b64encoded.decode(encoding="UTF-8")

    return {"raw": str_msg_b64encoded}


def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = apiclient.discovery.build("gmail", "v1", http=http)

    try:
        speech_text = get_speech_text()
        result = service.users().messages().send(
            userId=MAIL_FROM,
            body=create_message(speech_text.encode('utf-8'))
            #body=create_message("")
        ).execute()

        print("Message Id: {}".format(result["id"]))

    except apiclient.errors.HttpError:
        print("------start trace------")
        traceback.print_exc()
        print("------end trace------")


if __name__ == "__main__":
    main()
