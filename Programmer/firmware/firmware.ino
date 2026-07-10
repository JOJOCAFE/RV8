// ============================================================
// RV8 Programmer — ESP32-WROOM-32 Firmware
// Connects to CPU board via RV8-Bus (40-pin)
// PROG mode: hold /RST, drive A[14:0]+D[7:0]+/WR to flash ROM
// RUN mode: release bus, UART bridge via /SLOT1
// Serial protocol: 115200 baud
//   '?' → "Connected\n"
//   'F' + len_hi + len_lo + data[len] → flash ROM
//   'V' → verify (read back and send)
//   'R' → reset CPU (pulse /RST)
// ============================================================

// --- Pin Definitions ---

// Data bus D[7:0] — bidirectional, via TXS0108E #2 → RV8-Bus pin 17-24
const int DATA_PINS[8] = {13, 12, 14, 27, 26, 25, 33, 32};

// Address via 74HC595 ×2 shift register → RV8-Bus pin 1-15
#define PIN_SR_DATA  23  // SER (pin 14 on 595 #1)
#define PIN_SR_CLK   18  // SRCLK (pin 11 on both 595)
#define PIN_SR_LATCH 19  // RCLK (pin 12 on both 595)

// Control signals via TXS0108E #1 → RV8-Bus
#define PIN_nRST  4   // → Bus pin 26 (/RST)
#define PIN_nWR   16  // → Bus pin 27 (/WR) — write strobe
#define PIN_nRD_O 17  // → Bus pin 28 (/RD) — read strobe (drives ROM /OE)

// Input-only pins (GPIO 34-39) — from RV8-Bus
#define PIN_nSLOT 34  // ← Bus pin 30 (/SLOT1)
#define PIN_nRD   35  // ← Bus pin 28 (/RD)
#define PIN_nWR_S 36  // ← Bus pin 27 (/WR sense — for RUN mode)
#define PIN_MODE  39  // PROG/RUN switch: LOW=PROG, HIGH=RUN

// --- State ---
enum Mode { MODE_PROG, MODE_RUN };
volatile Mode currentMode;
volatile bool rxReady = false;
volatile uint8_t rxByte = 0;

// --- Data Bus Helpers ---

void dataBusOutput() {
  for (int i = 0; i < 8; i++) pinMode(DATA_PINS[i], OUTPUT);
}

void dataBusInput() {
  for (int i = 0; i < 8; i++) pinMode(DATA_PINS[i], INPUT);
}

void dataBusWrite(uint8_t val) {
  for (int i = 0; i < 8; i++) {
    digitalWrite(DATA_PINS[i], (val >> i) & 1);
  }
}

uint8_t dataBusRead() {
  uint8_t val = 0;
  for (int i = 0; i < 8; i++) {
    if (digitalRead(DATA_PINS[i])) val |= (1 << i);
  }
  return val;
}

// --- Address Helpers ---
// Full A[14:0] via 74HC595 ×2 daisy-chain (16 bits shifted, A15=0 for ROM)

void setAddress(uint16_t addr) {
  // Shift 16 bits MSB first: [0, A14..A8, A7..A0]
  // A15=0 selects ROM on CPU board (ROM /CE = /A15)
  uint16_t bits = addr & 0x7FFF;
  for (int i = 15; i >= 0; i--) {
    digitalWrite(PIN_SR_DATA, (bits >> i) & 1);
    digitalWrite(PIN_SR_CLK, HIGH);
    digitalWrite(PIN_SR_CLK, LOW);
  }
  digitalWrite(PIN_SR_LATCH, HIGH);
  digitalWrite(PIN_SR_LATCH, LOW);
}

// --- ROM Write/Read via Bus ---
// ROM on CPU board: /CE = /A15 (addr < 0x8000 → selected)
// In PROG mode only, the Programmer holds CPU reset and owns /RD and /WR.
// During normal CPU runtime, ROM /WE must remain inactive.

void romWriteByte(uint16_t addr, uint8_t data) {
  setAddress(addr);
  dataBusOutput();
  dataBusWrite(data);
  delayMicroseconds(1);

  // Pulse /WR low in PROG mode → ROM sees write cycle.
  digitalWrite(PIN_nWR, LOW);
  delayMicroseconds(1);
  digitalWrite(PIN_nWR, HIGH);

  delayMicroseconds(1);
}

uint8_t romReadByte(uint16_t addr) {
  setAddress(addr);
  dataBusInput();
  digitalWrite(PIN_nWR, HIGH);   // /WR inactive
  digitalWrite(PIN_nRD_O, LOW);  // /RD active → ROM outputs data
  delayMicroseconds(1);
  uint8_t val = dataBusRead();
  digitalWrite(PIN_nRD_O, HIGH); // /RD inactive
  return val;
}

// --- Serial Protocol Handlers ---

void handleFlash() {
  while (Serial.available() < 2) yield();
  uint16_t len = (Serial.read() << 8) | Serial.read();

  if (len == 0 || len > 32768) {
    Serial.print("E:BAD_LEN\n");
    return;
  }

  Serial.print("K\n");

  digitalWrite(PIN_nRST, LOW);
  digitalWrite(PIN_nWR, HIGH);
  delay(10);

  uint16_t addr = 0;
  uint16_t received = 0;
  uint32_t lastPageAddr = 0xFFFF;

  while (received < len) {
    if (Serial.available()) {
      uint8_t b = Serial.read();

      uint16_t page = addr & 0x7FC0;
      if (page != lastPageAddr && lastPageAddr != 0xFFFF) {
        delay(10);
      }
      lastPageAddr = page;

      romWriteByte(addr, b);
      addr++;
      received++;
    }
    yield();
  }

  delay(10);
  Serial.print("D\n");
}

void handleVerify() {
  digitalWrite(PIN_nRST, LOW);
  digitalWrite(PIN_nWR, HIGH);
  dataBusInput();
  delay(1);

  for (uint16_t addr = 0; addr < 32768; addr++) {
    Serial.write(romReadByte(addr));
    if ((addr & 0xFF) == 0) yield();
  }
}

void handleReset() {
  digitalWrite(PIN_nRST, LOW);
  delay(10);
  digitalWrite(PIN_nRST, HIGH);
  Serial.print("K\n");
}

// --- RUN Mode: UART Bridge via /SLOT1 ---

void runModePoll() {
  // CPU WRITE: /SLOT1 LOW + /WR LOW → read D[7:0], send to PC
  if (digitalRead(PIN_nSLOT) == LOW && digitalRead(PIN_nWR_S) == LOW) {
    dataBusInput();
    uint8_t b = dataBusRead();
    Serial.write(b);
    while (digitalRead(PIN_nWR_S) == LOW) {}
  }

  // CPU READ: /SLOT1 LOW + /RD LOW → drive D[7:0] with buffered byte
  if (digitalRead(PIN_nSLOT) == LOW && digitalRead(PIN_nRD) == LOW) {
    if (rxReady) {
      dataBusOutput();
      dataBusWrite(rxByte);
      rxReady = false;
    } else {
      dataBusOutput();
      dataBusWrite(0x00);
    }
    while (digitalRead(PIN_nRD) == LOW) {}
    dataBusInput();
  }

  // Buffer incoming byte from PC
  if (!rxReady && Serial.available()) {
    rxByte = Serial.read();
    rxReady = true;
  }
}

// --- Mode Detection ---

Mode detectMode() {
  return digitalRead(PIN_MODE) == LOW ? MODE_PROG : MODE_RUN;
}

void enterProgMode() {
  Serial.println("[PROG]");
  digitalWrite(PIN_nRST, LOW);
  pinMode(PIN_nWR, OUTPUT);     // reclaim /WR for ROM write cycles
  digitalWrite(PIN_nWR, HIGH);
  pinMode(PIN_nRD_O, OUTPUT);   // reclaim /RD for read operations
  digitalWrite(PIN_nRD_O, HIGH);
  dataBusInput();
}

void enterRunMode() {
  Serial.println("[RUN]");
  dataBusInput();
  digitalWrite(PIN_nWR, HIGH);
  digitalWrite(PIN_nRD_O, HIGH);
  pinMode(PIN_nWR, INPUT);      // release /WR — let CPU drive it
  pinMode(PIN_nRD_O, INPUT);    // release /RD — let CPU drive it
  digitalWrite(PIN_nRST, HIGH);
  rxReady = false;
}

// --- Setup & Loop ---

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(1);

  // Control output pins
  pinMode(PIN_nRST, OUTPUT);
  digitalWrite(PIN_nRST, LOW);   // hold CPU in reset
  pinMode(PIN_nWR, OUTPUT);
  digitalWrite(PIN_nWR, HIGH);   // /WR inactive
  pinMode(PIN_nRD_O, OUTPUT);
  digitalWrite(PIN_nRD_O, HIGH); // /RD inactive

  // Shift register
  pinMode(PIN_SR_DATA, OUTPUT);
  pinMode(PIN_SR_CLK, OUTPUT);
  pinMode(PIN_SR_LATCH, OUTPUT);
  digitalWrite(PIN_SR_DATA, LOW);
  digitalWrite(PIN_SR_CLK, LOW);
  digitalWrite(PIN_SR_LATCH, LOW);

  // Input-only pins (from bus)
  pinMode(PIN_nSLOT, INPUT);
  pinMode(PIN_nRD, INPUT);
  pinMode(PIN_nWR_S, INPUT);
  pinMode(PIN_MODE, INPUT);

  // Detect initial mode
  currentMode = detectMode();
  if (currentMode == MODE_PROG) enterProgMode();
  else enterRunMode();

  Serial.println("RV8 Programmer ready");
}

void loop() {
  Mode m = detectMode();
  if (m != currentMode) {
    currentMode = m;
    if (m == MODE_PROG) enterProgMode();
    else enterRunMode();
  }

  if (currentMode == MODE_PROG) {
    if (Serial.available()) {
      char cmd = Serial.read();
      switch (cmd) {
        case '?': Serial.print("Connected\n"); break;
        case 'F': handleFlash();  break;
        case 'V': handleVerify(); break;
        case 'R': handleReset();  break;
        default:  Serial.print("E:UNK\n"); break;
      }
    }
  } else {
    runModePoll();
  }
}
