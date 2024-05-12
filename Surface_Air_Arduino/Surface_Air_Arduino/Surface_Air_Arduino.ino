
int relayPin = 2;

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(20);

  
  pinMode(relayPin, OUTPUT);
  
  Serial.println("Begin.");
}



void loop() {
  if (Serial.available()) {
    String data = Serial.readString();
    int relayState = 0;

    if (data == "1") {
      relayState = 1;
    }

    Serial.write("Set to ")

    digitalWrite(relayPin, relayState);
  }
}