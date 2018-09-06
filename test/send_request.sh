curl -s -X POST -H "Content-Type: application/json" --data-binary @request.json "https://speech.googleapis.com/v1beta1/speech:syncrecognize?key=$1"
