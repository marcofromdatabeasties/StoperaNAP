

/**
   Programma dat aan de hand van de (deels) verwachte waterstanden boven NAP in het Stopera monument de juiste waarde laat zien.

   This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

*/
#include <WiFi.h>
#include <FirebaseJson.h>
#include <dummy.h>
#include <HTTPClient.h>
//File that includes the secrets
#include "Keys.h"

#define IJMUIDEN_alt "https://waterberichtgeving.rws.nl/wbviewer/maak_grafiek.php?loc=IJMH&set=metingen&nummer=12&format=csv"
#define IJMUIDEN "https://waterinfo.rws.nl/api/chart?mapType=waterhoogte&locationCode=IJmuiden-Buitenhaven(IJMH)&values=-1,0"

#ifndef LOGGING
#define LOGGING "<<some webhook tooling like ifttt url >>";
#endif

#define PUMP 23 //pomp GPIO23, om water bij te pompen
#define SOLENOID 22 //solenoid GPIO22, water weg te laten lopen.
#define WIFI_ON 2 //inet active led indicator, use onboard
#define PRESSURE 36 // FSR op ADC1_0, meet de hoeveelheid water in kolom.
#define MAX_PRES 4095 //max conversie waarde: 0-4095 bij 0.1-3.2 volt.


const static uint8_t W1_LOW = 0; // world 1: water in kolom te laag tov NAP/ water in column to low
const static uint8_t W2_HIGH = 1; // world 2: water in kolom te hoog tov NAP/water in column to high
const static uint8_t W3_GOOD = 2; // world 3: water in kolom goed tov NAP/water in column ok
const static uint8_t W4_ERROR = 3; // world 4: water in kolom veranderd niet / meting onjuist/ error world: water is not moving or measurement is off.
const static uint8_t START = 4; //world 5: starting (INet)
const static uint8_t NOWHERE = 5;//boot

//change on release
//set on site with real values RATIO becomes 1
#define C_HEIGHT_NAP 63.5f // 0.6 meter
#define C_R 3.75f //  cm radius
#define C_RATIO 0.254f // 1.5 meter / 5 meter
//((127 * 3.14 * 25) / 1000 = 9.9 kg
#define C_HEIGHT_MAX 127f // 1.27m
#define C_P_MAX 9.9f // 1.27cm equals 10k

#define FLOW_IN 7 //liter per minute.
#define FLOW_OUT 5 //liter per minute.
// end change on release
//holds the state in the form of Kripke worlds
uint8_t volatile world = NOWHERE; // we start from nowhere
uint8_t volatile next_world = START;

//holds the pressure of the column
float volatile pressureNminus2 = 0.1;
float volatile pressureNminus1 = 0.2;
float volatile pressureCurrent = 0.1;

//holds the presure the is respresented by the height of the seawaterlevel.
float pressureWanted = 0.0;

SemaphoreHandle_t xSemaphore_world = NULL; //mutex for worldchanges
SemaphoreHandle_t xSemaphore_P = NULL; //mutex for new pressure values
SemaphoreHandle_t xSemaphore_INET = NULL; //mutex for connection status
SemaphoreHandle_t xSemaphore_log = NULL; //mutex for logging

TaskHandle_t xHandlex_World;
TaskHandle_t xHandlex_Pressure;
TaskHandle_t xHandlex_HandleWorld;
TaskHandle_t xHandlex_Level;

void addNewPressureValue(float pressureNew) {
  if ( xSemaphore_P != NULL ) {
    /* See if we can obtain the semaphore.  If the semaphore is not
      available wait 30 ticks to see if it becomes free. */
    if ( xSemaphoreTake( xSemaphore_P, ( TickType_t ) 30 ) == pdTRUE ) {
      pressureNminus1 = pressureCurrent;
      pressureNminus2 = pressureNminus1;
      pressureCurrent = pressureNew;
      xSemaphoreGive( xSemaphore_P );
    }
  }
}

void checkErrorPressureValues(void *parameter) {
  if ( xSemaphore_P != NULL ) {
    /* See if we can obtain the semaphore.  If the semaphore is not
      available wait 30 ticks to see if it becomes free. */
    if ( xSemaphoreTake( xSemaphore_P, ( TickType_t ) 30 ) == pdTRUE ) {
      bool eror = pressureNminus1 == pressureCurrent &&
                  pressureNminus2 == pressureNminus1;
      xSemaphoreGive( xSemaphore_P );
      setWorld(W4_ERROR);
    }
  }
}

void setWorld(uint8_t worldNew) {
  if ( xSemaphore_world != NULL && worldNew != NULL) {
    /* See if we can obtain the semaphore.  If the semaphore is not
      available wait 10 ticks to see if it becomes free. */
    if ( xSemaphoreTake( xSemaphore_world, ( TickType_t ) 30 ) == pdTRUE ) {
      world = next_world;
      next_world = worldNew;
      xSemaphoreGive( xSemaphore_world );
    }
  }
}

//does the logging
void logger(void * what) {
  if ( xSemaphore_log != NULL) {
    if ( xSemaphoreTake( xSemaphore_log, ( TickType_t ) 1000 / portTICK_PERIOD_MS ) == pdTRUE ) {
      Serial.println(*((String*)what));
      xSemaphoreGive( xSemaphore_log );
    }
  }

  if ( xSemaphore_INET != NULL) {
    if ( xSemaphoreTake( xSemaphore_INET, ( TickType_t ) 10000 / portTICK_PERIOD_MS ) == pdTRUE ) {//10 second wait

      if (WiFi.status() == WL_CONNECTED) {
        // Domain name with URL path
        HTTPClient http;
        String serverPath = String(LOGGING) + String("?value1=") + urlencode(*((String*)what));
        http.begin(serverPath);

        int httpResponseCode = http.GET();

        http.end();
      }
      //no longer needed to hold the inet-connection and log, we got what we need.
      xSemaphoreGive( xSemaphore_INET );
    }
  }
  vTaskDelete(NULL); // done
}

void getSealevelHeightNAP(void * parameter) {
  // gets the sealevel and translates it into pressure of the column.
  static String l; //log
  while (true) {
    if ( xSemaphore_INET != NULL ) {
      if ( xSemaphoreTake( xSemaphore_INET, ( TickType_t ) 10000 / portTICK_PERIOD_MS ) == pdTRUE ) { //10 second wait
        if (WiFi.status() == WL_CONNECTED) {
          HTTPClient http;
          http.begin(IJMUIDEN); //URL waterlevel
          int httpCode = http.GET(); //Make the request

          //no longer needed to hold the inet-connection, we got what we need.
          xSemaphoreGive( xSemaphore_INET );

          l = "Received code" + httpCode;
          xTaskCreate(logger, "log4", 2000, &l , 1, NULL);

          if (httpCode == HTTP_CODE_OK) {
            String content = http.getString();
           
            FirebaseJson json;
            FirebaseJsonData jsonData;
            json.setJsonData(content);
            json.get(jsonData, "series/[0]/data");

            FirebaseJsonArray myArr;
            //Get the array data
            jsonData.getArray(myArr);

            String path = "[" + String(myArr.size() - 1) + "]/value";
            myArr.get(jsonData, path);
            float value = jsonData.floatValue;

            if (jsonData.success) {
              l = "Parse error";
              xTaskCreate(logger, "log4b", 3000, &l , 1, NULL);
            } else {

              l = "value" + String(value);
              xTaskCreate(logger, "log4", 3000, &l , 1, NULL);


              //p will be 0.0 when parsing failes atof(str) function used in lib.
              float p = ((value * C_RATIO + C_HEIGHT_NAP) * 3.1415926f * pow(C_R, 2)) / 1000.0f; //h * pi * r² (volume cylinder) 1000cm³ = 1 kg = liter

              float p_upper = p * 1.025f; //+2.5 % error
              float p_lower = p * 0.975f; //-2.5 % error

              boolean error = false;
              if ( xSemaphore_P != NULL) {
                if ( xSemaphoreTake( xSemaphore_P, ( TickType_t ) 1000 / portTICK_PERIOD_MS ) == pdTRUE ) {
                  pressureWanted = min(C_P_MAX, p);
                  //pressure is set, release semaphore
                  xSemaphoreGive(xSemaphore_P);
                }
              }
            }
          }

          http.end(); //free resources
        } else {
          //no longer needed to hold the inet-connection, we got what we need.
          xSemaphoreGive( xSemaphore_INET );
        }
      }
    }
    vTaskDelay(60000 / portTICK_PERIOD_MS); // wait 10/5 minutes (update frequency of seawaterlevel)
  }
}

//checks the level of the column against the wanted level and sets the worlds.
void determinWorld(void *parameter) {
  static String l;
  while (true) {
    if ( xSemaphore_world != NULL && xSemaphore_P != NULL) {
      if ( xSemaphoreTake( xSemaphore_world, ( TickType_t ) 1000 / portTICK_PERIOD_MS ) == pdTRUE ) {
        if ( xSemaphoreTake( xSemaphore_P, ( TickType_t ) 1000 / portTICK_PERIOD_MS ) == pdTRUE ) {
          float p_upper = pressureWanted * 1.025f; //+2.5 % error
          float p_lower = pressureWanted * 0.975f; //-2.5 % error
          //pressure is used, release semaphore
          xSemaphoreGive(xSemaphore_P);
          if (p_lower > pressureCurrent ) {
            setWorld(W1_LOW);
            l = "Column to low";

          } else if (p_upper < pressureCurrent) {
            setWorld(W2_HIGH);
            l = "Column to high";

          } else {
            setWorld(W3_GOOD);
            l = "Column ok";
          }
        }
        xSemaphoreGive(xSemaphore_world);
        xTaskCreate(logger, "log3", 3000, &l , 1, NULL);
      }
    }
    vTaskDelay(10 * 60000 / portTICK_PERIOD_MS); // wait 10 minutes
  }
}


void testINETConnection(void * parameter) {
  static String l;
  while (true) {
    if ( xSemaphore_INET != NULL ) {
      if ( xSemaphoreTake( xSemaphore_INET, ( TickType_t ) 100 ) == pdTRUE ) {
        if (WiFi.status() == WL_CONNECTED) {
          digitalWrite(WIFI_ON, HIGH);
          vTaskDelay(120000 / portTICK_PERIOD_MS); // 2 minutes
        } else {
          digitalWrite(WIFI_ON, LOW);
          setWorld(START);
          vTaskDelay(1000 / portTICK_PERIOD_MS); // 1 second
        }
        xSemaphoreGive( xSemaphore_INET );
      }
    }
  }
}

void initiateINETConnection(void * parameter) {
  //start the WIFI and connect, for now (Ethernet later)
  if ( xSemaphore_INET != NULL ) {
    if ( xSemaphoreTake( xSemaphore_INET, ( TickType_t ) 1000 / portTICK_PERIOD_MS ) == pdTRUE ) {

      Serial.print("Connecting to ");
      Serial.println(ST_SSID);

      WiFi.mode(WIFI_STA);
      WiFi.begin(ST_SSID, PASSWORD);
      WiFi.setHostname("Column1-NAP");
      vTaskDelay(3000 / portTICK_PERIOD_MS); // wait 5 seconds

      while (WiFi.status() != WL_CONNECTED) {
        Serial.print(".");
        vTaskDelay(500 / portTICK_PERIOD_MS);
      }
      Serial.print("IP: ");
      Serial.println(WiFi.localIP());
      xSemaphoreGive( xSemaphore_INET );

      digitalWrite(WIFI_ON, HIGH);
      setWorld(W3_GOOD);

    }
  }
  vTaskDelete(NULL); // done
}

//task to lower water in column (only task to do solenoid IO)
void lowerWater(void * parameter) {
  if ( xSemaphore_P != NULL ) {
    /* See if we can obtain the semaphore.  If the semaphore is not
      available wait 30 ticks to see if it becomes free. */
    if ( xSemaphoreTake( xSemaphore_P, ( TickType_t ) 30 ) == pdTRUE ) {
      float minutes_flow = min(1.0f, (pressureCurrent - pressureWanted) / FLOW_OUT);
      digitalWrite(SOLENOID, LOW);
      vTaskDelay(round(minutes_flow * 60000) / portTICK_PERIOD_MS); // wait a period
      digitalWrite(SOLENOID, HIGH);
      xSemaphoreGive( xSemaphore_P );
    }
  }
  vTaskDelete(NULL); // done
}

//task to raise water in column (only task to do pump IO)
void raiseWater(void * parameter) {
  if ( xSemaphore_P != NULL ) {
    /* See if we can obtain the semaphore.  If the semaphore is not
      available wait 30 ticks to see if it becomes free. */
    if ( xSemaphoreTake( xSemaphore_P, ( TickType_t ) 30 ) == pdTRUE ) {
      float minutes_flow = min(1.0f, (pressureWanted - pressureCurrent) / FLOW_IN);
      digitalWrite(PUMP, HIGH);
      vTaskDelay(round(minutes_flow * 60000) / portTICK_PERIOD_MS); // wait a period
      digitalWrite(PUMP, LOW);
      xSemaphoreGive( xSemaphore_P );
    }
  }
  vTaskDelete(NULL); // done
}

void handleWorlds(void * parameter) {
  //handles the world changes and fires the corresponding tasks
  static String l; //logging
  while (true) {
    if ( xSemaphore_world != NULL ) {
      if ( xSemaphoreTake( xSemaphore_world, ( TickType_t ) 100 ) == pdTRUE ) {
        if (world != next_world) {
          l = "World has changed to " + String(next_world) + " from " + String(world);
          xTaskCreate(logger, "log2", 2000, &l , 1, NULL);
          switch (next_world) {
            case W1_LOW:
              xTaskCreate(raiseWater, "raise", 1000, NULL, 1, NULL);
              break;
            case W2_HIGH:
              xTaskCreate(lowerWater, "lower", 1000, NULL, 1, NULL);
              break;
            case W3_GOOD:
              //where ok.
              break;
            case W4_ERROR:
              //stops the worlds
              vTaskDelete(xHandlex_World);
              vTaskDelete(xHandlex_Pressure);
              vTaskDelete(xHandlex_HandleWorld);
              vTaskDelete(xHandlex_Level);
              WiFi.disconnect();
              break;
            case START:
              xTaskCreate(initiateINETConnection, "iNet_Connection", 10000, NULL, 1, NULL);
              break;
            default:
              break;
          }
        }
        xSemaphoreGive( xSemaphore_world );
      }
    }
    vTaskDelay(120000 / portTICK_PERIOD_MS); // wait 2 minutes
  }
}

void pressureReader(void* parameter) {
  static String l;
  while (true) {
    if ( xSemaphore_P != NULL) {
      if ( xSemaphoreTake( xSemaphore_P, ( TickType_t ) 60000 / portTICK_PERIOD_MS ) == pdTRUE ) {
        //read 12bit ADC > max 4095
        float p_now = map_f(float(analogRead(PRESSURE)), 0.0, 4095.0, 0.0, C_P_MAX);
        l = "Pressure read" + String(p_now);
        xTaskCreate(logger, "log1", 2000, &l , 1, NULL);
        xSemaphoreGive( xSemaphore_P );
        addNewPressureValue(p_now);
      }
    }
    vTaskDelay(30000 / portTICK_PERIOD_MS); // wait 1/2 minute
  }
}


float map_f(float x, float in_min, float in_max, float out_min, float out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

String urlencode(String str)
{
  str.replace(".", "_");
  str.replace(" ", "_");

  return str;

}

void setup() {
  Serial.begin(115200);

  pinMode(PUMP, OUTPUT);
  pinMode(SOLENOID, OUTPUT);
  pinMode(WIFI_ON, OUTPUT);

  digitalWrite(PUMP, LOW); // pump off
  digitalWrite(SOLENOID, HIGH); // solenoid closed, change on release
  digitalWrite(WIFI_ON, LOW); // INET off

  xSemaphore_world = xSemaphoreCreateMutex();
  xSemaphore_P = xSemaphoreCreateMutex();
  xSemaphore_INET = xSemaphoreCreateMutex();
  xSemaphore_log = xSemaphoreCreateMutex();

  Serial.println("Starting tasks");

  //handles the worlds.
  xTaskCreate( handleWorlds, "Worlds", 10000, NULL, 1, &xHandlex_World);
  //handels reading of current column height in kg.
  xTaskCreate(pressureReader, "Pressure", 1000, NULL, 1, &xHandlex_Pressure);
  //handles reading of waterlevel
  xTaskCreate(getSealevelHeightNAP, "Level", 10000, NULL, 1, &xHandlex_Level);
  //what is the world like today?
  xTaskCreate(determinWorld, "DetWorlds", 3000, NULL, 1, &xHandlex_HandleWorld);

  //needs INET check

}

void loop() {
  vTaskDelete(NULL); //cancel the loop, we use tasks
}
