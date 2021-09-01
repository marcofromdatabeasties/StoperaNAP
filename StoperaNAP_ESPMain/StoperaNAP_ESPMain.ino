

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
//File that includes the secrets
//#include "Keys.h"


#ifndef LOGGING
#define LOGGING "<<some webhook tooling like ifttt url >>";
#endif

//defining the modem
#define SerialAT Serial2
#define TINY_GSM_MODEM_A6

#if !defined(TINY_GSM_RX_BUFFER)
#define TINY_GSM_RX_BUFFER 1024
#endif

#define TINY_GSM_DEBUG Serial
#define TINY_GSM_USE_GPRS true

const char apn[]      = "internet";
const char gprsUser[] = "";
const char gprsPass[] = "";
#define GSM_PIN "0000"

#include <TinyGsmClient.h>

#define TINY_GSM_USE_GPRS true

#ifdef DUMP_AT_COMMANDS
#include <StreamDebugger.h>
StreamDebugger debugger(SerialAT, SerialMon);
TinyGsm        modem(debugger);
#else
TinyGsm        modem(SerialAT);
#endif

TinyGsmClient  client(modem);

//define ports
#define PUMP 23 //pomp GPIO23, om water bij te pompen
#define SOLENOID 22 //solenoid GPIO22, water weg te laten lopen.
#define WIFI_ON 2 //inet active led indicator, use onboard
#define PRESSURE 36 // FSR op ADC1_0, meet de hoeveelheid water in kolom.
#define MAX_PRES 4095 //max conversie waarde: 0-4095 bij 0.1-3.2 volt.

//define worlds
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

#define LEVEL_SERVER naplevel-tifcbsrqva-ez.a.run.app
#define LEVEL_RESOURCE /api/v1/sdkflj432l324ljkhk234jjl/waterlevel/


SemaphoreHandle_t xSemaphore_INET = NULL; //mutex for connection status
SemaphoreHandle_t xSemaphore_log = NULL; //mutex for logging

//does the logging
void logger(void * what) {
  if ( xSemaphore_log != NULL) {
    if ( xSemaphoreTake( xSemaphore_log, ( TickType_t ) 1000 / portTICK_PERIOD_MS ) == pdTRUE ) {
      Serial.println(*((String*)what));
      xSemaphoreGive( xSemaphore_log );
    }
  }
  vTaskDelete(NULL); // done
}

float map_f(float x, float in_min, float in_max, float out_min, float out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

class Column_t {
  public:
    Column_t(const char* cde) {
      code = String(*cde);
      xSemaphore_world = xSemaphoreCreateMutex();
      xSemaphore_P = xSemaphoreCreateMutex();
    }

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
      if ( xSemaphore_world != NULL) {
        /* See if we can obtain the semaphore.  If the semaphore is not
          available wait 10 ticks to see if it becomes free. */
        if ( xSemaphoreTake( xSemaphore_world, ( TickType_t ) 30 ) == pdTRUE ) {
          world = next_world;
          next_world = worldNew;
          xSemaphoreGive( xSemaphore_world );
        }
      }
    }


    uint8_t volatile world = NOWHERE; // we start from nowhere
    uint8_t volatile next_world = START;

    //holds the pressure of the column
    float volatile pressureNminus2 = 0.1;
    float volatile pressureNminus1 = 0.2;
    float volatile pressureCurrent = 0.1;

    float volatile pressureWanted = 0.0;

    SemaphoreHandle_t xSemaphore_world = NULL; //mutex for worldchanges
    SemaphoreHandle_t xSemaphore_P = NULL; //mutex for new pressure values
    
    TaskHandle_t *xHandlex_World;
    TaskHandle_t *xHandlex_Pressure;
    TaskHandle_t *xHandlex_HandleWorld;
    TaskHandle_t *xHandlex_Level;
    TaskHandle_t *xHandlex_HandleErrors;

    String code;
};

Column_t ijmh("IJMH");
Column_t ziez("ZIEZ");

void getSealevelHeightNAP(void * clmn) {

  Column_t *column = static_cast<Column_t *>(clmn);

  while (true) {
    vTaskDelay(600000 / portTICK_PERIOD_MS); // wait 10 minutes (update frequency of seawaterlevel)
    //mind INET is GLOBAL
    if ( xSemaphore_INET != NULL ) {
      if ( xSemaphoreTake( xSemaphore_INET, ( TickType_t ) 10000 / portTICK_PERIOD_MS ) == pdTRUE ) { //10 second wait
        if (modem.isGprs ) { // this should test connection
          if (!client.connect(LEVEL_SERVER, port)) {
            xTaskCreate(logger, "log4", 3000, "Failed to connect server" , 1, NULL);
          } else {
            client.print(String("GET ") +  LEVEL_RESOURCE + column->code + " HTTP/1.1\r\n");
            client.print(String("Host: ") + server + "\r\n");
            client.print("Connection: close\r\n\r\n");
            client.println();
            uint32_t timeout = millis();
            while (client.connected() && millis() - timeout < 10000L) {
              // Print available data
              //todo
              ........
              while (client.available()) {
                char c = client.read();
                timeout = millis();
              }
            }
          }
          //no longer needed to hold the inet-connection, we got what we need.
          xSemaphoreGive( xSemaphore_INET );

          if (true) { // test http scope
            float value = content.toFloat();

            float pressure = ((value * C_RATIO + C_HEIGHT_NAP) * 3.1415926f * pow(C_R, 2)) / 1000.0f; //h * pi * r² (volume cylinder) 1000cm³ = 1 kg = liter

            String l = "pressure wanted" + String(pressure);
            xTaskCreate(logger, "log4", 3000, &l , 1, NULL);

            if ( column->xSemaphore_P != NULL) {
              if ( xSemaphoreTake( column->xSemaphore_P, ( TickType_t ) 10000 / portTICK_PERIOD_MS ) == pdTRUE ) {
                column->pressureWanted = min(C_P_MAX, pressure);
                //pressure is set, release semaphore
                xSemaphoreGive(column->xSemaphore_P);
              }
            }
          }
        } else {
          //no longer needed to hold the inet-connection, we're skipping this one.
          xSemaphoreGive( xSemaphore_INET );
        }
      }
    }
  }
}

//checks the level of the column against the wanted level and sets the worlds.
void determinWorld(void *parameter ) {
  Column_t *column = static_cast<Column_t *>(parameter);
  static String l;
  while (true) {
    if ( column->xSemaphore_P != NULL) {
      if ( xSemaphoreTake( column->xSemaphore_P, ( TickType_t ) 1000 / portTICK_PERIOD_MS ) == pdTRUE ) {
        float p_upper = column->pressureWanted * 1.025f; //+2.5 % error
        float p_lower = column->pressureWanted * 0.975f; //-2.5 % error
        //pressure is used, release semaphore
        xSemaphoreGive(column->xSemaphore_P);
        if (p_lower > column->pressureCurrent ) {
          column->setWorld(W1_LOW);
          l = "Column to low";

        } else if (p_upper < column->pressureCurrent) {
          column->setWorld(W2_HIGH);
          l = "Column to high";

        } else {
          column->setWorld(W3_GOOD);
          l = "Column ok";
        }
      }
      xTaskCreate(logger, "log3", 3000, &l , 1, NULL);
    }

    vTaskDelay(60000 / portTICK_PERIOD_MS); // wait 10 minutes
  }
}

//task to lower water in column (only task to do solenoid IO)
void lowerWater(void * parameter) {
  Column_t *column = static_cast<Column_t *>(parameter);
  if ( column->xSemaphore_P != NULL ) {
    /* See if we can obtain the semaphore.  If the semaphore is not
      available wait 30 ticks to see if it becomes free. */
    if ( xSemaphoreTake( column->xSemaphore_P, ( TickType_t ) 30 ) == pdTRUE ) {
      float minutes_flow = min(1.0f, (column->pressureCurrent - column->pressureWanted) / FLOW_OUT);
      digitalWrite(SOLENOID, LOW);
      vTaskDelay(round(minutes_flow * 60000) / portTICK_PERIOD_MS); // wait a period
      digitalWrite(SOLENOID, HIGH);
      xSemaphoreGive( column->xSemaphore_P );
    }
  }
  vTaskDelete(NULL); // done
}

//task to raise water in column (only task to do pump IO)
void raiseWater(void * parameter) {
  Column_t *column = static_cast<Column_t *>(parameter);
  if ( column->xSemaphore_P != NULL ) {
    /* See if we can obtain the semaphore.  If the semaphore is not
      available wait 30 ticks to see if it becomes free. */
    if ( xSemaphoreTake( column->xSemaphore_P, ( TickType_t ) 30 ) == pdTRUE ) {
      float minutes_flow = min(1.0f, (column->pressureWanted - column->pressureCurrent) / FLOW_IN);
      digitalWrite(PUMP, HIGH);
      vTaskDelay(round(minutes_flow * 60000) / portTICK_PERIOD_MS); // wait a period
      digitalWrite(PUMP, LOW);
      xSemaphoreGive( column->xSemaphore_P );
    }
  }
  vTaskDelete(NULL); // done
}

void handleWorlds(void * parameter) {
  //handles the world changes and fires the corresponding tasks
  Column_t *column = static_cast<Column_t *>(parameter);
  static String l; //logging
  while (true) {
    if ( column->xSemaphore_world != NULL ) {
      if ( xSemaphoreTake( column->xSemaphore_world, ( TickType_t ) 100 ) == pdTRUE ) {
        if (column->world != column->next_world) {
          l = "World has changed to " + String(column->next_world) + " from " + String(column->world);
          xTaskCreate(logger, "log2", 2000, &l , 1, NULL);
          switch (column->next_world) {
            case W1_LOW:
              xTaskCreate(raiseWater, "raise", 1000, column, 1, NULL);
              break;
            case W2_HIGH:
              xTaskCreate(lowerWater, "lower", 1000, column, 1, NULL);
              break;
            case W3_GOOD:
              //where ok.
              break;
            case W4_ERROR:
              l = "Error state initiated";
              xTaskCreate(logger, "logger", 2000, &l , 1, NULL);
              digitalWrite(WIFI_ON, LOW); // INET off
              //stops the worlds
              vTaskDelete(column->xHandlex_World);
              vTaskDelete(column->xHandlex_Pressure);
              vTaskDelete(column->xHandlex_HandleWorld);
              vTaskDelete(column->xHandlex_Level);
              vTaskDelete(column->xHandlex_HandleErrors);
              break;
            case START:
              xTaskCreate(initiateINETConnection, "iNet_Connection", 10000, NULL, 1, NULL);
              break;
            default:
              break;
          }
        }
        xSemaphoreGive( column->xSemaphore_world );
      }
    }
    vTaskDelay(120000 / portTICK_PERIOD_MS); // wait 2 minutes
  }
}

void pressureReader(void* parameter) {
  
  Column_t *column = static_cast<Column_t *>(parameter);  

  while (true) {
    if ( column->xSemaphore_P != NULL) {
      if ( xSemaphoreTake( column->xSemaphore_P, ( TickType_t ) 60000 / portTICK_PERIOD_MS ) == pdTRUE ) {
        //read 12bit ADC > max 4095
        float p_now = map_f(float(analogRead(PRESSURE)), 0.0, 4095.0, 0.0, C_P_MAX);
        xTaskCreate(logger, "log1", 2000, "Pressure read" + String(p_now), 1, NULL);
        xSemaphoreGive( column->xSemaphore_P );
        column->addNewPressureValue(p_now);
      }
    }
    vTaskDelay(30000 / portTICK_PERIOD_MS); // wait 1/2 minute
  }
}


void testINETConnection(void * parameter) {
  vTaskDelay(1000 / portTICK_PERIOD_MS); // 1 second
  while (true) {
    if ( xSemaphore_INET != NULL ) {
      if ( xSemaphoreTake( xSemaphore_INET, ( TickType_t ) 100 ) == pdTRUE ) {
        if (modem.isGprsConnected()) {
          digitalWrite(WIFI_ON, HIGH);
          vTaskDelay(119000 / portTICK_PERIOD_MS); // near 2 minutes
        } else {
          digitalWrite(WIFI_ON, LOW);
          ijmh.setWorld(START);
          ziez.setWorld(START);
          vTaskDelay(1000 / portTICK_PERIOD_MS); // 1 second
          digitalWrite(WIFI_ON, HIGH);
        }
        xSemaphoreGive( xSemaphore_INET );
      }
    }     
  }
}

void initiateINETConnection(void * parameter) {
  //start the GSM
  if (false) {  // test inet connection
    if ( xSemaphore_INET != NULL ) {
      if ( xSemaphoreTake( xSemaphore_INET, ( TickType_t ) 1000 / portTICK_PERIOD_MS ) == pdTRUE ) {
        // Init modem
        modem.restart();
        if (GSM_PIN && modem.getSimStatus() != 3) { 
          modem.simUnlock(GSM_PIN); 
        }
        modem.gprsConnect(apn, gprsUser, gprsPass);
        if (!modem.waitForNetwork()) {
          SerialMon.println(" fail");
        } else {
          ijmh.setWorld(W3_GOOD);
          ziez.setWorld(W3_GOOD);
        }
        xSemaphoreGive( xSemaphore_INET );
      }
    }
    vTaskDelete(NULL); // done
  }
}

TaskHandle_t xHandlex_INET;

void setup() {
  SerialMon.begin(115200);
  SerialAT.begin(115200,SERIAL_8N1,16,17,false);
  modem.setBaud(115200)

  pinMode(PUMP, OUTPUT);
  pinMode(SOLENOID, OUTPUT);
  pinMode(WIFI_ON, OUTPUT);

  digitalWrite(PUMP, LOW); // pump off
  digitalWrite(SOLENOID, HIGH); // solenoid closed, change on release
  digitalWrite(WIFI_ON, LOW); // INET off

  xSemaphore_INET = xSemaphoreCreateMutex();
  xSemaphore_log = xSemaphoreCreateMutex();

  String modemInfo = modem.getModemInfo();
  SerialMon.print("Modem Info: ");
  SerialMon.println(modemInfo);


  SerialMon.println("Starting tasks");

  //handles the worlds.
  xTaskCreate(handleWorlds, "IJM_H_Worlds", 10000, &ijmh, 1, ijmh.xHandlex_World);
  //handels reading of current column height in kg.
  xTaskCreate(pressureReader, "IJM_H_Pressure", 1000, &ijmh, 1, ijmh.xHandlex_Pressure);
  //handles reading of waterlevel
  xTaskCreate(getSealevelHeightNAP, "IJM_H_Level", 10000, &ijmh, 1, ijmh.xHandlex_Level);
  //what is the world like today?
  xTaskCreate(determinWorld, "IJM_H_DetWorlds", 3000, &ijmh, 1, ijmh.xHandlex_HandleWorld);
  //Errors checking
  //xTaskCreate(checkError, "IJ_Errors", 3000, NULL, 1,  &xHandlex_HandleErrors);

  //test for net connection
  xTaskCreate(testINETConnection, "INETt" , 3000, NULL, 1,  &xHandlex_INET);
}

void loop() {
  vTaskDelete(NULL); //cancel the loop, we use tasks
}
