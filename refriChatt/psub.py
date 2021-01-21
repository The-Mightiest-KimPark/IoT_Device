# [START speech_transcribe_streaming_mic]
from __future__ import division

import re
import sys

from google.cloud import speech

import pyaudio
from six.moves import queue

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

#sub,pub
import paho.mqtt.client as mqtt

# from pymongo import MongoClient
from datetime import datetime,date
import json
import requests

# 쓰레드
import threading
from threading import Thread

# 카카오 음성합성
import requests
import io
import time
from pydub import AudioSegment
from pydub.playback import play

# S3 버킷 전송
import boto3
import mimetypes

import simpleaudio as sa

# 캠 영상 캡쳐
import cv2
import os
import datetime

# 냉장고 내부 Led 
import RPi.GPIO as GPIO

import numpy as np

from numpy import nan as NA

from bs4 import BeautifulSoup

# 냉장고 내부 Led 센서 설정
GPIO.setmode(GPIO.BCM)
GPIO.setup(17,GPIO.OUT)
GPIO.setup(18,GPIO.OUT)
GPIO.setup(23,GPIO.OUT)
GPIO.setup(24,GPIO.OUT)

# aws 서버와 통신

aws_url = "https://8i8wxh81q2.execute-api.us-east-1.amazonaws.com/" 
aws_header ={"Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                # "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
                "Access-Control-Allow-Credentials": "true"
            }

# 음성 서버통신
speech_url ="http://13.209.95.229/"
speech_header={"Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                # "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
                "Access-Control-Allow-Credentials": "true"
            }

# 카카오 합성 설정
URL = "https://kakaoi-newtone-openapi.kakao.com/v1/synthesize"

rest_api_key = ''

HEADERS = {
"Content-Type" : "application/xml",
"Authorization" : "KakaoAK " + rest_api_key,
}

# S3 클라이언트 생성
s3 = boto3.client('s3')

# 변수 선언
topicName = ""
textValue = ""
speakWhat =""
fridge_number="multicampus"

like_recipe =False

recipe = {}
# 불 끄고 키기
def ledOn():
    GPIO.output(17, True)
    GPIO.output(18, True)
    GPIO.output(23, True)
    GPIO.output(24, True)

def ledOff():
    GPIO.output(17, False)
    GPIO.output(18, False)
    GPIO.output(23, False)
    GPIO.output(24, False)

# 냉장고 내부 사진 촬영 함수
def foodCapture():
    print("사진 함수 들어옴")
    cap = cv2.VideoCapture(0) # 0번 카메라

    # 캡쳐 Frame
    retval, frame = cap.read()
    # if not retval: break
    
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d %H:%M:%S.%f')
    print(str(nowDate))
    pic_name = "multicampus"+".jpg"
    cv2.imshow('frame', frame)
    cv2.imwrite(pic_name, frame)


    cap.release()
    cv2.destroyAllWindows()
    print("사진 함수 무사히 마침")

    # 사진 찍고 난 후 냉장고c 불꺼짐


    ledOff() 
    print("냉장고불꺼짐")

    
    # s3로 사진 업로드
    bucket_name = 'themightiestkpk1'

    #첫번째 매개변수:로컬에서 올리는 파일이름
    #두번째 매개변수 : s3버킷 이름
    #세번째 매개변수 : 버킷에 저장될 파일 이름

    
    # s3.upload_file(pic_name,bucket_name,pic_name)

    s3 = boto3.resource('s3')
    
    s3.meta.client.upload_file(pic_name,bucket_name,pic_name,ExtraArgs={'ContentType': 'image/jpeg'})
    
    doc={
        "url" : "https://themightiestkpk1.s3.amazonaws.com/" +pic_name,
        "fridge_number":"multicampus",
        "reg_date" : str(nowDate)
    }
    res = requests.post("http://3.92.44.79/api/ai-img-grocery/",headers=speech_header,data=json.dumps(doc))
    text = res.text

    print("서버값사진업로드:"+text)

   

    # 서버로 문 닫혀있는 상태로 값 변경



    
    # db.sensors.insert_one(doc)

    # 라즈베리에 저장했던 이미지 다시 지우기
    os.remove(pic_name)


# 문 닫힌 상태 : 0 / 문 열린 상태 : 1
# sub 토픽 값에 따라 해야할 일 지정
def menu(topicName,value):
    # 앱에서 문 열기 (모션센서 감지가 0일 때 열 수 있음)
    if "door/android/open" in topicName:
        print("문 열었습니다")
        client.publish("sensors/door/motion/open", 1)

    # 앱에서 문 닫기 (모션센서 감지가 0일 때 닫을 수 있음)
    elif "door/android/close" in topicName:
        print("문 닫았습니다")
        client.publish("sensors/door/motion/close", 0)

    

    # 모션이 0이어서 문열기에 성공했을 경우 다시 sub받아서 문이 열린 상태로 값을 바꿔줌
    elif "state/open" in topicName:
        print("파이:문열림 상태 서버로 1값 보내기")
        
        # 냉장고 불켜짐
        ledOn()
        print("냉장고 불켜짐")
        now = datetime.datetime.now()
        nowDate = now.strftime('%Y-%m-%d %H:%M:%S.%f')
        doc = {
            "fridge_number" : fridge_number,
            "name" : "door",    
            "value" : 1,
            "reg_date" : str(nowDate)
            
        }
        print("서버 값 날짜 뭐라고뜨니"+str(nowDate))
        res = requests.post(aws_url+"dev/sensor", headers=aws_header, data=json.dumps(doc))
        print(res)
        text = res.text

        print("서버값:"+text)
        speak("문을 열었습니다","progress")
    
    # 모션이 0이어서 문닫기에 성공했을 경우 다시 sub받아서 문이 열린 상태로 값을 바꿔줌
    elif "state/close" in topicName:
        now = datetime.datetime.now()
        nowDate = now.strftime('%Y-%m-%d %H:%M:%S.%f')
        doc ={
            "fridge_number" : fridge_number,
            "name" : "door",
            "value" : 0,
            "reg_date" : str(nowDate)
        }
        # 문이 닫히고 나서 사진 찍기
        thread_picture = threading.Thread(target=foodCapture)
        thread_picture.start()
        speak("문을 닫았습니다","progress")
        

        res = requests.post(aws_url+"dev/sensor",headers=aws_header,data=json.dumps(doc))
        text = res.text

        doc2 = {
            "email" : "multi@naver.com"
        }

        res2 = requests.post("http://3.93.61.7/api/answer-save/",headers=aws_header,data=json.dumps(doc2))

        print("서버값:"+text)

        print("이메일값 전송 결과-------------"+res2.text+"-----------")
        
    
    # 0이상이면 화재 감지 서버에서 바로 문자알림 가게해야함 
    elif "flame" in topicName:
        now = datetime.datetime.now()
        nowDate = now.strftime('%Y-%m-%d %H:%M:%S.%f')
        print("불꽃 들어옴")
        doc={
             "fridge_number" : fridge_number,
            "name" : "flame",
            "value" : value,
            "reg_date" : str(nowDate)
        }
        res = requests.post(aws_url+"dev/sensor",headers=aws_header,data=json.dumps(doc))
        text = res.text

        print("서버값:"+text)
    # 습도 측정 값
    elif "humi" in topicName:
        now = datetime.datetime.now()
        nowDate = now.strftime('%Y-%m-%d %H:%M:%S.%f')
        print("습도 들어옴")
        doc={
            "fridge_number" : fridge_number,
            "name" : "humi",
            "value" : value,
            "reg_date" : str(nowDate)
        }
        res = requests.post(aws_url+"dev/sensor",headers=aws_header,data=json.dumps(doc))
        text = res.text

        print("서버값:"+text)
    # 온도 측정 값
    elif "temp" in topicName:
        now = datetime.datetime.now()
        nowDate = now.strftime('%Y-%m-%d %H:%M:%S.%f')
        print("온도 들어옴")
        doc={
             "fridge_number" : fridge_number,
            "name" : "temp",
            "value" :value,
            "reg_date" : str(nowDate)
        }
        res = requests.post(aws_url+"dev/sensor",headers=aws_header,data=json.dumps(doc))
        text = res.text

        print("서버값:"+text)



class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


def listen_print_loop(responses):
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()

            num_chars_printed = len(transcript)
           

        else:
            print(transcript + overwrite_chars)
            myScript=transcript + overwrite_chars
            
        
            if "문 열" in myScript:
                client.publish("sensors/door/mic/open", "1")

            elif "문 닫" in myScript:
                client.publish("sensors/door/mic/close", "0")

            elif "레시피 추천" in myScript:
                speak("추천","recommend")
            elif "즐겨찾기 추가" in myScript:
                    if like_recipe==False:
                        speak("레시피 정보가 없습니다.","register_recipe_null")
                    if like_recipe==True:
                        speak("김치볶음밥 레시피를 즐겨찾기 했습니다.","register_recipe")
            elif "즐겨찾기 조회" in myScript:
                    speak("즐겨찾기 리스트가 없습니다","favorite_recipe")

            elif "냉장고" in myScript:
                if "뭐 있어" in myScript:
                    speak("냉장고에 식재료가 없습니다","whatGrocery")
    
            elif "몇 개" in myScript:
                speak(myScript,"jr")

            else:
                speak(myScript,"jr")
           

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r"\b(종료|quit)\b", transcript, re.I):
                print("Exiting..")
                break

            num_chars_printed = 0



def on_connect(client,userdata, flags, rc):
    print("Connected with result code " + str(rc))
    thread_mic.start()
    
    
    if rc == 0:
        client.subscribe("sensors/#")
    else:
        print("연결실패 : ",rc)

def on_message(client, userdata, msg):
    value = float(msg.payload.decode())
    print(f"{msg.topic} {value}")
    
    
    menu(msg.topic,value)

    



# 구글 어시스턴트 음성인식
def mic():
    
    language_code = "ko-KR"  # a BCP-47 language tag

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        listen_print_loop(responses)



       

# 카카오 음성 합성/바로 재생되게
def speak(textValue,speakWhat):
    # 오늘의 레시피 추천
    if "recommend" == speakWhat:
        res = requests.get(speech_url+"api/recomm-recipe-one",params={"email" : "multi@naver.com"})
        global recipe
        recipe = res.json()

        global like_recipe
        like_recipe = True


        print(res.text)
        print("음식이름" + recipe['name'])
        
        textValue = "오늘의 레시피는 "+ recipe['name'] + "입니다. 재료는 " + recipe['ingredient'] + "를 준비해주세요. 그럼 즐거운 요리 시간되세요!" 

    # 현재 냉장고 식재료 
    if "whatGrocery" == speakWhat:
        res = requests.get(speech_url+"api/user-input-grocery",params={"email" : "multi@naver.com"})
        print("api요청 잘됐나요?2"+str(res.status_code))
        print(res.json())
        groceryList = res.json()

        textValue = "현재 냉장고의 식재료는 "

        if len(groceryList) !=0:
            for grocery in groceryList:
                textValue +=grocery['name'] +str(grocery['count']) +"개"+"<break time='ms'/>"
            textValue += "있습니다."
        else:
            textValue = "현재 냉장고의 식재료는 비어있습니다."

    if "hi" == speakWhat:
        textValue = textValue


    if "register_recipe_null" == speakWhat:
        textValue = textValue

    if "register_recipe" == speakWhat:
        textValue = recipe['name'] +"레시피를 즐겨찾기에 추가했습니다!"
        res = requests.put(speech_url+"api/recipe-favorite/",data={'email':recipe['email'],'all_recipe_id':recipe['all_recipe_id']})
        print(str(res.status_code))

    if "favorite_recipe" == speakWhat:
        res = requests.get(speech_url+"api/recipe-favorite",params={"email" : "multi@naver.com"})
        favorite_recipeList = res.json()
        textValue = "현재 나의 즐겨찾기 레시피 요리는 "

        if len(favorite_recipeList) !=0:
            for frecipe in favorite_recipeList:
                textValue += frecipe['name'] +",                "
            textValue +="입니다"  
        else:
            textValue = "현재 나의 즐겨찾기 레시피가 없습니다."    

        print(str(res.status_code))

# 빅데이터로 결과값 얻는 부분
    if "jr" == speakWhat:
        res = requests.get("http://3.93.61.7/api/answer-count/",params={"email" : "multi@naver.com","query" : textValue})
       
        answer = res.json()
        textValue = answer['result']


    DATA="<speak><prosody rate='slow' volume='medium'>"+textValue+"</prosody></speak>"
    res = requests.post(URL, headers = HEADERS, data = DATA.encode('utf-8'))
    sound = io.BytesIO(res.content)
    song = AudioSegment.from_file(sound)
    # p = PlayThread(song)
    # p.run()
    play(song)



#통신
client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

thread_mic = threading.Thread(target=mic)
try:
    
    client.connect("localhost")
    client.loop_forever()
  
except Exception as err:
    print('에러 : %s' %err)
like_recipe = False
print("-----end main thread-----")