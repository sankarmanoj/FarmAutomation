#include <HCSR04.h>


UltraSonicDistanceSensor distanceSensor(D0, D1);  // Initialize sensor that uses digital pins 13 and 12.
boolean pumpStatus = false;
void setup () {
    Serial.begin(9600);  // We initialize serial connection so that we could print values from sensor.
    pinMode(D2,OUTPUT);
}

int second = 0;

void loop () {
    // Every 500 miliseconds, do a measurement using the sensor and print the distance in centimeters.
    int distance = (distanceSensor.measureDistanceCm());
    Serial.print(distance);
    Serial.print(" Pump is ");
    if(pumpStatus)
    {
      Serial.println("ON");
    }
    else
    {
      Serial.println("OFF");
    }
    if(second<180)
    {
      pumpStatus = true;  
    }
    else if(second<1980)
    {
      pumpStatus = false;
    }
    else
    {
      second = 0;
    }
    if(distance < 80 || distance > 100)
    {
      pumpStatus = false;
    }
    if(pumpStatus)
    {
      digitalWrite(D2,HIGH);
    }
    else
    {
      digitalWrite(D2,LOW);
    }
    delay(1000);
    second++;

}
