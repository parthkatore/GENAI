# ArduinoMate — User Questions  (Day 5)

**Student:** Parth Dasharath Katore | Enroll: 2124UCEM2079 | Roll: 53

Ten realistic questions an ArduinoMate user might ask, covering all major Arduino concepts in the Week 1 knowledge base.

---

## Q1 — What does `pinMode()` do, and when must I call it?

**Expected answer source:** `pinMode` record (Digital I/O category)

`pinMode(pin, mode)` configures a digital pin as `INPUT`, `OUTPUT`, or `INPUT_PULLUP`. It must be called inside `setup()` before any `digitalRead()` or `digitalWrite()` on that pin. Forgetting it causes unpredictable behaviour because the pin's direction register is in an undefined state after reset.

---

## Q2 — How do I read a button press with `digitalRead()`?

**Expected answer source:** `digitalRead` record (Digital I/O category)

Wire the button between the pin and GND, then use `pinMode(pin, INPUT_PULLUP)` so the pin reads `HIGH` normally and `LOW` when pressed. Call `digitalRead(pin)` inside `loop()`. Without `INPUT_PULLUP` (or an external pull-up resistor), an unconnected pin floats and returns random `HIGH`/`LOW` values.

---

## Q3 — What is the difference between `delay()` and `millis()`?

**Expected answer source:** `delay` and `millis` records (Time category)

`delay(ms)` completely blocks all code execution for the specified milliseconds — nothing else runs, including reading sensors or responding to button presses. `millis()` returns the number of milliseconds since the board started without blocking anything. The standard non-blocking pattern is to record a `startTime = millis()` and check `if (millis() - startTime >= interval)` inside `loop()`.

---

## Q4 — How does `analogWrite()` produce a PWM signal?

**Expected answer source:** `analogWrite` record (Analog I/O category)

`analogWrite(pin, value)` does not output a true analog voltage. It generates a **PWM (Pulse Width Modulation)** square wave at approximately 490 Hz (980 Hz on pins 5 and 6 of the Uno). The duty cycle is set by `value` (0 = always LOW, 255 = always HIGH, 128 = 50% on/off). It only works on PWM-capable pins: 3, 5, 6, 9, 10, 11 on Arduino Uno.

---

## Q5 — Why does my `analogRead()` give fluctuating values on an unconnected pin?

**Expected answer source:** `analogRead` record (Analog I/O category)

An unconnected analog pin acts as an antenna and picks up electromagnetic noise from the environment, the USB cable, nearby wires, and even your hand. The ADC samples this floating voltage and returns a seemingly random value between 0 and 1023. Always connect the pin to a signal source or pull it to GND/VCC before reading.

---

## Q6 — Can ArduinoMate tell me how to connect an HC-SR04 ultrasonic sensor to measure distance?

> ⚠️ **Intentionally unanswerable with the current Week 1 dataset.**

The HC-SR04 ultrasonic sensor is **not** covered in the ArduinoMate Week 1 knowledge base. The dataset contains only Arduino language reference functions (`digitalRead`, `analogWrite`, `millis`, etc.) — it does not include sensor wiring guides or project tutorials.

ArduinoMate cannot answer this question from stored data and will not fabricate an answer. This question is a planned addition for a future week when sensor documentation is ingested.

---

## Q7 — How do I send data to the Serial Monitor?

**Expected answer source:** `Serial.begin` and `Serial.print` records (Serial category)

Call `Serial.begin(9600)` (or any baud rate) inside `setup()` to initialise the port. Then use `Serial.print(value)` to send data without a newline, or `Serial.println(value)` to append `\r\n`. The Serial Monitor baud rate setting must exactly match the value passed to `Serial.begin()`, otherwise you will see garbage characters.

---

## Q8 — What is the common mistake with `attachInterrupt()`?

**Expected answer source:** `attachInterrupt` record (Interrupts category)

The ISR (Interrupt Service Routine) function must be very short and fast. You cannot call `delay()` inside an ISR because `delay()` relies on the timer interrupt that the ISR itself may be blocking. `millis()` will also stop incrementing inside an ISR. Any variable shared between the ISR and `loop()` must be declared `volatile` so the compiler does not optimise it away.

---

## Q9 — What is the difference between `map()` and `constrain()` in Arduino?

**Expected answer source:** `map` and `constrain` records (Math category)

`map(value, fromLow, fromHigh, toLow, toHigh)` re-scales a number from one range to another (e.g. 0–1023 → 0–180 for a servo). **It does not clamp the output** — a value outside `fromLow–fromHigh` will produce a result outside `toLow–toHigh`. `constrain(value, min, max)` clamps a value to stay within `[min, max]`. They are often used together: `constrain(map(analogRead(A0), 0, 1023, 0, 180), 0, 180)`.

---

## Q10 — How do I generate a random number in Arduino and avoid getting the same sequence every reset?

**Expected answer source:** `random` record (Math category)

`random(min, max)` returns a pseudo-random `long` where `max` is **excluded**. Because it uses a deterministic algorithm, it produces the **same sequence** after every power-on reset. To get a truly unpredictable sequence, seed it once in `setup()` with `randomSeed(analogRead(A0))` — the floating analog pin reads an unpredictable noise voltage, giving a different seed each time.

---

*Document version: Week 1 — Day 5*
