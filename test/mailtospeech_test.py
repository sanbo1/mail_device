# coding: utf-8
from __future__ import print_function
import httplib2
import os
import base64
import email

from apiclient import discovery, errors
import oauth2client
from oauth2client import client
from oauth2client import tools

import sys
import codecs
#from googleapiclient import discovery

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


# 参考サイト
# https://a-zumi.net/python-gmail-api/


#APIキーを設定
rf = open('.credentials/api_key', 'r')
key = rf.read()
rf.close()

#URL情報
DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')

#APIの情報を返す関数
def get_texttospeech_service():
    http = httplib2.Http()
    return discovery.build(
        'texttospeech', 'v1', http=http, discoveryServiceUrl=DISCOVERY_URL, developerKey=key)


class GmailClient(object):

    #メールアドレスを読み込み
    rf = open('.credentials/mail_from', 'r')
    MAIL_FROM = rf.read().strip()
    rf.close()
    rf = open('.credentials/mail_to', 'r')
    MAIL_TO = rf.read().strip()
    rf.close()


    SCOPES = 'https://mail.google.com/'
    #CLIENT_SECRET_FILE = 'client_secret.json'
    CLIENT_SECRET_FILE = 'maildeviceclient_secret.json'
    APPLICATION_NAME = 'Gmail Client'

    def __init__(self, **kwargs):
        #メールアドレスを読み込み
        rf = open('.credentials/mail_from', 'r')
        MAIL_FROM = rf.read().strip()
        rf.close()

        if "user_id" in kwargs:
            self.user_id = user_id
        else:
            #self.user_id = "me"
            self.user_id = MAIL_FROM

        credentials = self.credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('gmail', 'v1', http=http)

    # Gmailの認証処理
    def credentials(self):
        #home_dir = os.path.expanduser('~')
        #credential_dir = os.path.join(home_dir, '.credentials')

        script_dir =os.path.abspath(os.path.dirname(__file__))
        credential_dir = os.path.join(script_dir, ".credentials")

        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)

        #credential_path = os.path.join(credential_dir,
        #    'gmail-python-quickstart.json')
        credential_path = os.path.join(credential_dir, "token.json")

        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()

        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)

        return credentials

    # メールリストを取得
    def get_messages(self, q=""):
        try:
            results = self.service.users().messages().list(userId=self.user_id, q=q).execute()
            for msg in results.get("messages", []):
                message = self.service.users().messages().get(userId=self.user_id, id=msg["id"], format='raw').execute()
                #print(message['raw'])
                #print(type(message['raw']))
                #msg_str = base64.urlsafe_b64decode(message['raw']).decode("utf-8")
                msg_str = base64.urlsafe_b64decode(message['raw'].encode("utf-8")).decode("utf-8")
                #msg_str = base64.urlsafe_b64decode(message['raw']).encode("utf-8")
                #msg_str = base64.urlsafe_b64decode(message['raw'])
                self.msg = email.message_from_string(msg_str)
                yield self
        except errors.HttpError as error:
            raise("An error occurred: %s" % error)

    # 件名を取得
    @property
    def subject(self):
        subjects = email.header.decode_header(self.msg.get("Subject"))
        for subject in subjects:
            if isinstance(subject[0], bytes) and subject[1] is not None:
                return subject[0].decode(subject[1])
            else:
                return subject[0].decode()

    # 本文を取得
    @property
    def body(self):
        if self.msg.is_multipart():
            for payload in self.msg.get_payload():
                if payload.get_content_type() == "text/plain":
                    # multipart なので get_payload() で取得できるのが message のリスト
                    # 解析したいのは取得した message リストの中の本文なので、見たい charset も
                    # 解析した message の内容になるはず
                    #charset = self.msg.get_param("charset")
                    charset = payload.get_param("charset")
                    if charset is None:
                        return payload.get_payload(decode=True).decode("iso-2022-jp")
                    else:
                        return payload.get_payload(decode=True).decode(charset)
        else:
            charset = self.msg.get_param("charset")
            return self.msg.get_payload(decode=True).decode(charset)

if __name__ == '__main__':
    Gmail = GmailClient()
    messages = Gmail.get_messages()

    if not messages:
        print('No messages found.')
    else:
        cnt = 0
        for message in messages:
            print(message.subject)
            #print(message.body)
            #if cnt == 5:
            if message.subject == "Re: gmail api test":
                #print(message.body.encode('utf-8'))
                print(type(message.body))
                print(message.body)
                #print(type(message))

                rf = open('result.wav', 'w')

                #音声合成
                tospeech = get_texttospeech_service()
                service_request = tospeech.text().synthesize(
                    body={
                        'input': {
                            #'text': speech_text
                            'text': message.body
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

                break
            else:
                cnt = cnt + 1

