# -*- coding: utf-8 -*-
import os
import time
import threading
import RPi.GPIO as GPIO  #GPIOにアクセスするライブラリをimport

from my_modules.audio import MyAudioClient
from my_modules.gcp.gmail import GmailClient
from my_modules.gcp.gspeech import GspeechClient
from my_modules.gcp.gtranslation import GtranslationClient

script_dir =os.path.abspath(os.path.dirname(__file__))

data_dir = os.path.join(script_dir, "data")
input_file = os.path.join(data_dir, "input.wav")
output_file = os.path.join(data_dir, "output.wav")

credential_dir = os.path.join(os.path.join(script_dir, "my_modules/gcp"), ".credentials")

if not os.path.exists(credential_dir):
    os.makedirs(credential_dir)

#メールアドレスを読み込み
rf = open(os.path.join(credential_dir, "mail_to"), 'r')
TARGET_ADDR = rf.read().strip()
rf.close()

GPIO_BTN1 = 17
GPIO_LED1 = 27
GPIO_BTN2 = 26
GPIO_LED2 = 19

#・GPIO.BOARD: 物理ピン番号（左上からの連番）
#・GPIO.BCM: 役割ピン番号（broadcomが命名しているもの）
GPIO.setmode(GPIO.BCM)  #GPIOへアクセスする番号をBCMの番号で指定することを宣言します。

GPIO.setup(GPIO_LED1, GPIO.OUT)
GPIO.setup(GPIO_BTN1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_LED2, GPIO.OUT)
GPIO.setup(GPIO_BTN2, GPIO.IN, pull_up_down=GPIO.PUD_UP)


#def ovserve_message_send_btn(Gmail, Gspeech, MyAudio):
def ovserve_message_send_btn(gpio_pin):
    #print("ovserve_message_send_btn start")
    #Gmail クラス生成
    Gmail = GmailClient(TARGET_ADDR)
    #Google Speech to Text / Text to Speech クラス生成
    Gspeech = GspeechClient()
    #Audio クラス生成
    MyAudio = MyAudioClient()

    #録音
    GPIO.output(GPIO_LED1,GPIO.HIGH)
    MyAudio.rec(input_file)
    GPIO.output(GPIO_LED1,GPIO.LOW)

    #
    #音声をテキストに変換
    #
    speech_text = Gspeech.get_speech_to_text(input_file)
    if speech_text == "":
        pass
        #print("not in message")

    #先頭5文字(15byte)が"英語に翻訳"の場合、翻訳して音声再生
    elif speech_text[0:15] == "英語に翻訳":
        #Translation クラス生成
        Gtranslation = GtranslationClient()
        mail_text = Gtranslation.get_text_jp_to_en(speech_text[15:-1])

        #テキストを音声に変換
        Gspeech.get_text_to_en_speech(mail_text, output_file)
        #再生
        MyAudio.play(output_file)

    else:
        #print(speech_text)

        #メール送信
        Gmail.send_message(speech_text)

    #1秒毎
    time.sleep(1)

#コールバック登録ができるのは１つまで
def ovserve_message_read_btn(e, Gmail, Gspeech, MyAudio):
#def ovserve_message_read_btn(gpio_pin):
    #print("ovserve_message_read_btn start")

    while True:
        #print("start")
        GPIO.wait_for_edge(GPIO_BTN2, GPIO.RISING)
        #print("end")
        #if GPIO.input(GPIO_BTN2):
        #    # HIGHの場合
        #    print("HIGH")
        #    pass
        #else:
        #    # LOWの場合
        #    print("LOW")
        #新メッセージ再生
        e.set()
        GPIO.output(GPIO_LED2,GPIO.LOW)
        MyAudio.play(output_file)

        #1秒毎
        time.sleep(1)



def ovserve_new_message(e, Gmail, Gspeech, MyAudio):
    #print("ovserve_new_message start")

    e.set()

    last_message = ""
    while True:
        #
        #メール受信
        #
        #メッセージ本文は不要な改行を削除してUTF8にエンコード
        mail_text = Gmail.get_new_message().strip().encode('utf-8')
        #テスト用にメッセージ取得時に一瞬光るようにする
        GPIO.output(GPIO_LED2,GPIO.HIGH)
        if e.isSet():
            time.sleep(0.1)
            GPIO.output(GPIO_LED2,GPIO.LOW)
        #print(type(mail_text))
        #print(mail_text)

        #
        #メッセージ受信
        #
        #起動後の初回処理は音声データの作成は行うが再生は行わない
        if last_message == "":
            print(mail_text)
            #テキストを音声に変換
            Gspeech.get_text_to_speech(mail_text, output_file)
            #メッセージを保存
            last_message = mail_text

        #読み込んだメッセージが前回と同じなら無視
        elif last_message == mail_text:
            pass

        #ヘルプメッセージ
        elif (mail_text == "Help" or mail_text == "help" or mail_text == "ヘルプ" or mail_text == "へるぷ"):
            print(mail_text)
            help_text = "音声ファイル：前回音声認識を行ったときの音声ファイルを添付してメールを送信する"
            #メール送信
            Gmail.send_message(help_text)

        #音声ファイル添付
        elif mail_text == "音声ファイル":
            print(mail_text)
            Gmail.send_attached_message("直近の音声", input_file)

        #特定メッセージでなかった場合、メッセージの再生
        elif not (last_message == "" or last_message == mail_text):
            #
            #テキストを音声に変換
            #
            Gspeech.get_text_to_speech(mail_text, output_file)
            #新メッセージ受信通知
            e.clear()
            GPIO.output(GPIO_LED2,GPIO.HIGH)
            #再生
            MyAudio.play(output_file)
            #メッセージを保存
            last_message = mail_text

        #5秒毎
        time.sleep(5)


def main():
    time.sleep(10)

    #Gmail クラス生成
    Gmail = GmailClient(TARGET_ADDR)
    #Google Speech to Text / Text to Speech クラス生成
    Gspeech = GspeechClient()
    #Audio クラス生成
    MyAudio = MyAudioClient()

    GPIO.output(GPIO_LED1,GPIO.LOW)

    #・GPIO.FALLING → 立ち下がりエッジ
    #・GPIO.RISING → 立ち上エッジ
    #・GPIO.BOTH → 両エッジ
    GPIO.add_event_detect(GPIO_BTN1, GPIO.RISING, bouncetime=100)
    GPIO.add_event_callback(GPIO_BTN1, ovserve_message_send_btn)

    #GPIO.add_event_callback(GPIO_BTN2, ovserve_message_read_btn)

    try:
        #GPIO.output(GPIO_LED1,GPIO.LOW)
        #time.sleep(0.1)

        e = threading.Event()

        thread_1 = threading.Thread(target=ovserve_message_read_btn, args=(e, Gmail, Gspeech, MyAudio,))
        # thread_1をデーモンに設定する。メインスレッドが終了すると、デーモンスレッドは一緒に終了する
        thread_1.setDaemon(True)
        thread_1.start()

        thread_2 = threading.Thread(target=ovserve_new_message, args=(e, Gmail, Gspeech, MyAudio,))
        # thread_2をデーモンに設定する。メインスレッドが終了すると、デーモンスレッドは一緒に終了する
        thread_2.setDaemon(True)
        thread_2.start()

    except KeyboardInterrupt:
        GPIO.cleanup()

    #メインループ
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
