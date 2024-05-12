
int relayPin = 2;

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(20);

  
  pinMode(relayPin, OUTPUT);
}



void loop() {
  int relayState = 0;
  if (Serial.available()) {
    String data = Serial.readString();
    // Serial.read();

    data.replace("\n", "");

    if (data == "1") {
      relayState = 1;
    }
    else {
      relayState = 0;
    }

    Serial.println("Received: [" + data + "]");

    // Serial.println("Set to " + String(relayState));

    digitalWrite(relayPin, relayState);
  }
}