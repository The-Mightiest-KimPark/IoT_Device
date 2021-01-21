// 자동문, 모션감지 프로그램

#include <car.h>
#include <WiFiEsp.h>
#include <SoftwareSerial.h>
#include <PubSubClient.h>
#include <Arduino.h>
#include <WifiUtil.h>

#include <Servo.h>

#include <stdio.h>
#include <string.h>

// 3강의실 네트워크
// const char ssid[] = "Campus7_Room3_2.4";
// const char password[] = "12345678";
// const char mqtt_server[] = "192.168.0.153";

// 1강의실 네트워크
const char ssid[] = "Campus7_Room1_2.4GHz";
const char password[] = "12345678";
const char mqtt_server[] = "192.168.0.122";

//우리집 네트워크
// const char ssid[] = "KT_GiGA_2G_4E8A";
// const char password[] = "5zg34hc581";
// const char mqtt_server[] = "172.30.1.3";

//통신 설정
SoftwareSerial SoftwareSerial(11, 12);
WifiUtil wifi(11, 12);

// MQTT용 WIFI 클라이언트 객체 초기화
WiFiEspClient espClient;
PubSubClient client(espClient);



//서보모터
Servo servoMotor1;
Servo servoMotor2;

const int servoMotorPin1 = 9;//주황색-문 위에
const int servoMotorPin2 = 8;//노란색(날개달린서보모터)-문아래

//모션센서
int pir = 4; //PIR 모션센서



void mqtt_init() {
    
    client.setServer(mqtt_server, 1883);

    // subscriber인경우 메시지 수신시 호출할 콜백 함수 등록
    client.setCallback(callback);

}

//라즈베리파이에서 온 값이 들어오는 함수
void callback(char* topic, byte* payload, unsigned int length) {
    payload[length] = NULL;
    char *message = payload;
    
    // 문 개폐에 관한 토픽
    // 안드로이드에서 문 개폐 동작제어
    if(strstr(topic,"sensors/door/motion/open")!=NULL){
        Serial.println("모션이 감지됨/문열릴수없음");
        if(detectMotion()==LOW){
            openDoor();
            Serial.println("안드로이드 문열림");
        }
    }
    else if(strstr(topic,"sensors/door/motion/close")!=NULL){
        Serial.println("모션이 감지됨/문닫힐수없음");
        if(detectMotion()==LOW){
            closeDoor();
            Serial.println("안드로이드 문닫힘");
        }
    }
    // 파이에서 음성 인식 문 개폐 동작제어
    else if(strstr(topic, "sensors/door/mic/open")!=NULL){
        Serial.println("문 열었음");
        openDoor();
    }
    else if(strstr(topic, "sensors/door/mic/close")!=NULL){
        Serial.println("문 닫았음");
        closeDoor();
    }


    // if(strcmp("1", message)==0) {
    //     digitalWrite(13, HIGH);
    // } else {
    //     digitalWrite(13, LOW);
    // }
    // Serial.print(topic);
    // Serial.print(" : ");
    // Serial.println(message);
}

void reconnect() {
    while(!client.connected()) {
        Serial.print("Attempting MQTT connection....");

        if(client.connect("MotionEspClient")) {
            Serial.println("connected");
            
            // subscriber로 등록
            client.subscribe("sensors/door/#");
            Serial.println("구독등록완료");

        }
        else {
            Serial.print("failed, rc=");
            Serial.print(client.state());
            Serial.println("try again in 5 seconds");
            delay(5000);
        }
    }
}

//매개변수는 door state 값 0:닫힌상태 1:열린상태
void pub_doorState(int a) {

    Serial.println("문 상태 퍼블리시 들어옴");
    char message[100];
    dtostrf(a, 1, 1, message);
     //파이와 통신
    if(!client.connected()){
        reconnect();
    }
    if(a == 0){
        client.publish("sensors/door/state/close", message);
    }else if(a == 1){
        client.publish("sensors/door/state/open", message);
    }
    
    Serial.print("Door State: ");
    Serial.println(a);

}
// 문 열어주는 함수
void openDoor(){    
    // 어떤색 서보모터인지 알아내기
    Serial.println("문열어주는 서보모터 함수 IN");
    servoMotor1.attach(servoMotorPin1);
    
    servoMotor2.attach(servoMotorPin2);
    for(int angle=0;angle<180;angle++){
        
        servoMotor1.write(180-angle);
        servoMotor2.write(angle);
        delay(10);
    }


    servoMotor1.detach();
    servoMotor2.detach();

   
    pub_doorState(1);

}

// 문 닫아주는 함수
void closeDoor(){
    Serial.println("문닫어주는 서보모터 함수 IN");
    
    servoMotor1.attach(servoMotorPin1);
    servoMotor2.attach(servoMotorPin2);
    for(int angle=180;angle>0;angle--){
        servoMotor1.write(180-angle);
        servoMotor2.write(angle);
        delay(10);
        
    }
    servoMotor1.detach();
    servoMotor2.detach();
   
    pub_doorState(0);

}

int detectMotion(){
    int val = digitalRead(pir); //pir 모션센서로부터 입력값을 얻어옴 0:움직임없음 1:움직임감지
    Serial.println(val);
    return val;
}


void setup(){
    Serial.begin(9600);
    
    // 네트워크 통신
    wifi.init(ssid, password);
    mqtt_init();

   

    pinMode(pir,INPUT);
}

void loop(){
    // 파이와 통신
    if(!client.connected()){
        reconnect();
    }
    client.loop();
}