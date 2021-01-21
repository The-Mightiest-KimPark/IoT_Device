// 1분마다 서버로 온습도와 불꽃감지 정보를 보내주는 프로그램

#include <WiFiEsp.h>
#include <SoftwareSerial.h>
#include <PubSubClient.h>
#include <Arduino.h>
#include <WifiUtil.h>
#include <DHT.h>
#include <MiniCom.h>

#define DHTPIN 2 //DHT핀을 2번으로 정의한다 (DATA핀)
#define DHTTYPE DHT11 //DHT타입을 DHT11로 정의한다
#define FLAMEPIN 5 //불꽃감지센서 데이터핀

DHT dht11(DHTPIN, DHTTYPE); //DHT설정-dht(디지털2, dht11)

MiniCom com;
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
// const char mqtt_server[] = "172.30.1.52";

//통신 설정
SoftwareSerial SoftwareSerial(11, 12);
WifiUtil wifi(11, 12);

// MQTT용 WIFI 클라이언트 객체 초기화
WiFiEspClient espClient;
PubSubClient client(espClient);


// mqtt 통신 관련 함수
void mqtt_init() {
    
    client.setServer(mqtt_server, 1883);

}

void reconnect() {
    while(!client.connected()) {
        Serial.print("Attempting MQTT connection....");

        if(client.connect("MotionEspClient")) {
            Serial.println("connected");
            
            // subscriber로 등록
            // client.subscribe("sensors/door/#");

        }
        else {
            Serial.print("failed, rc=");
            Serial.print(client.state());
            Serial.println("try again in 5 seconds");
            delay(5000);
        }


    }
}

void publish(float h, float t, int f){

    char humi[100];
    char temp[100];
    char flame[100];

    dtostrf(h, 3, 1, humi);
    dtostrf(t, 4, 3, temp);
    dtostrf(f, 1, 1, flame);

    client.publish("sensors/humi", humi);
    client.publish("sensors/temp", temp);
    client.publish("sensors/flame", flame);

}



// 온, 습도, 불꽃 감지 측정 함수
void checkValue(){
    Serial.println("함수안에 들어오나요?");
    float h = dht11.readHumidity();//변수 h에 습도값을 저장
    float t = dht11.readTemperature();//변수 t에 온도값을 저장
    int f = analogRead(A1); //불꽃 감지 센서 A1핀 설정

    Serial.print("습도 : ");
    Serial.print(h);
    Serial.print("온도 : ");
    Serial.print(t);
    Serial.print("불꽃 : ");
    Serial.print(f);


    
     publish(h,t,f);
}


void setup(){
    Serial.begin(9600);
    
    wifi.init(ssid, password);
    mqtt_init();
    
    dht11.begin();
    pinMode(FLAMEPIN,INPUT);
    
    

}
void loop(){
    
    // 파이와 통신
    if(!client.connected()){
        reconnect();
    }
    client.loop();
    checkValue();
    delay(10000);
}