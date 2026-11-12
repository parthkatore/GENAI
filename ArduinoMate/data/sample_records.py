"""
ArduinoMate - Day 2: Arduino Reference Records
------------------------------------------------
Student  : Parth Dasharath Katore
Enroll   : 2124UCEM2079
Roll No  : 53

Contains 20 Arduino functions as a list of dictionaries.
Each record has: function_name, category, syntax, returns,
                 common_gotcha, source_url

Also includes utility functions:
    print_all()       – print all records
    search_records()  – search by keyword
    count_categories() – count per category
"""

# ── 20 Arduino Function Records ───────────────────────────────────────────────
records = [
    {
        "function_name": "pinMode",
        "category": "Digital I/O",
        "syntax": "pinMode(pin, mode)",
        "returns": "None",
        "common_gotcha": "Must be called before using a pin as INPUT or OUTPUT. "
                         "Forgetting this causes unpredictable reads/writes.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/digital-io/pinmode/"
    },
    {
        "function_name": "digitalRead",
        "category": "Digital I/O",
        "syntax": "digitalRead(pin)",
        "returns": "HIGH or LOW (integer 1 or 0)",
        "common_gotcha": "Pin must be configured as INPUT or INPUT_PULLUP first. "
                         "An unconnected pin returns a random HIGH or LOW.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/digital-io/digitalread/"
    },
    {
        "function_name": "digitalWrite",
        "category": "Digital I/O",
        "syntax": "digitalWrite(pin, value)",
        "returns": "None",
        "common_gotcha": "The pin must be set as OUTPUT with pinMode() first. "
                         "Calling it on an INPUT pin enables/disables the internal pull-up.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/digital-io/digitalwrite/"
    },
    {
        "function_name": "analogRead",
        "category": "Analog I/O",
        "syntax": "analogRead(pin)",
        "returns": "Integer 0–1023 (10-bit ADC on Uno)",
        "common_gotcha": "Only works on analog pins (A0–A5 on Uno). "
                         "The range changes if analogReference() is changed.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/analog-io/analogread/"
    },
    {
        "function_name": "analogWrite",
        "category": "Analog I/O",
        "syntax": "analogWrite(pin, value)",
        "returns": "None",
        "common_gotcha": "Outputs PWM (not true analog). Only works on PWM-capable pins "
                         "(3, 5, 6, 9, 10, 11 on Uno). Value must be 0–255.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/analog-io/analogwrite/"
    },
    {
        "function_name": "analogReference",
        "category": "Analog I/O",
        "syntax": "analogReference(type)",
        "returns": "None",
        "common_gotcha": "Available reference types vary by board. "
                         "Applying a voltage higher than the selected reference can damage the MCU.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/analog-io/analogreference/"
    },
    {
        "function_name": "delay",
        "category": "Time",
        "syntax": "delay(ms)",
        "returns": "None",
        "common_gotcha": "Completely blocks all code (including interrupts serviced in loop) "
                         "while waiting. Use millis() for non-blocking timing instead.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/time/delay/"
    },
    {
        "function_name": "delayMicroseconds",
        "category": "Time",
        "syntax": "delayMicroseconds(us)",
        "returns": "None",
        "common_gotcha": "Accuracy degrades for values above ~16 383 µs. "
                         "Interrupts are disabled during the delay, affecting Serial.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/time/delaymicroseconds/"
    },
    {
        "function_name": "millis",
        "category": "Time",
        "syntax": "millis()",
        "returns": "unsigned long – milliseconds since the board started",
        "common_gotcha": "Wraps around to 0 after ~49.7 days. "
                         "Always use subtraction (millis() - startTime) to handle rollover safely.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/time/millis/"
    },
    {
        "function_name": "micros",
        "category": "Time",
        "syntax": "micros()",
        "returns": "unsigned long – microseconds since the board started",
        "common_gotcha": "Wraps around after ~70 minutes on 16 MHz boards. "
                         "Resolution is 4 µs on 16 MHz Uno.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/time/micros/"
    },
    {
        "function_name": "map",
        "category": "Math",
        "syntax": "map(value, fromLow, fromHigh, toLow, toHigh)",
        "returns": "long – the mapped value",
        "common_gotcha": "Does NOT constrain the output to the target range. "
                         "Values outside fromLow–fromHigh will produce out-of-range results. "
                         "Use constrain() together with map() if needed.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/math/map/"
    },
    {
        "function_name": "constrain",
        "category": "Math",
        "syntax": "constrain(value, min, max)",
        "returns": "value clamped to [min, max]",
        "common_gotcha": "min must be less than or equal to max. "
                         "Swapping them does not automatically fix it.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/math/constrain/"
    },
    {
        "function_name": "tone",
        "category": "Advanced I/O",
        "syntax": "tone(pin, frequency)  or  tone(pin, frequency, duration)",
        "returns": "None",
        "common_gotcha": "Uses a hardware timer, which can interfere with PWM on certain pins. "
                         "Only one tone can be generated at a time.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/advanced-io/tone/"
    },
    {
        "function_name": "noTone",
        "category": "Advanced I/O",
        "syntax": "noTone(pin)",
        "returns": "None",
        "common_gotcha": "Must be called on the same pin that tone() was started on. "
                         "If duration was specified in tone(), noTone() is called automatically.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/advanced-io/notone/"
    },
    {
        "function_name": "pulseIn",
        "category": "Advanced I/O",
        "syntax": "pulseIn(pin, value)  or  pulseIn(pin, value, timeout)",
        "returns": "unsigned long – pulse duration in microseconds; 0 on timeout",
        "common_gotcha": "Blocks execution while waiting for the pulse. "
                         "Default timeout is 1 second. Can miss events if used inside a busy loop.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/advanced-io/pulsein/"
    },
    {
        "function_name": "Serial.begin",
        "category": "Serial",
        "syntax": "Serial.begin(speed)  or  Serial.begin(speed, config)",
        "returns": "None",
        "common_gotcha": "Serial Monitor baud rate must match the value passed to Serial.begin(). "
                         "Common rates: 9600, 115200.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/communication/serial/begin/"
    },
    {
        "function_name": "Serial.print",
        "category": "Serial",
        "syntax": "Serial.print(value)  or  Serial.print(value, format)",
        "returns": "size_t – number of bytes written",
        "common_gotcha": "Does NOT append a newline. Use Serial.println() if you want a newline. "
                         "Printing floats truncates to 2 decimal places by default.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/communication/serial/print/"
    },
    {
        "function_name": "Serial.read",
        "category": "Serial",
        "syntax": "Serial.read()",
        "returns": "int – next byte as integer (0–255), or -1 if no data",
        "common_gotcha": "Always check Serial.available() > 0 before calling Serial.read() "
                         "to avoid reading -1 when the buffer is empty.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/communication/serial/read/"
    },
    {
        "function_name": "attachInterrupt",
        "category": "Interrupts",
        "syntax": "attachInterrupt(digitalPinToInterrupt(pin), ISR, mode)",
        "returns": "None",
        "common_gotcha": "Keep ISR functions very short and fast. "
                         "Do NOT use delay() or Serial inside an ISR. "
                         "Variables shared with the ISR must be declared volatile.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/external-interrupts/attachinterrupt/"
    },
    {
        "function_name": "random",
        "category": "Math",
        "syntax": "random(max)  or  random(min, max)",
        "returns": "long – pseudo-random number; upper bound (max) is excluded",
        "common_gotcha": "Produces the same sequence after each reset unless randomSeed() "
                         "is called first (e.g., randomSeed(analogRead(0))).",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/random-numbers/random/"
    }
]


# ── Utility Functions ─────────────────────────────────────────────────────────

def print_all():
    """Print every Arduino function record in a readable format."""
    print(f"\n{'='*55}")
    print(f"  ALL ARDUINO FUNCTIONS  ({len(records)} records)")
    print(f"{'='*55}")
    for i, rec in enumerate(records, start=1):
        print(f"\n[{i:02d}] {rec['function_name']}  ({rec['category']})")
        print(f"     Syntax  : {rec['syntax']}")
        print(f"     Returns : {rec['returns']}")
        print(f"     Gotcha  : {rec['common_gotcha']}")
        print(f"     Source  : {rec['source_url']}")


def search_records(keyword: str) -> list:
    """
    Search all records for a keyword (case-insensitive).

    Parameters
    ----------
    keyword : str
        The word or phrase to search for.

    Returns
    -------
    list of matching records
    """
    if not keyword or not keyword.strip():
        return []

    kw = keyword.strip().lower()
    matches = []

    for rec in records:
        # Combine all field values into one searchable text blob
        searchable = " ".join(str(v) for v in rec.values()).lower()
        if kw in searchable:
            matches.append(rec)

    return matches


def count_categories() -> dict:
    """
    Count how many functions belong to each category.

    Returns
    -------
    dict  { category_name: count }
    """
    counts: dict = {}
    for rec in records:
        cat = rec.get("category", "Unknown")
        counts[cat] = counts.get(cat, 0) + 1
    return counts


# ── Main (self-contained demo) ────────────────────────────────────────────────
if __name__ == "__main__":
    print_all()

    print(f"\n{'='*55}")
    print("  CATEGORY DISTRIBUTION")
    print(f"{'='*55}")
    for cat, cnt in count_categories().items():
        print(f"  {cat:<20} : {cnt} function(s)")

    print(f"\n{'='*55}")
    kw = input("Enter a keyword to search: ").strip()
    results = search_records(kw)
    if results:
        print(f"\nFound {len(results)} result(s):")
        for r in results:
            print(f"  → {r['function_name']}  [{r['category']}]")
    else:
        print("  No matching records found.")
