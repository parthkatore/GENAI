
# Arduino Functions Reference - S1

records = [
    {
        "function_name": "pinMode",
        "category": "Digital I/O",
        "syntax": "pinMode(pin, mode)",
        "returns": "None",
        "common_gotcha": "Must be called before using a pin as INPUT or OUTPUT.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/digital-io/pinmode/"
    },
    {
        "function_name": "digitalRead",
        "category": "Digital I/O",
        "syntax": "digitalRead(pin)",
        "returns": "HIGH or LOW",
        "common_gotcha": "The pin should be configured as INPUT or INPUT_PULLUP.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/digital-io/digitalread/"
    },
    {
        "function_name": "digitalWrite",
        "category": "Digital I/O",
        "syntax": "digitalWrite(pin, value)",
        "returns": "None",
        "common_gotcha": "The pin should be configured as OUTPUT for normal output use.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/digital-io/digitalwrite/"
    },
    {
        "function_name": "analogRead",
        "category": "Analog I/O",
        "syntax": "analogRead(pin)",
        "returns": "Integer ADC reading",
        "common_gotcha": "The reading range depends on the board's ADC resolution.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/analog-io/analogread/"
    },
    {
        "function_name": "analogWrite",
        "category": "Analog I/O",
        "syntax": "analogWrite(pin, value)",
        "returns": "None",
        "common_gotcha": "It produces PWM on supported pins, not a true analog voltage.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/analog-io/analogwrite/"
    },
    {
        "function_name": "analogReference",
        "category": "Analog I/O",
        "syntax": "analogReference(type)",
        "returns": "None",
        "common_gotcha": "Available reference types depend on the board.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/analog-io/analogreference/"
    },
    {
        "function_name": "delay",
        "category": "Time",
        "syntax": "delay(ms)",
        "returns": "None",
        "common_gotcha": "Blocks normal program execution while waiting.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/time/delay/"
    },
    {
        "function_name": "delayMicroseconds",
        "category": "Time",
        "syntax": "delayMicroseconds(us)",
        "returns": "None",
        "common_gotcha": "Only suitable for relatively short delays; timing precision varies.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/time/delaymicroseconds/"
    },
    {
        "function_name": "millis",
        "category": "Time",
        "syntax": "millis()",
        "returns": "Unsigned long elapsed milliseconds",
        "common_gotcha": "The counter eventually wraps around; use unsigned subtraction for elapsed time.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/time/millis/"
    },
    {
        "function_name": "micros",
        "category": "Time",
        "syntax": "micros()",
        "returns": "Unsigned long elapsed microseconds",
        "common_gotcha": "Resolution and wraparound period vary by board.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/time/micros/"
    },
    {
        "function_name": "map",
        "category": "Math",
        "syntax": "map(value, fromLow, fromHigh, toLow, toHigh)",
        "returns": "Mapped long integer",
        "common_gotcha": "Does not constrain the input to the source range.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/math/map/"
    },
    {
        "function_name": "constrain",
        "category": "Math",
        "syntax": "constrain(value, min, max)",
        "returns": "Value limited to the specified range",
        "common_gotcha": "The minimum must not be greater than the maximum.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/math/constrain/"
    },
    {
        "function_name": "tone",
        "category": "Advanced I/O",
        "syntax": "tone(pin, frequency, duration)",
        "returns": "None",
        "common_gotcha": "Timer use and supported pins vary by board.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/advanced-io/tone/"
    },
    {
        "function_name": "noTone",
        "category": "Advanced I/O",
        "syntax": "noTone(pin)",
        "returns": "None",
        "common_gotcha": "Stops tone generation on the specified pin.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/advanced-io/notone/"
    },
    {
        "function_name": "pulseIn",
        "category": "Advanced I/O",
        "syntax": "pulseIn(pin, value, timeout)",
        "returns": "Pulse duration in microseconds, or 0 on timeout",
        "common_gotcha": "Can block while waiting for a pulse.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/advanced-io/pulsein/"
    },
    {
        "function_name": "Serial.begin",
        "category": "Serial",
        "syntax": "Serial.begin(baudRate)",
        "returns": "None",
        "common_gotcha": "The Serial Monitor baud rate should match the selected baud rate.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/communication/serial/begin/"
    },
    {
        "function_name": "Serial.print",
        "category": "Serial",
        "syntax": "Serial.print(value)",
        "returns": "Number of bytes written",
        "common_gotcha": "Does not automatically add a newline.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/communication/serial/print/"
    },
    {
        "function_name": "Serial.read",
        "category": "Serial",
        "syntax": "Serial.read()",
        "returns": "Next byte as an integer, or -1 if no data is available",
        "common_gotcha": "Check Serial.available() before reading.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/communication/serial/read/"
    },
    {
        "function_name": "attachInterrupt",
        "category": "Interrupts",
        "syntax": "attachInterrupt(digitalPinToInterrupt(pin), ISR, mode)",
        "returns": "None",
        "common_gotcha": "Keep the interrupt function short; avoid delay() and Serial calls inside it.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/external-interrupts/attachinterrupt/"
    },
    {
        "function_name": "random",
        "category": "Math",
        "syntax": "random(min, max)",
        "returns": "Pseudo-random long integer",
        "common_gotcha": "The upper limit is excluded from the result.",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/random-numbers/random/"
    }
]


# 1. Print all records
def print_all():
    print("\n===== ALL ARDUINO FUNCTIONS =====")

    for record in records:
        print("\nFunction:", record["function_name"])
        print("Category:", record["category"])
        print("Syntax:", record["syntax"])
        print("Returns:", record["returns"])
        print("Gotcha:", record["common_gotcha"])
        print("Source:", record["source_url"])


# 2. Search records by keyword
def search_records(keyword):
    print("\n===== SEARCH RESULTS =====")

    found = False

    for record in records:
        searchable_text = " ".join(str(value) for value in record.values())

        if keyword.lower() in searchable_text.lower():
            print(record["function_name"], "-", record["category"])
            found = True

    if not found:
        print("No matching records found.")


# 3. Count records per category
def count_categories():
    print("\n===== CATEGORY COUNTS =====")

    counts = {}

    for record in records:
        category = record["category"]
        counts[category] = counts.get(category, 0) + 1

    for category, count in counts.items():
        print(f"{category}: {count}")


# Main program
if __name__ == "__main__":
    print_all()

    keyword = input("\nEnter keyword to search: ")
    search_records(keyword)

    count_categories()
