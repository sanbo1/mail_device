# -*- coding: utf-8 -*-

import httplib2
import os
import base64
import email

import apiclient
from apiclient import discovery, errors
import oauth2client
from oauth2client import client
from oauth2client import tools

from email.mime.text import MIMEText
from email.utils import formatdate
import traceback

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


class GmailClient(object):

    SCOPES = 'https://mail.google.com/'
    #CLIENT_SECRET_FILE = 'client_secret.json'
    CLIENT_SECRET_FILE = 'maildeviceclient_secret.json'
    APPLICATION_NAME = 'Gmail Client'
    TARGET_SUBJECT = "gmail api test"

    def __init__(self, mailaddr):
        script_dir =os.path.abspath(os.path.dirname(__file__))
        self.credential_dir = os.path.join(script_dir, ".credentials")

        if not os.path.exists(self.credential_dir):
            os.makedirs(self.credential_dir)

        #メールアドレスを読み込み
        rf = open(os.path.join(self.credential_dir, "mail_from"), 'r')
        self.MAIL_FROM = rf.read().strip()
        rf.close()

        self.MAIL_TO = mailaddr

        self.user_id = self.MAIL_FROM

        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('gmail', 'v1', http=http)

    # Gmailの認証処理
    def get_credentials(self):
        credential_path = os.path.join(self.credential_dir, "token.json")

        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()

        if not credentials or credentials.invalid:
            secret_path = os.path.join(self.credential_dir, self.CLIENT_SECRET_FILE)
            flow = client.flow_from_clientsecrets(secret_path, self.SCOPES)
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
                msg_str = base64.urlsafe_b64decode(message['raw'].encode("utf-8")).decode("utf-8")
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


    def get_new_message(self):
        messages = self.get_messages()

        if not messages:
            print('No messages found.')
        else:
            cnt = 0
            for message in messages:
                #print(message.subject)
                if message.subject == "Re: " + self.TARGET_SUBJECT:
                    #print(message.body)
                    return message.body
                else:
                    cnt = cnt + 1

    def create_message(self, mail_str):
        message = MIMEText(mail_str, 'plain', 'utf-8')    # 'plain' は JIS エンコード(iso-2022-jp) の意味(引数はutf-8をplainに変換)
        message["from"] = self.MAIL_FROM
        message["to"] = self.MAIL_TO
        message["subject"] = self.TARGET_SUBJECT
        message["Date"] = formatdate(localtime=True)

        byte_msg = message.as_string().encode(encoding="UTF-8")
        byte_msg_b64encoded = base64.urlsafe_b64encode(byte_msg)
        str_msg_b64encoded = byte_msg_b64encoded.decode(encoding="UTF-8")

        return {"raw": str_msg_b64encoded}

    def send_message(self, speech_text):
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = apiclient.discovery.build("gmail", "v1", http=http)

        try:
            result = service.users().messages().send(
                userId=self.MAIL_FROM,
                body=self.create_message(speech_text.encode('utf-8'))
            ).execute()

            print("Message Id: {}".format(result["id"]))

        except apiclient.errors.HttpError:
            print("------start trace------")
            traceback.print_exc()
            print("------end trace------")


