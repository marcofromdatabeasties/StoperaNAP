  
/**
 * Programma dat aan de hand van de (deels) verwachte waterstanden boven NAP in het Stopera monument de juiste waarde laat zien.
 * 
 * This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
 * 
 */
#include <WiFi.h>
#include "Keys.h"

#define PUMP 23 //pomp GPIO23, om water bij te pompen
#define SOLENOID 22 //solenoid GPIO24, water weg te laten lopen.
#define WIFI_ON 21 //Wifi active led indicator
#define PRESSURE 5 // FSR op ADC1_0, meet de hoeveelheid water in kolom.
#define MAX_PRES 4095 //max conversie waarde: 0-4095 bij 0.1-3.2 volt.

#define W1_LAAG 0 // state 1: water in kolom te laag tov NAP/ water in column to low
#define W2_HOOG 1 // state 2: water in kolom te hoog tov NAP/water in column to high
#define W3_GOED 2 // state 3: water in kolom goed tov NAP/water in column ok
#define W4_ERROR 3 // state 4: water in kolom veranderd niet / meting onjuist/ error state: water is not moving or measurement is off.
#define START 4 //state 5: starting (WIFI)

#define C_HEIGHT 120 // 1.2 meter
#define C_R 5 //5 cm radius

#define FLOW_IN 7 //liter per minute.
#define FLOW_OUT 5 //liter per minute.

uint8_t state = START;

void initiateWIFIConnection(void * parameter) {
  //start the WIFI and connect.
  digitalWrite(WIFI_ON, LOW);
  WiFi.begin(ST_SSID, PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        vTaskDelay(500 / portTICK_PERIOD_MS);
    }
  digitalWrite(WIFI_ON, HIGH);
  vTaskDelete(NULL); // done 
}


void setup() {
  pinMode(PUMP, OUTPUT);
  pinMode(SOLENOID, OUTPUT);
  pinMode(WIFI_ON, OUTPUT);

  digitalWrite(PUMP, LOW); // pump off
  digitalWrite(SOLENOID, HIGH); // solenoid closed

  

}

void loop() {
  vTaskDelete(NULL); //cancel the loop, we use tasks
}
