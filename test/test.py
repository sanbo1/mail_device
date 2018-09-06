#coding:utf8
import sys
import codecs
import base64
from googleapiclient import discovery
import httplib2

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
for i in response["results"]:
    print(i)
    #print(i["alternatives"][0]["transcript"].decode('unicode-escape'),"confidence:" , i["alternatives"][0]["confidence"])
    speech_text = i["alternatives"][0]["transcript"]
    confidence =  i["alternatives"][0]["confidence"]
    #print(speech_text.decode('unicode-escape'),"confidence:" , confidence)
    #print(speech_text.encode('UTF-8'),"confidence:" , confidence)
    #print(speech_text.encode('ascii').decode('unicode-escape'),"confidence:" , confidence)
    #print(speech_text.encode('ascii'),"confidence:" , confidence)
    #print(speech_text.encode().decode("unicode_escape"),"confidence:" , confidence)
    print(speech_text,"confidence:" , confidence)

    print(type(speech_text))
    print(speech_text.encode('utf-8'))


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

