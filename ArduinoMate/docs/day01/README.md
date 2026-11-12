# Day 1 — Project Setup and Python Fundamentals

**Student:** Parth Dasharath Katore | Enroll: 2124UCEM2079 | Roll: 53  
**Status:** ✅ Complete

---

## Objective

Set up the ArduinoMate project, understand the problem being solved, and practise core Python fundamentals: variables, f-strings, `input()`, `while` loops, and `if/elif/else` logic.

---

## Tasks Completed

- [x] Defined the ArduinoMate project card (product, users, problem, solution, data source)
- [x] Created `day01_intro.py` — prints the project card, greets the user by name, echoes their Arduino question
- [x] Created `day01_menu.py` — interactive 4-option menu with while loop and pin-rule checker
- [x] Updated `README.md` with full project description

---

## Files Created / Modified

| File | Action | Description |
|------|--------|-------------|
| `day01_intro.py` | Created | Project card + personalised greeting |
| `day01_menu.py` | Created | Menu with About / Questions / Pin Check / Exit |
| `README.md` | Updated | Full ArduinoMate project documentation |

---

## Concepts Learned

- Variables and f-strings for readable output
- `input()` for interactive user prompts
- `while True` loop with `break` for menu-driven programs
- `if / elif / else` for branching logic
- Structuring a Python script with a clear entry point

---

## Technologies Used

- Python 3.13 (built-in only — no external libraries)

---

## Commands to Run

```bash
# Navigate into the project
cd ArduinoMate

# Run the intro script
python day01_intro.py

# Run the menu
python day01_menu.py
```

---

## Sample Output — `day01_intro.py`

```
============================================================
              ARDUINOMATE PROJECT CARD
============================================================
  Product      : ArduinoMate
  Target Users : Arduino beginners, students, and hobbyists
  Problem      : Beginners struggle to understand Arduino functions ...
  Solution     : ArduinoMate provides an AI-powered knowledge base ...
  Data Source  : Official Arduino Reference (https://github.com/arduino/reference-en)
  Version      : 1.0.0 – Week 1
============================================================

What is your name? Parth
What is your Arduino question? What does pinMode do?

Hello, Parth! 👋  Welcome to ArduinoMate.

You asked: "What does pinMode do?"
ArduinoMate's knowledge base covers Arduino functions ...
```

---

## Sample Output — `day01_menu.py` (Option 3)

```
============================================
       ARDUINOMATE MAIN MENU
============================================
  1. About ArduinoMate
  2. Sample Arduino Questions
  3. Arduino Pin Number Rule Check
  0. Exit
--------------------------------------------
Enter your choice: 3

Enter an Arduino pin number to check: 6
  ✓ Pin 6 is a valid digital pin on Arduino Uno.
    It is also PWM-capable (use analogWrite).
```

---

## Completion Status

Day 1 is fully complete. All scripts run without errors.
