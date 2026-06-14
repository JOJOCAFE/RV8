 1. ผังการต่อระบบไฟเลี้ยง (Power & Ground Lines)ต่อสายไฟเลี้ยงหลักเหล่านี้ให้ครบทุกจุดก่อนเริ่มเดินสายสัญญาณ เพื่อความปลอดภัยของชิป

 [ ESP32 บอร์ด ] -------- (3V3) --------------------> [ TXS0108E ตัวที่ 1 และ 2: พิน 1 (V_A) ]
                                                      [ TXS0108E ตัวที่ 1 และ 2: พิน 10 (OE) ] (ต่อผ่านตัวต้านทาน 10kΩ Pull-up เข้า 3.3V)
                 -------- (VN / 5V) ----------------> [ 74HC595 ตัวที่ 1 และ 2: พิน 16 (VCC) ]
                                                      [ TXS0108E ตัวที่ 1 และ 2: พิน 20 (V_B) ]
                                                      [ AT28C256: พิน 28 (VCC) ]
                 -------- (GND) --------------------> ต่อพ่วงเข้ากับพิน GND ของไอซีทุกตัว (Common Ground)
                                                      - TXS0108E ตัวที่ 1 และ 2: พิน 11 (GND)
                                                      - 74HC595 ตัวที่ 1 และ 2: พิน 8 (GND)
                                                      - AT28C256: พิน 14 (GND)


2. ผังวงจรฝั่งสัญญาณควบคุม และ Address Busใช้ TXS0108E ตัวที่ 1 แปลงสัญญาณจาก ESP32 (3.3V) เป็น 5V ส่งเข้า 74HC595 และขา Control ของ ROM

[ ESP32 ฝั่ง 3.3V ]       [ TXS0108E ตัวที่ 1 ]              [ อุปกรณ์ปลายทาง ฝั่ง 5V ]

📌 กลุ่มขับชิฟต์รีจิสเตอร์เพื่อกำหนด Address
GPIO 23 ----------------> พิน 2 (A1) <======> พิน 19 (B1) ------> [ 74HC595 ตัวที่ 1: พิน 14 (SER) ]
GPIO 18 ----------------> พิน 3 (A2) <======> พิน 18 (B2) ------> [ 74HC595 ทั้ง 2 ตัว: พิน 11 (SRCLK) ]
GPIO 19 ----------------> พิน 4 (A3) <======> พิน 17 (B3) ------> [ 74HC595 ทั้ง 2 ตัว: พิน 12 (RCLK) ]

📌 กลุ่มสั่งงานคำสั่งควบคุม ROM ลอจิก 5V เต็ม
GPIO 4  ----------------> พิน 5 (A4) <======> พิน 16 (B4) ------> [ AT28C256: พิน 20 (/CE - Chip Enable) ]
GPIO 16 ----------------> พิน 6 (A5) <======> พิน 15 (B5) ------> [ AT28C256: พิน 22 (/OE - Output Enable) ]
GPIO 17 ----------------> พิน 7 (A6) <======> พิน 14 (B6) ------> [ AT28C256: พิน 27 (/WE - Write Enable) ]
(ขา A7/B7 และ A8/B8 ของ TXS ตัวที่ 1 นี้ไม่ได้ใช้งาน ให้ปล่อยลอยไว้ได้เลย)

การเชื่อมต่อระหว่าง 74HC595 (ทั้ง 2 ตัว) ไปยังขา Address ของ AT28C256

📌 การจัดการขาพิเศษของ 74HC595 ทั้งตัวที่ 1 และ 2:
- พิน 10 (/SRCLR) -------> ต่อเข้าไฟ 5V (VCC)
- พิน 13 (/G) -----------> ต่อลงกราวด์ (GND)

📌 การต่อพ่วงชิป (Daisy Chain):
- [ 74HC595 ตัวที่ 1: พิน 9 (Q7S) ] --------------------> ต่อข้ามไปเข้า [ 74HC595 ตัวที่ 2: พิน 14 (SER) ]

📌 การเดินสายไปยังขา Address ของ ROM (AT28C256):
- 74HC595 ตัวที่ 1 (คุม Address บิตต่ำ A0 - A7):
  พิน 15 (Q0) -> ขา A0 (พิน 10)       พิน 1 (Q1) -> ขา A1 (พิน 9)        พิน 2 (Q2) -> ขา A2 (พิน 8)
  พิน 3 (Q3) -> ขา A3 (พิน 7)        พิน 4 (Q4) -> ขา A4 (พิน 6)        พิน 5 (Q5) -> ขา A5 (พิน 5)
  พิน 6 (Q6) -> ขา A6 (พิน 4)        พิน 7 (Q7) -> ขา A7 (พิน 3)

- 74HC595 ตัวที่ 2 (คุม Address บิตสูง A8 - A14):
  พิน 15 (Q0) -> ขา A8 (พิน 25)      พิน 1 (Q1) -> ขา A9 (พิน 24)       พิน 2 (Q2) -> ขา A10 (พิน 21)
  พิน 3 (Q3) -> ขา A11 (พิน 23)      พิน 4 (Q4) -> ขา A12 (พิน 2)       พิน 5 (Q5) -> ขา A13 (พิน 26)
  พิน 6 (Q6) -> ขา A14 (พิน 1)       พิน 7 (Q7) -> (ปล่อยลอย ไม่ใช้งาน)

3. ผังวงจรฝั่ง Data Bus (สื่อสารแบบ 2 ทาง)ใช้ TXS0108E ตัวที่ 2 ทั้งตัวในการรับ-ส่งข้อมูล 8 บิต ระหว่าง ESP32 (3.3V) และ AT28C256 (5V)

[ ESP32 ฝั่ง 3.3V ]       [ TXS0108E ตัวที่ 2 ]              [ AT28C256 Data Pins ]
GPIO 13 ----------------> พิน 2 (A1) <======> พิน 19 (B1) ------> พิน 11 (I/O 0)
GPIO 12 ----------------> พิน 3 (A2) <======> พิน 18 (B2) ------> พิน 12 (I/O 1)
GPIO 14 ----------------> พิน 4 (A3) <======> พิน 17 (B3) ------> พิน 13 (I/O 2)
GPIO 27 ----------------> พิน 5 (A4) <======> พิน 16 (B4) ------> พิน 15 (I/O 3)
GPIO 26 ----------------> พิน 6 (A5) <======> พิน 15 (B5) ------> พิน 16 (I/O 4)
GPIO 25 ----------------> พิน 7 (A6) <======> พิน 14 (B6) ------> พิน 17 (I/O 5)
GPIO 33 ----------------> พิน 8 (A7) <======> พิน 13 (B7) ------> พิน 18 (I/O 6)
GPIO 32 ----------------> พิน 9 (A8) <======> พิน 12 (B8) ------> พิน 19 (I/O 7)

C 104 (0.1uF)เซรามิก คร่อม Vcc และ Gnd ของทุกตัว

เขียนฟังก์ชันในโค้ดแยกส่วนกันอย่างชัดเจน เช่น ฟังก์ชัน setAddress(uint16_t addr) สำหรับยิงบิตเข้า 74HC595 และฟังก์ชัน writeEEPROM() / readEEPROM() เพื่อควบคุมทิศทางของขาพินคำสั่งควบคุมตามลำดับ [1]

Example Code

// ==========================================
// 📌 CONFIGURATION & PIN MAPPING (ESP32)
// ==========================================

// กลุ่มควบคุม Address (ผ่าน TXS0108E #1 -> 74HC595 x2)
#define SHIFT_DATA   23   // ขา SER
#define SHIFT_CLK    18   // ขา SRCLK
#define SHIFT_LATCH  19   // ขา RCLK

// กลุ่มควบคุมคำสั่ง ROM (ผ่าน TXS0108E #1)
#define ROM_CE       4    // Chip Enable (Active LOW)
#define ROM_OE       16   // Output Enable (Active LOW)
#define ROM_WE       17   // Write Enable (Active LOW)

// กลุ่มรับ-ส่งข้อมูล Data Bus 8 บิต (ผ่าน TXS0108E #2)
const int dataPins[8] = {13, 12, 14, 27, 26, 25, 33, 32}; // I/O 0 ถึง I/O 7

// ==========================================
// 🛠️ FUNCTIONS FOR HARDWARE CONTROL
// ==========================================

// ฟังก์ชันกำหนดทิศทางของขาข้อมูล Data Bus (ESP32: INPUT หรือ OUTPUT)
void setDataBusMode(uint8_t mode) {
  for (int i = 0; i < 8; i++) {
    pinMode(dataPins[i], mode);
  }
}

// ฟังก์ชันส่งตำแหน่ง Address 15 บิต ออกไปยัง 74HC595 ทั้ง 2 ตัว
void setAddress(uint16_t address) {
  digitalWrite(SHIFT_LATCH, LOW);
  
  // แยกส่งทีละ 8 บิต (ชิปตัวที่ 2 รับบิตสูงก่อน, ชิปตัวที่ 1 รับบิตต่ำ)
  shiftOut(SHIFT_DATA, SHIFT_CLK, MSBFIRST, (address >> 8) & 0xFF);
  shiftOut(SHIFT_DATA, SHIFT_CLK, MSBFIRST, address & 0xFF);
  
  digitalWrite(SHIFT_LATCH, HIGH);
}

// ฟังก์ชันเขียนข้อมูลลงบัสข้อมูล (ใช้ตอนฟังก์ชัน Write)
void writeDataBus(uint8_t data) {
  for (int i = 0; i < 8; i++) {
    digitalWrite(dataPins[i], (data >> i) & 0x01);
  }
}

// ฟังก์ชันอ่านข้อมูลจากบัสข้อมูล (ใช้ตอนฟังก์ชัน Read)
uint8_t readDataBus() {
  uint8_t data = 0;
  for (int i = 0; i < 8; i++) {
    if (digitalRead(dataPins[i]) == HIGH) {
      data |= (1 << i);
    }
  }
  return data;
}

// ==========================================
// 💾 CORE ROM OPERATIONS (READ / WRITE)
// ==========================================

// 🔵 ฟังก์ชันอ่านข้อมูลจาก EEPROM 1 ไบต์
uint8_t readEEPROM(uint16_t address) {
  setDataBusMode(INPUT); // เปลี่ยนโหมดพินเป็นอินพุตเพื่อเตรียมรับข้อมูล
  
  // ปิดสวิตช์ควบคุมทั้งหมดก่อนเปลี่ยนตำแหน่งข้อมูล
  digitalWrite(ROM_WE, HIGH);
  digitalWrite(ROM_OE, HIGH);
  digitalWrite(ROM_CE, HIGH);
  
  setAddress(address);   // สั่งขยับ Address ไปยังตำแหน่งที่ต้องการ
  
  // เริ่มจังหวะเวลาอ่านข้อมูล (Read Cycle)
  digitalWrite(ROM_CE, LOW); // เปิดใช้งานชิป ROM
  digitalWrite(ROM_OE, LOW); // เปิดให้ ROM จ่ายสัญญาณข้อมูลออกมา
  
  delayMicroseconds(1);      // รอสัญญาณเสถียร (ตามสเปก AT28C256 ใช้เวลาเข้าถึงข้อมูลพิกัดนาโนวินาที)
  
  uint8_t data = readDataBus(); // อ่านลอจิกบัสข้อมูล
  
  // เคลียร์ขาสัญญาณคุมกลับเข้าสู่โหมดพัก
  digitalWrite(ROM_OE, HIGH);
  digitalWrite(ROM_CE, HIGH);
  
  return data;
}

// 🔴 ฟังก์ชันเขียนข้อมูลลง EEPROM 1 ไบต์ (Byte Write)
void writeEEPROM(uint16_t address, uint8_t data) {
  setDataBusMode(OUTPUT); // เปลี่ยนโหมดพินเป็นเอาต์พุตเพื่อส่งข้อมูลเข้าไป
  
  // ตรึงขาสัญญาณคุมให้อยู่ในสถานะปลอดภัยก่อนเริ่มงาน
  digitalWrite(ROM_WE, HIGH);
  digitalWrite(ROM_OE, HIGH);
  digitalWrite(ROM_CE, HIGH);
  
  setAddress(address);   // กำหนดตำแหน่งที่จะเขียน
  writeDataBus(data);    // ป้อนข้อมูลเตรียมรอไว้ที่บัสข้อมูล
  
  // เริ่มจังหวะเวลาเขียนข้อมูล (Write Cycle Sequence)
  digitalWrite(ROM_CE, LOW); // เปิดใช้งานชิป
  delayMicroseconds(1);
  digitalWrite(ROM_WE, LOW); // ยิงพัลส์สัญญาณสั่ง "บันทึก" (Write Enable)
  
  delayMicroseconds(1);      // พัลส์ความกว้างขั้นต่ำของสัญญาณสับบันทึกข้อมูล (Twp)
  
  digitalWrite(ROM_WE, HIGH); // ปิดสัญญาณบันทึกเพื่อล็อกข้อมูลเข้าหน่วยความจำ
  digitalWrite(ROM_CE, HIGH); // ปิดการทำงานชิป
  
  // ⚠️ ข้อควรระวังสูงสุด: ชิป AT28C256 ต้องการเวลาประมวลผลภายในหลังรับคำสั่ง (Write Cycle Time: Twc)
  // สเปกโรงงานกำหนดให้รอประมาณ 10 มิลลิวินาที ห้ามส่งข้อมูลไบต์ถัดไปซ้อนในช่วงเวลานี้เด็ดขาด
  delay(10); 
}

// ==========================================
// 🚀 ARDUINO STANDARD MAIN RUN
// ==========================================

void setup() {
  Serial.begin(115200);
  
  // ตั้งค่ากลุ่มขาควบคุมเอาต์พุต
  pinMode(SHIFT_DATA, OUTPUT);
  pinMode(SHIFT_CLK, OUTPUT);
  pinMode(SHIFT_LATCH, OUTPUT);
  
  pinMode(ROM_CE, OUTPUT);
  pinMode(ROM_OE, OUTPUT);
  pinMode(ROM_WE, OUTPUT);
  
  // ตรึงขาให้อยู่ในสถานะไม่ทำงานตอนเปิดเครื่อง (High-State Safe)
  digitalWrite(ROM_CE, HIGH);
  digitalWrite(ROM_OE, HIGH);
  digitalWrite(ROM_WE, HIGH);
  
  Serial.println("\n--- Starting AT28C256 Programmer Test ---");
  
  // 📝 ทดสอบเขียนข้อมูล
  Serial.println("Writing data 0xA5 to Address 0x0042...");
  writeEEPROM(0x0042, 0xA5);
  
  // 🔍 ทดสอบอ่านข้อมูลกลับมาเช็ก
  Serial.print("Reading data from Address 0x0042: 0x");
  uint8_t testRead = readEEPROM(0x0042);
  Serial.println(testRead, HEX);
}

void loop() {
  // พักระบบไว้หลังจากรันครั้งแรกเสร็จใน setup
}
