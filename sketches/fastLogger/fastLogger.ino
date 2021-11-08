/*********************************************************************
 *  
 *  Data Logger for the course "Laboratorio di Elettronica (MFN0580)"
 *  Corso di Laurea in Fisica - Universita` di Torino
 *  
 *  Logger based on Adafuit 254 shield
 *  https://www.adafruit.com/product/254
 *  
 *  Author: Michele Risino 
 *  Dipartimento di Fisica - Universita` di Torino
 *  Created: 2021.06.15
 *  
 ************************************************************************/
#include <SPI.h>
#include <SD.h>

const String VERSION = " v1.1"; // current version 

const int TRIGGER_PIN = 6; //pin connected to shift register Q_F to trigger acquisition events
const int TOGGLE_PIN = 7;  //pin connected to the "toggle acquisition" button (active HIGH)
const int CD_PIN = 8;      //pin that is low when the card is disconnected
const int CS_PIN = 10;     //sd card stuff
const double MICROS_TO_S = 0.000001;

int fileCount;            //number to print in filename of next acquisition/
unsigned long activeTime; //timestamp of beginning of acquisition
bool sdInitOk;            //true if sd card is detected with no errors
bool active = false;      //true while acquiring data
File dataFile;            //handle to open and write files on the sd card

void setup() {
  //print sketch name and version 
  Serial.begin(9600);
  if (Serial) Serial.println( __FILE__ + VERSION );
  //SD card stuff
  checkSDCard();
}


void checkSDCard(){
  //check good wiring and SD card presence
  sdInitOk = SD.begin(CS_PIN);
 //move fileCount to next available number
  if (sdInitOk)
  {
    fileCount = 1;
    while (SD.exists("data" + String(fileCount) + ".txt")) fileCount++;
  }
}

void acquireData()
{
  //wait for trigger to rise: trigger must be high and it must have been low on the previous check for it to avoid multiple reading of the same data
  int trigger = digitalRead(TRIGGER_PIN);
  int oldTrigger = HIGH;
  while (oldTrigger == HIGH || trigger == LOW)
  {
    oldTrigger = trigger;
    trigger = digitalRead(TRIGGER_PIN);
  }

  //acquire data from pins 2 to 5, shifting bits to form an integer
  int code = 0; //maybe byte?
  for (int dataPin = 2; dataPin <= 5; dataPin++) {
    int dataBit = digitalRead(dataPin);
    code = (code << 1) + dataBit;
  }
  
  //get a timestamp of the acquisition event relative to beginning of acquisition, in seconds.
  //rawTimestamp's calculation works even if micros() overflowed because of unsigned arithmetic,
  //but it becomes wrong after 70 minutes of an individual acquisition
  unsigned long rawTimestamp = micros() - activeTime;
  double timestamp = rawTimestamp * MICROS_TO_S;
  
  //write to the sd card. If the card is unavailable, halt
  String dataString = String(timestamp, 6) + "," + String(code);
  if (dataFile) dataFile.println(dataString);
  else while (1); //executes once
}

//toggle the active flag when the "toggle acquisition" button is pressed and released.
//when passing to active mode a new file is open and activeTime is set. When passing to inactive, changes to the previous file are saved
void checkToggle()
{
  static bool triggered = false;
  if (triggered)
  {
    if (digitalRead(TOGGLE_PIN) == LOW)
    {
      triggered = false;
      active = !active;
      if (active)
      {
        dataFile = SD.open("data" + String(fileCount++) + ".txt", FILE_WRITE);
        activeTime = micros();
      }
      else dataFile.close();
    }
  }
  else if (digitalRead(TOGGLE_PIN) == HIGH) triggered = true;
}

void loop() {
  while (!sdInitOk) checkSDCard(); //look for the sd card until it is found
  if (active) acquireData();
  checkToggle(); //always check if the toggle button has been pressed
  if (digitalRead(CD_PIN) == LOW) sdInitOk = false; //if the card has been disconnected, revert to attempting setup
}
