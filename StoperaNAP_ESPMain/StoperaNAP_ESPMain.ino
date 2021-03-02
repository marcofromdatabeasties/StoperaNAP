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
#include <CSV_Parser.h>
#include <dummy.h>
#include <HTTPClient.h>
#include "Keys.h"

#ifndef ST_SSID
#define ST_SSID "somenetwork"
#define PASSWORD "very_secret"
#endif

#define IJMUIDEN "http://waterinfo.rws.nl/api/Download/CSV?expertParameter=Waterhoogte___20Oppervlaktewater___20t.o.v.___20Normaal___20Amsterdams___20Peil___20in___20cm&locationSlug=IJmuiden-Buitenhaven(IJMH)&timehorizon=-1,0"

#define PUMP 23 //pomp GPIO23, om water bij te pompen
#define SOLENOID 22 //solenoid GPIO22, water weg te laten lopen.
#define WIFI_ON 21 //inet active led indicator
#define ERROR_ON 19 //error led indicator
#define PRESSURE 36 // FSR op ADC1_0, meet de hoeveelheid water in kolom.
#define MAX_PRES 4095 //max conversie waarde: 0-4095 bij 0.1-3.2 volt.


#define W1_LOW 0 // world 1: water in kolom te laag tov NAP/ water in column to low
#define W2_HIGH 1 // world 2: water in kolom te hoog tov NAP/water in column to high
#define W3_GOOD 2 // world 3: water in kolom goed tov NAP/water in column ok
#define W4_ERROR 3 // world 4: water in kolom veranderd niet / meting onjuist/ error world: water is not moving or measurement is off.
#define START 4 //world 5: starting (INet)
#define NOWHERE 5 //boot

//change on release
//set on site with real values RATIO becomes 1
#define C_HEIGHT_NAP 63.5f // 0.6 meter
#define C_R 3.75f //  cm radius
#define C_RATIO 0.254f // 1.5 meter / 5 meter
//((127 * 3.14 * 25) / 1000 = 9.9 kg
#define C_HEIGHT_MAX 127f // 1.27m
#define C_P_MAX 9.9f // 1.27cm equals 10kg

#define FLOW_IN 7 //liter per minute.
#define FLOW_OUT 5 //liter per minute.
// end change on release
//holds the state in the form of Kripke worlds
uint8_t volatile world = NOWHERE; // we start from nowhere
uint8_t volatile next_world = START;

//holds the pressure of the column
float volatile pressureNminus2;
float volatile pressureNminus1;
float volatile pressureCurrent;

//holds the presure the is respresented by the height of the seawaterlevel.
float pressureWanted;

SemaphoreHandle_t xSemaphore_world = NULL; //mutex for worldchanges
SemaphoreHandle_t xSemaphore_P = NULL; //mutex for new pressure values
SemaphoreHandle_t xSemaphore_INET = NULL; //mutex for connection status

//does http handling
HTTPClient http;

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

void setWorld(uint8_t worldNew) {
  if ( xSemaphore_world != NULL ) {
    /* See if we can obtain the semaphore.  If the semaphore is not
      available wait 10 ticks to see if it becomes free. */
    if ( xSemaphoreTake( xSemaphore_world, ( TickType_t ) 30 ) == pdTRUE ) {
      world = next_world;
      next_world = worldNew;
      xSemaphoreGive( xSemaphore_world );
    }
  }
}

void getSealevelHeightNAP(void * parameter) {
  // gets the sealevel and translates it into pressure of the column.
  while (true) {
    if ( xSemaphore_INET != NULL ) {
      if ( xSemaphoreTake( xSemaphore_INET, ( TickType_t ) 1000 / portTICK_PERIOD_MS ) == pdTRUE ) {
        if (WiFi.status() == WL_CONNECTED) {
          
          http.begin(IJMUIDEN); //URL waterlevel
          int httpCode = http.GET(); //Make the request
          //no longer needed to hold the inet-connection, we got what we need.
          xSemaphoreGive( xSemaphore_INET );
          
          if (httpCode == 200) {
            String payload = http.getString();
            //Datum;Tijd;Parameter;Locatie;Meting;Astronomisch getijden;Eenheid;Windrichting;Windrichting eenheid;Bemonsteringshoogte;Referentievlak;
            CSV_Parser cp(payload.c_str(), /*format*/ "ssssfdsdsss-",  /*has_header*/ true, /*delimiter*/ ';');
            //char **dates = (char**)cp["Datum"];
            //char **times = (char**)cp["Tijd"];
            //char **params = (char**)cp["Parameter"];
            //char **locs = (char**)cp["Locatie"];
            float **measurements = (float**)cp["Meting"];
            //int **astrs = (int**)cp["Astronomisch getijden"];
            //char **units = (char**)cp["Eenheid"];
            //int **dirs = (int**)cp["Windrichting eenheid"];
            //char **mheights = (char**)cp["Bemonsteringshoogte"];
            char **refs = (char**)cp["Referentievlak"];

            //start from the last row upwards, the file contains estimates based upon calculations (astronomical)
            for (int i = cp.getRowsCount() - 1; i >= 0; i++) {
              if (strcmp(refs[i], "NAP")) {
                float p = ((*measurements[i] * C_RATIO + C_HEIGHT_NAP) * 3.1415926f * pow(C_R, 2)) / 1000.0f; //h * pi * r² (volume cylinder) 1000cm³ = 1 kg = liter
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
          }
        }
      }
    }
    vTaskDelay(10 * 60000 / portTICK_PERIOD_MS); // wait 10 minutes (update frequency of seawaterlevel)
  }
}

//checks the level of the column against the wanted level and sets the worlds.
void determinWorld(void *parameter) {
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
          } else if (p_upper < pressureCurrent) {
            setWorld(W2_HIGH);
          } else {
            setWorld(W3_GOOD);
          }
        }
        xSemaphoreGive(xSemaphore_world);
      }
    }
    vTaskDelay(10 * 60000 / portTICK_PERIOD_MS); // wait a minute
  }
}


void testINETConnection(void * parameter) {
  while (true) {
    if ( xSemaphore_INET != NULL ) {
      if ( xSemaphoreTake( xSemaphore_INET, ( TickType_t ) 100 ) == pdTRUE ) {
        if (WiFi.status() == WL_CONNECTED) {
          digitalWrite(WIFI_ON, HIGH);
          vTaskDelay(120000 / portTICK_PERIOD_MS);
        } else {
          digitalWrite(WIFI_ON, LOW);
          setWorld(START);
        }
        xSemaphoreGive( xSemaphore_INET );
      }
    }
  }
}

void initiateINETConnection(void * parameter) {
  //start the WIFI and connect, for now (Ethernet later)
  digitalWrite(WIFI_ON, LOW);
  if ( xSemaphore_INET != NULL ) {
    if ( xSemaphoreTake( xSemaphore_INET, ( TickType_t ) 100 ) == pdTRUE ) {

      WiFi.begin(ST_SSID, PASSWORD);

      while (WiFi.status() != WL_CONNECTED) {
        vTaskDelay(500 / portTICK_PERIOD_MS);
      }
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
      vTaskDelay(round(minutes_flow * 1000) / portTICK_PERIOD_MS); // wait a period
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
      vTaskDelay(round(minutes_flow * 1000) / portTICK_PERIOD_MS); // wait a period
      digitalWrite(PUMP, LOW);
      xSemaphoreGive( xSemaphore_P );
    }
  }
  vTaskDelete(NULL); // done
}

void handleWorlds(void * parameter) {
  //handles the world changes and fires the corresponding tasks
  while (true) {
    if ( xSemaphore_world != NULL ) {
      if ( xSemaphoreTake( xSemaphore_world, ( TickType_t ) 100 ) == pdTRUE ) {
        if (world != next_world) {
          switch (next_world) {
            case W1_LOW:
              xTaskCreate(raiseWater,"raise", 1000, NULL, 1, NULL);
              break;
            case W2_HIGH:
              xTaskCreate(lowerWater, "lower", 1000, NULL, 1, NULL);
              break;
            case W3_GOOD:
              //where ok.
              break;
            case W4_ERROR:

              break;
            case START:
              xTaskCreate(initiateINETConnection, "iNet_Connection", 1000, NULL, 1, NULL);
              break;
            default:
              xSemaphoreGive( xSemaphore_world );
          }
        }
      }
    }
    vTaskDelay(120000 / portTICK_PERIOD_MS); // wait 2 minutes
  }
}

float map_f(float x, float in_min, float in_max, float out_min, float out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

void pressureReader(void* parameter) {
  while (true) {
    if ( xSemaphore_P != NULL) {
      if ( xSemaphoreTake( xSemaphore_P, ( TickType_t ) 60000 / portTICK_PERIOD_MS ) == pdTRUE ) {
        //read 12bit ADC > max 4095
        float p_now = map_f(float(analogRead(PRESSURE)), 0.0, 4095.0, 0.0, C_P_MAX);
        addNewPressureValue(p_now);
        xSemaphoreGive( xSemaphore_P );
      }
    }
    vTaskDelay(30000 / portTICK_PERIOD_MS); // wait 1/2 minute
  }
}


void setup() {
  pinMode(PUMP, OUTPUT);
  pinMode(SOLENOID, OUTPUT);
  pinMode(WIFI_ON, OUTPUT);

  digitalWrite(PUMP, LOW); // pump off
  digitalWrite(SOLENOID, HIGH); // solenoid closed, change on release
  digitalWrite(WIFI_ON, LOW); // INET off
  digitalWrite(ERROR_ON, LOW); // INET off

  xSemaphore_world = xSemaphoreCreateMutex();
  xSemaphore_P = xSemaphoreCreateMutex();
  xSemaphore_INET = xSemaphoreCreateMutex();

  //handles the worlds.
  xTaskCreate( handleWorlds, "Worlds", 1000, NULL, 1, NULL);
  //handels reading of current column height in kg.
  xTaskCreate(pressureReader, "Pressure", 1000, NULL, 1, NULL);
  //handles reading of waterlevel
  xTaskCreate(getSealevelHeightNAP, "Level", 1000, NULL, 1, NULL );
  //what is the world like today?
  xTaskCreate(determinWorld, "Worlds", 1000, NULL, 1, NULL);
}

void loop() {
  vTaskDelete(NULL); //cancel the loop, we use tasks
}
