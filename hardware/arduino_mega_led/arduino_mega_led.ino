#include <string.h>

const char DEVICE_ID[] = "mega-onboard-led-01";
const size_t LINE_CAPACITY = 128;
char lineBuffer[LINE_CAPACITY];
size_t lineLength = 0;
bool discardUntilNewline = false;

char* trimField(char* value) {
  while (*value == ' ' || *value == '\t') ++value;
  size_t length = strlen(value);
  while (length > 0 && (value[length - 1] == ' ' || value[length - 1] == '\t')) {
    value[--length] = '\0';
  }
  return value;
}

bool isCommandId(const char* value) {
  if (value == nullptr || value[0] == '\0' || strlen(value) > 40) return false;
  for (const char* cursor = value; *cursor != '\0'; ++cursor) {
    const bool allowed = (*cursor >= 'a' && *cursor <= 'z')
      || (*cursor >= 'A' && *cursor <= 'Z')
      || (*cursor >= '0' && *cursor <= '9')
      || *cursor == '-';
    if (!allowed) return false;
  }
  return true;
}

void handleLine(char* line) {
  char* fields[4] = {line, nullptr, nullptr, nullptr};
  size_t fieldCount = 1;
  bool malformed = false;
  for (char* cursor = line; *cursor != '\0'; ++cursor) {
    if (*cursor != ',') continue;
    if (fieldCount == 4) {
      malformed = true;
      break;
    }
    *cursor = '\0';
    fields[fieldCount++] = cursor + 1;
  }
  for (size_t index = 0; index < fieldCount; ++index) {
    fields[index] = trimField(fields[index]);
    if (fields[index][0] == '\0') malformed = true;
  }

  if (malformed || fieldCount != 4 || strcmp(fields[0], "AEGIS/1") != 0
      || !isCommandId(fields[1])) {
    Serial.println("AEGIS/1,ERROR,malformed");
    return;
  }
  if (strcmp(fields[2], DEVICE_ID) != 0) {
    Serial.print("AEGIS/1,");
    Serial.print(fields[1]);
    Serial.println(",ERROR,wrong_device");
    return;
  }

  if (strcmp(fields[3], "LED_ON") == 0) {
    digitalWrite(LED_BUILTIN, HIGH);
  } else if (strcmp(fields[3], "LED_OFF") == 0) {
    digitalWrite(LED_BUILTIN, LOW);
  } else {
    Serial.print("AEGIS/1,");
    Serial.print(fields[1]);
    Serial.println(",ERROR,unsupported_command");
    return;
  }

  const bool ledIsOn = digitalRead(LED_BUILTIN) == HIGH;
  Serial.print("AEGIS/1,");
  Serial.print(fields[1]);
  Serial.print(",OK,");
  Serial.println(ledIsOn ? "ON" : "OFF");
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.begin(115200);
}

void loop() {
  while (Serial.available() > 0) {
    const char next = static_cast<char>(Serial.read());
    if (next == '\r' || next == '\n') {
      if (!discardUntilNewline && lineLength > 0) {
        lineBuffer[lineLength] = '\0';
        handleLine(lineBuffer);
      } else if (discardUntilNewline) {
        Serial.println("AEGIS/1,ERROR,line_too_long");
      }
      lineLength = 0;
      discardUntilNewline = false;
      continue;
    }
    if (discardUntilNewline) continue;
    if (lineLength + 1 >= LINE_CAPACITY) {
      lineLength = 0;
      discardUntilNewline = true;
      continue;
    }
    lineBuffer[lineLength++] = next;
  }
}
