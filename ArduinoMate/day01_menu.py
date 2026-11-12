"""
ArduinoMate - Day 1: Interactive Menu
---------------------------------------
Student  : Parth Dasharath Katore
Enroll   : 2124UCEM2079
Roll No  : 53

Demonstrates a while-loop driven menu with:
  Option 1 – About ArduinoMate
  Option 2 – Sample Arduino questions
  Option 3 – Arduino pin-number rule check (if/elif)
  Option 0 – Exit
"""

# ── Sample questions shown in Option 2 ───────────────────────────────────────
SAMPLE_QUESTIONS = [
    "What does pinMode() do in Arduino?",
    "How do I read a digital input with digitalRead()?",
    "What is the difference between delay() and millis()?",
    "How does analogWrite() produce a PWM signal?",
    "What happens if I call digitalRead() on an unconnected pin?",
    "How do I use Serial.begin() to start serial communication?",
]

# ── Menu loop ─────────────────────────────────────────────────────────────────
while True:
    print()
    print("=" * 44)
    print("       ARDUINOMATE MAIN MENU")
    print("=" * 44)
    print("  1. About ArduinoMate")
    print("  2. Sample Arduino Questions")
    print("  3. Arduino Pin Number Rule Check")
    print("  0. Exit")
    print("-" * 44)

    choice = input("Enter your choice: ").strip()

    if choice == "1":
        # ── Option 1: About ───────────────────────────────────────────────────
        print()
        print("┌─ About ArduinoMate ──────────────────────────┐")
        print("│                                               │")
        print("│  ArduinoMate is an AI-powered Arduino        │")
        print("│  learning assistant.  It helps students      │")
        print("│  understand Arduino functions, syntax,        │")
        print("│  electronics concepts, and common errors.    │")
        print("│                                               │")
        print("│  Knowledge base: Official Arduino Docs       │")
        print("│  github.com/arduino/reference-en             │")
        print("└───────────────────────────────────────────────┘")

    elif choice == "2":
        # ── Option 2: Sample questions ────────────────────────────────────────
        print()
        print("Sample Arduino questions you can ask ArduinoMate:")
        print()
        for i, q in enumerate(SAMPLE_QUESTIONS, start=1):
            print(f"  {i}. {q}")

    elif choice == "3":
        # ── Option 3: Pin number rule check ──────────────────────────────────
        print()
        pin_input = input("Enter an Arduino pin number to check: ").strip()

        try:
            pin = int(pin_input)
        except ValueError:
            print("  ✗ That is not a valid number. Please enter an integer.")
        else:
            # Arduino Uno: digital pins 0-13, PWM capable: 3,5,6,9,10,11
            # Analog pins A0-A5 (also usable as digital 14-19)
            PWM_PINS = {3, 5, 6, 9, 10, 11}

            if 0 <= pin <= 13:
                if pin in PWM_PINS:
                    print(f"  ✓ Pin {pin} is a valid digital pin on Arduino Uno.")
                    print(f"    It is also PWM-capable (use analogWrite).")
                elif pin in (0, 1):
                    print(f"  ✓ Pin {pin} is a valid digital pin.")
                    print(f"    Note: Pins 0 and 1 are shared with Serial TX/RX —")
                    print(f"    avoid using them while Serial communication is active.")
                else:
                    print(f"  ✓ Pin {pin} is a valid digital pin on Arduino Uno.")
                    print(f"    It is NOT PWM-capable; use it with digitalWrite only.")
            elif 14 <= pin <= 19:
                print(f"  ✓ Pin {pin} maps to analog pin A{pin - 14}.")
                print(f"    It can be used as a digital pin with pinMode/digitalRead/digitalWrite.")
            elif pin < 0:
                print(f"  ✗ Pin {pin} is invalid. Pin numbers cannot be negative.")
            else:
                print(f"  ✗ Pin {pin} is out of range for Arduino Uno (valid: 0–13 digital, 14–19 analog).")

    elif choice == "0":
        # ── Exit ──────────────────────────────────────────────────────────────
        print()
        print("Thank you for using ArduinoMate. Happy coding! 🚀")
        break

    else:
        print()
        print("  Invalid choice. Please enter 1, 2, 3, or 0.")
