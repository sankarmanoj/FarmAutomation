#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <ArduinoJson.h>
#define PIN_VALVE_LOW D2
#define PIN_VALVE_HIGH D7

const char* ssid = "JioFarm";
const char* password = "farmtheland";

WiFiClient wClient;

StaticJsonBuffer<1000> jsonOutputBuffer;
StaticJsonBuffer<1000> jsonInputBuffer;


String ServerIP = "192.168.225.200";
String inputBuffer;
int ServerPort = 3212;
void setup () {
  Serial.begin(9600);  // We initialize serial connection so that we could print values from sensor.
  pinMode(D6,OUTPUT);
  pinMode(PIN_VALVE_LOW,INPUT_PULLUP);
  pinMode(PIN_VALVE_HIGH,INPUT_PULLUP);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
//  IPAddress ip(192,168,225,102);   
//  IPAddress gateway(192,168,225,1);   
//  IPAddress subnet(255,255,255,0);  
  WiFi.setAutoConnect(true);
  WiFi.setAutoReconnect(true);
  ArduinoOTA.setHostname("board5");
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
  ArduinoOTA.begin();
  Serial.println("Ready");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  wClient.connect(ServerIP,ServerPort);

}

int second = 0;
float temperature_value;
boolean valve_status;
void loop () {
  ArduinoOTA.handle();

  JsonObject &root = jsonOutputBuffer.createObject();

  int low_switch_status = digitalRead(PIN_VALVE_LOW);
  int high_switch_status = digitalRead(PIN_VALVE_HIGH);
  root["sensor-level-switch-low-tank-2"] = low_switch_status;
  root["sensor-level-switch-high-tank-2"] = high_switch_status;
  root["control-valve-raft-tank-2"] = int(valve_status);

  if(valve_status)
  {
    digitalWrite(D6,HIGH);
  }
  else
  {
    digitalWrite(D6,LOW);
  }
  Serial.println("Tank 2 - Valve = "+String(valve_status));
  Serial.println("Tank 2 - Switch Status Low = "+String(low_switch_status));
  Serial.println("Tank 2 - Switch Status High = "+String(high_switch_status));
  delay(150);
  while(wClient.available())
  {
    char c = wClient.read();
    if(c=='~')
    {
      // Serial.println(inputBuffer);
      JsonObject &input_json = jsonInputBuffer.parse(inputBuffer);
      if(input_json.success())
      {
        valve_status = input_json["control-valve-raft-tank-2"];
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
