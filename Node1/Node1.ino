#include <HCSR04.h>
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <ArduinoJson.h>


const char* ssid = "JioFarm";
const char* password = "farmtheland";

UltraSonicDistanceSensor distanceSensor(D1, D2);  // Initialize sensor that uses digital pins 13 and 12.
boolean pumpStatus = false;
WiFiClient wClient;

StaticJsonBuffer<1000> jsonOutputBuffer;
StaticJsonBuffer<1000> jsonInputBuffer;


String ServerIP = "192.168.225.200";
String inputBuffer;
int ServerPort = 3212;
void setup () {
    pinMode(D0,OUTPUT);
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    WiFi.setAutoConnect(true);
    WiFi.setAutoReconnect(true);
    ArduinoOTA.setHostname("board1");
    ArduinoOTA.setPassword("thisboardofmine");


    ArduinoOTA.onStart([]() {
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH) {
      type = "sketch";
    } else { // U_SPIFFS
      type = "filesystem";
    }

    // NOTE: if updating SPIFFS this would be the place to unmount SPIFFS using SPIFFS.end()
    Serial.println("Start updating " + type);
  });
  ArduinoOTA.onEnd([]() {
    Serial.println("\nEnd");
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) {
      Serial.println("Auth Failed");
    } else if (error == OTA_BEGIN_ERROR) {
      Serial.println("Begin Failed");
    } else if (error == OTA_CONNECT_ERROR) {
      Serial.println("Connect Failed");
    } else if (error == OTA_RECEIVE_ERROR) {
      Serial.println("Receive Failed");
    } else if (error == OTA_END_ERROR) {
      Serial.println("End Failed");
    }
  });
  Serial.begin(9600);  // We initialize serial connection so that we could print values from sensor.

  ArduinoOTA.begin();
  Serial.println("Ready");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  wClient.connect(ServerIP,ServerPort);

}

int second = 0;
float temperature_value;
void loop () {
    ArduinoOTA.handle();

    JsonObject &root = jsonOutputBuffer.createObject();
    // // Every 500 miliseconds, do a measurement using the sensor and print the distance in centimeters.
    root["control-valve-raft-tank-1"] = int(pumpStatus);
    int distance = 80 - (distanceSensor.measureDistanceCm());

    root["sensor-water-level-buffer-tank-1"] = int(distance);


    if(pumpStatus)
    {
      digitalWrite(D0,LOW);
    }
    else
    {
      digitalWrite(D0,HIGH);
    }


   delay(100);
   while(wClient.available())
   {
    char c = wClient.read();
    if(c=='~')
    {
      Serial.println(inputBuffer);
      JsonObject &input_json = jsonInputBuffer.parse(inputBuffer);
      if(input_json.success())
      {
      input_json.prettyPrintTo(Serial);
      pumpStatus = input_json["control-valve-raft-tank-1"];
      Serial.println("Updating Pump Status to "+String(pumpStatus));
      }
      else
      {
        Serial.println("Unable to parse json");
      }
      inputBuffer = "";
      jsonInputBuffer.clear();
    }
    else
    {
      inputBuffer += c;
    }

   }
   if(!wClient.connected())
   {
     if (! wClient.connect(ServerIP,ServerPort))
     {
      Serial.println("connection failed to "+ServerIP);
     }
     delay(1000);
   }
   else
   {
     root.printTo(wClient);
     wClient.print("~");
   }
    second++;
    jsonOutputBuffer.clear();
}
