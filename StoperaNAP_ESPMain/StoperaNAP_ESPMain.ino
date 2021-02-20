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

#define PUMP 23 //pomp GPIO23, om water bij te pompen
#define SOLENOID 22 //solenoid GPIO22, water weg te laten lopen.
#define WIFI_ON 21 //inet active led indicator
#define ERROR_ON 19 //error led indicator
#define PRESSURE 36 // FSR op ADC1_0, meet de hoeveelheid water in kolom.
#define MAX_PRES 4095 //max conversie waarde: 0-4095 bij 0.1-3.2 volt.

#define W1_LAAG 0 // world 1: water in kolom te laag tov NAP/ water in column to low
#define W2_HOOG 1 // world 2: water in kolom te hoog tov NAP/water in column to high
#define W3_GOOD 2 // world 3: water in kolom goed tov NAP/water in column ok
#define W4_ERROR 3 // world 4: water in kolom veranderd niet / meting onjuist/ error world: water is not moving or measurement is off.
#define START 4 //world 5: starting (INet)
#define NOWHERE 5 //boot

//set on site with real values RATIO becomes 1
#define C_HEIGHT_NAP 40.0f // 0.4 meter
#define C_R 0.2f // 5 cm radius
#define C_RATIO 0.24f // 1.2 meter / 5 meter

#define FLOW_IN 7 //liter per minute.
#define FLOW_OUT 5 //liter per minute.

uint8_t volatile world = NOWHERE; // we start from nowhere
uint8_t volatile next_world = START;

float volatile pressureNminus2;
float volatile pressureNminus1;
float volatile pressureCurrent;

SemaphoreHandle_t xSemaphore_world = NULL; //mutex for worldchanges
SemaphoreHandle_t xSemaphore_P = NULL; //mutex for new pressure values
SemaphoreHandle_t xSemaphore_INET = NULL; //mutex for connection status

HTTPClient http;

bool addNewPressureValue(float pressureNew) {
  if ( xSemaphore_P != NULL ) {
    /* See if we can obtain the semaphore.  If the semaphore is not
      available wait 10 ticks to see if it becomes free. */
    if ( xSemaphoreTake( xSemaphore_P, ( TickType_t ) 30 ) == pdTRUE ) {
      pressureNminus1 = pressureCurrent;
      pressureNminus2 = pressureNminus1;
      pressureCurrent = pressureNew;
      xSemaphoreGive( xSemaphore_P );
    }
    return true;

  } else {
    return false; //error setup not completed.
  }
}

void getSealevelHeightNAP(void * parameter) {
  // gets the sealevel and translates it into pressure of the column.
  if ( xSemaphore_INET != NULL ) {
    if ( xSemaphoreTake( xSemaphore_INET, ( TickType_t ) 1000 / portTICK_PERIOD_MS ) == pdTRUE ) {
      if (WiFi.status() == WL_CONNECTED) {
        http.begin("http://waterinfo.rws.nl/api/Download/CSV?expertParameter=Waterhoogte___20Oppervlaktewater___20t.o.v.___20Normaal___20Amsterdams___20Peil___20in___20cm&locationSlug=IJmuiden-Buitenhaven(IJMH)&timehorizon=-1,0"); //URL waterlevel
        int httpCode = http.GET(); //Make the request
        if (httpCode == 200) {
          String payload = http.getString();
          //no longer needed to hold the inet-connection, we got what we need. 
          xSemaphoreGive( xSemaphore_INET );
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
          for (int i = cp.getRowsCount()-1; i >= 0; i++) {
            if (strcmp(refs[i],"NAP")) {
               float p = ((*measurements[i] * C_RATIO + C_HEIGHT_NAP)* 3.1415926f * pow(C_R, 2)) / 1000.0f; //h * pi * r² (volume cylinder) 1000cm³ = 1 kg = liter
               //((40 + (88 * .24) * 3.14 * 0,2²) / 1000 = .019
               addNewPressureValue(p);  
            }
          }
        }
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
      if ( xSemaphore_world != NULL ) {
        if ( xSemaphoreTake( xSemaphore_world, ( TickType_t ) 100 ) == pdTRUE ) {
          world = W3_GOOD;
          xSemaphoreGive( xSemaphore_world );
        }
      }
    }
  }
  vTaskDelete(NULL); // done
}

void handleWorlds(void * parameter) {
  //handles the world changes and fires the corresponding tasks
  for ( ;; ) {
    if ( xSemaphore_world != NULL ) {
      if ( xSemaphoreTake( xSemaphore_world, ( TickType_t ) 100 ) == pdTRUE ) {
        //check the inet connection
        if ( xSemaphore_INET != NULL ) {
          if ( xSemaphoreTake( xSemaphore_INET, ( TickType_t ) 1000 / portTICK_PERIOD_MS ) == pdTRUE ) {
            //we could be getting the sealevel at this point, so wait a little longer.
            if (WiFi.status() != WL_CONNECTED) {
              next_world = START;
            }
            xSemaphoreGive( xSemaphore_INET );
          }
        }

        if (world != next_world) {
          switch (next_world) {
            case W1_LAAG:

              break;
            case W2_HOOG:

              break;
            case W3_GOOD:

              break;
            case W4_ERROR:

              break;
            case START:
              xTaskCreate(
                initiateINETConnection,
                "iNet_Connection",
                1000,
                NULL,
                1,
                NULL            // Task handle
              );

              break;
            default:
              xSemaphoreGive( xSemaphore_world );
          }
        }
      }
    }
    vTaskDelay(1000 / portTICK_PERIOD_MS); // wait a second
  }
}


void setup() {
  pinMode(PUMP, OUTPUT);
  pinMode(SOLENOID, OUTPUT);
  pinMode(WIFI_ON, OUTPUT);

  digitalWrite(PUMP, LOW); // pump off
  digitalWrite(SOLENOID, LOW); // solenoid closed
  digitalWrite(WIFI_ON, LOW); // INET off
  digitalWrite(ERROR_ON, LOW); // INET off

  xSemaphore_world = xSemaphoreCreateMutex();
  xSemaphore_P = xSemaphoreCreateMutex();
  xSemaphore_INET = xSemaphoreCreateMutex();

  xTaskCreate(
    handleWorlds,
    "Worlds",
    1000,
    NULL,
    1,
    NULL
  );
}

void loop() {
  vTaskDelete(NULL); //cancel the loop, we use tasks
}
