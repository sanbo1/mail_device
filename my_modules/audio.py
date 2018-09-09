# -*- coding: utf-8 -*-

import pyaudio
import wave


class MyAudioClient(object):

    def __init__(self):
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1        # 1: モノラル 2: ステレオ
        #サンプリングレート、マイク性能に依存
        self.RATE = 16000
        self.RECORD_SECONDS = 5      # 5秒録音
        self.CHUNK = 1024


    def rec(self, filename):
        #pyaudio
        p = pyaudio.PyAudio()

        #マイクからデータ取得
        stream = p.open(format = self.FORMAT,
                        channels = self.CHANNELS,
                        rate = self.RATE,
                        input = True,
                        frames_per_buffer = self.CHUNK)
        all = []
        for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            data = stream.read(self.CHUNK)
            all.append(data)

        stream.stop_stream()
        stream.close()

        data = ''.join(all)
        out = wave.open(filename,'w')
        out.setnchannels(self.CHANNELS) #mono
        #out.setsampwidth(2) #16bits
        out.setsampwidth(p.get_sample_size(self.FORMAT)) #16bits
        out.setframerate(self.RATE)
        out.writeframes(data)
        out.close()

        p.terminate()

    def play(self, filename):
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
        data = wf.readframes(self.CHUNK)

        # 実行
        while data != '':
            # ストリームへの書き込み
            stream.write(data)
            # 再度1024個読み取る
            data = wf.readframes(self.CHUNK)

        # ファイルが終わったら終了処理
        stream.stop_stream()
        stream.close()

        p.terminate()

