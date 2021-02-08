* Title: System for COVID-19 prevention in closed spaces by access control and CO2 monitoring                *
 *                                                                                                            *
 * Authors: Pablo Rodríguez Martín & Daniel García Portero                                                    *
 *                                                                                                            *
 * Date: February 11th, 2021                                                                                  *
 *                                                                                                            * 
 * Version:. 1.0                                                                                              *   
 *                                                                                                            *
 * Type: Arduino code for ESP32                                                                               *
 *                                                                                                            * 
 * Availability: https://github.com/paroma96/COVID-19-prevention-by-access-control-and-CO2-monitoring/import  *
 *                                                                                                            *  
 **************************************************************************************************************
 **************************************************************************************************************/ 

#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include "MQUnifiedsensor.h"

#define SS_PIN 21
#define RST_PIN 22
#define CO2_PIN 34
#define LED_GRANTED 2
#define LED_DENIED 4

const char* ssid = "<YOUR_WIFI_SSID>";  // WiFi SSID
const char* password = "<YOUR_WIFI_PASS>";  // WiFi password
const uint16_t port_Access = 8085;  // TCP/IP access server
const uint16_t port_CO2 = 8084;  // UDP/IP access server
char ch;

IPAddress ipRaspaddr(192,168,1,132);  // Raspberry Pi 3B+ IP address
MFRC522 mfrc522(SS_PIN, RST_PIN); // Instance of the class
WiFiUDP udp;
MQUnifiedsensor co2Sensor("ESP32", 3.3, 12, CO2_PIN, "MQ-135");  // 3.3V and 12 bits for ADC's resolution


/************** SETUP ******************/
void setup() {
   Serial.begin(9600);
   SPI.begin();  // Initializing SPI bus
   mfrc522.PCD_Init(); // Initializing MFRC522 RFID module
   Serial.println("Calibrating CO2 sensor");
   co2Sensor.setRegressionMethod(1); // 1-Exponential, 2-Linear
   co2Sensor.setA(110.47);
   co2Sensor.setB(-2.862); // Values for CO2: ppm=a*ADC_level^b=110.47*ADC_level^(-2.862) -> https://github.com/miguel5612/MQSensorsLib/blob/master/examples/MQ-135-ALL/MQ-135-ALL.ino
   co2Sensor.setRL(1);  // 1kOhm load NECESSARY TO EVALUATE ON BOARD -> https://roboticafacil.es/prod/sensor-gas/
   // FIRST R0 CALIBRATION BEFORE USE. PREHEATING IS NEEDED. CONNECT, WAIT AND THEN RESET AFTER A WHILE. THEN SET R0 AND COMMENT THIS LOOP
   float calcR0 = 0;
   for(int i=1;i<=10;i++){
      co2Sensor.update();
      calcR0 += co2Sensor.calibrate(3.6); // 400ppm as ratio MQ-135 in clean air -> https://www.olimex.com/Products/Components/Sensors/Gas/SNS-MQ135/resources/SNS-MQ135.pdf
   }
   co2Sensor.setR0(calcR0/10);  
   co2Sensor.setR0(18); // R0 = 18kOhm MEASURED WITH OPEN CLEAN AIR - Oscillating between 16kOhm and 20kOhm
   Serial.print("R0 = ");
   Serial.print(co2Sensor.getR0());
   Serial.println(" kOhm");
   co2Sensor.init();
   Serial.println("Calibration done!");
   pinMode(LED_GRANTED, OUTPUT);
   pinMode(LED_DENIED, OUTPUT);
   Serial.print("Connecting to ");
   Serial.print(ssid);
   WiFi.mode(WIFI_STA);
   WiFi.begin(ssid, password);  // Initializing connection with WiFi
   while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
   }
   Serial.println("");
   Serial.println("CONNECTED!");
   Serial.print("IP: ");
   Serial.println(WiFi.localIP());  // Gets its IP address
   Serial.println("READY\n");
   udp.begin(666); // Random listen port, we don´t use it anymore
}


/************** LOOP ******************/
void loop() {
  int counter = 0;
  int valueCO2 = 0;
  WiFiClient client;
  while(!client.connected()){ // In case it is disconnected from database, tries with another attempt. RFID will be not functional until it is possible to check database
    Serial.print("CONNECTING TO DATABASE");
    for(int i = 0; i < 3; i++){
      delay(700);
      Serial.print(".");
    }
    Serial.println("");
    client.connect(ipRaspaddr,port_Access);  // Attempt of connecting
    if(client.connected())
      Serial.println("DONE\n");
  }
  while(client.connected()){  // In case it is already connected with database          
    if(mfrc522.PICC_IsNewCardPresent()){  // For not checking the same approximated card for more than once
      if(mfrc522.PICC_ReadCardSerial()){  // For checking possibility of obtaining card's UID
        String content = getUID();  // User ID to be sent to the RPi
        Serial.println(content);
        String result = checkUID(client, content);
        decissionUID(result);
      }
    }else{
      delay(100); // Checks every 0.5 second(s)
      if(counter>50){ // READING PERIOD: 5 SECONDS
        valueCO2 = 0;
        for(int i = 0; i < 10; i++){ // Avoids big fluctuations
          co2Sensor.update();
          valueCO2 = valueCO2 + co2Sensor.readSensor();
          delay(50);
        }
        valueCO2 = valueCO2/10;
        Serial.print("CO2 concentration: ");
        //Serial.print(valueCO2);
        Serial.print(valueCO2+400);  // 400ppm minimum
        Serial.println(" ppm");
        counter = 0;
        if(valueCO2 > 600){
          Serial.println("WARNING: HIGH CO2 CONCENTRATION DETECTED");
          if(valueCO2 > 800){
            Serial.println("ALERT: DANGER CO2 LEVEL ZONE");
            if(valueCO2 > 1000){
              Serial.println("ALERT: EXCEEDED SAFE CONCENTRATION! DO VENTILATE!");
              if(valueCO2 > 2000){
              Serial.println("DANGER: TOO HIGH CO2 LEVEL");
              }
            }
          }
        }
        sendCO2value(valueCO2+400);
      }else
        counter = counter + 1;
    }
  }
}

/**
 * OBTAINS THE ID FROM THE USER CARD IN HEXADECIMAL
 * NUMBERS, THEN RETURNS VALUE.
 */
String getUID(){
  Serial.print("User ID:");
  String content= "";  // User ID to be sent to the RPi
  for(byte i = 0; i < mfrc522.uid.size; i++) {
    Serial.print(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " ");
    Serial.print(mfrc522.uid.uidByte[i], HEX);
    content.concat(String(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " "));
    content.concat(String(mfrc522.uid.uidByte[i], HEX)); // Final hexadecimal User ID to be checked
  }
  Serial.println();
  mfrc522.PICC_HaltA();
  return content;
}

/* 
 * SENDS THE STRING WITH USER ID CODE AND WAITS UNTIL 
 * RECEIVING A RESPONSE FROM SERVER (TCP/IP Tx). THEN RETURNS IT.
 */
String checkUID(WiFiClient client, String content){
  Serial.println("CHECKING USER ID");
  content.toUpperCase();
  client.print(content.substring(1));  // UID sent to database server
  delay(1000);  // Gives 1 second to allow computation on server and communication to execute
  String result;
  while(client.available()>0) {
    ch = static_cast<char>(client.read());  // Reading the response character by character
    result.concat(ch);
  }
  return result;
}

/*
 * CHECKS IF USER HAS GOT PERMISSION FOR ENTERING,
 * IN CASE IT DOES, ACCESS WILL BE PERMITTED (TCP/IP Rx).
 */
void decissionUID(String result){
  // In case the card is authorized
  if(result == "Granted"){
    Serial.println("AUTHORIZED ACCESS");
    digitalWrite(LED_GRANTED , HIGH);
    delay(300);
    digitalWrite(LED_GRANTED , LOW);
    delay(200);
    Serial.println(""); 
  // In case the card is NOT authorized
  }else{
    Serial.println("ACCESS DENIED");
    digitalWrite(LED_DENIED , HIGH);
    delay(300);
    digitalWrite(LED_DENIED , LOW);
    delay(200);
    Serial.println(""); 
  }
}

/*
 * SENDS CO2 LEVEL TO SERVER VIA UDP/IP.
 */
void sendCO2value(int valueCO2){
  udp.beginPacket("192.168.1.132", port_CO2);
  udp.print(valueCO2); // CO2 value sent to database server
  udp.endPacket();
  delay(1000);  // Gives 1 second to allow computation on server and communication to execute
}
  
