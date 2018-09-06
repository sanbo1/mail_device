# -*- coding: utf-8 -*-
#マイク0番からの入力を受ける。一定時間(RECROD_SECONDS)だけ録音し、ファイル名：mono.wavで保存する。

import pyaudio
import sys
import time
import wave

# チャンク数を指定
CHUNK = 1024
filename = "rec_play_test.wav"

if __name__ == '__main__':
    #chunk = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1        # 1: モノラル 2: ステレオ
    #サンプリングレート、マイク性能に依存
    #RATE = 44100
    RATE = 16000
    #RECORD_SECONDS = input('Please input recoding time>>>')
    RECORD_SECONDS = 5      # 5秒録音

    #pyaudio
    p = pyaudio.PyAudio()

    #マイクからデータ取得
    stream = p.open(format = FORMAT,
                    channels = CHANNELS,
                    rate = RATE,
                    input = True,
                    frames_per_buffer = CHUNK)
    all = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        all.append(data)

    stream.stop_stream()
    stream.close()

    data = ''.join(all)
    out = wave.open(filename,'w')
    out.setnchannels(CHANNELS) #mono
    #out.setsampwidth(2) #16bits
    out.setsampwidth(p.get_sample_size(FORMAT)) #16bits
    out.setframerate(RATE)
    out.writeframes(data)
    out.close()

    p.terminate()


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
