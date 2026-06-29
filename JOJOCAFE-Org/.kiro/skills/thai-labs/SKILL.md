---
name: thai-labs
description: Template and style guide for Thai+English hardware lab sheets aimed at middle school students. Use when writing lab documentation, build guides, or student worksheets.
---

# Thai Lab Sheet Style Guide

## Audience
- Middle school students (มัธยมต้น)
- No prior electronics experience assumed
- Thai primary language, English technical terms

## Lab Sheet Structure

Every lab follows this exact structure:

```
# Lab XX: [English title]
# แลปที่ XX: [Thai title]

## เป้าหมาย (Goal)
- One sentence: what the student will achieve

## ความรู้พื้นฐาน (Background)
- 2-3 short paragraphs explaining the concept
- Use analogies (water flow = current, etc.)
- Include ONE simple diagram if helpful

## อุปกรณ์ (Parts)
| ชิ้น | ชื่อ | จำนวน |
|------|------|--------|
| U1   | 74HC574 (Octal D Flip-Flop) | 1 |
...

## ผังวงจร (Circuit Diagram)
- ASCII or reference to image
- Label every pin number
- Show power (VCC, GND) connections

## ตารางการต่อสาย (Wiring Table)
| จาก (From) | ไป (To) | สาย (Wire) |
|------------|---------|-------------|
| U1 pin 11  | U2 pin 3 | Yellow |
...

## ขั้นตอน (Steps)
1. Numbered steps
2. One action per step
3. "ต่อสาย..." (Connect wire...)
4. "ตรวจสอบ..." (Verify...)

## ทดสอบ (Test)
- What to observe
- Expected LED pattern / output
- What to do if it doesn't work

## เช็คลิสต์ (Checklist)
- [ ] Power connected correctly?
- [ ] All wires match table?
- [ ] Output matches expected?
```

## Style Rules

1. **Short sentences** — max 15 words Thai, 12 words English
2. **Pin numbers always** — never say "connect CLK", say "connect U1 pin 11 (CLK)"
3. **Full chip name on first mention** — "U7 (74HC86, Quad XOR)"
4. **Color-code wires** — assign colors in wiring table
5. **One concept per lab** — don't combine counter + ALU in one lab
6. **Test before proceeding** — every lab ends with a test step
7. **Thai for explanation, English for technical terms** — "ชิป U1 (74HC574) ทำหน้าที่เป็น register"
