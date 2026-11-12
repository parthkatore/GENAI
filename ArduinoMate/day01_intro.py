"""
ArduinoMate - Day 1: Project Introduction
------------------------------------------
Student  : Parth Dasharath Katore
Enroll   : 2124UCEM2079
Roll No  : 53

This script prints the ArduinoMate project card, greets the user,
and echoes back their Arduino question with a simple personalised reply.
"""

# ── Project Card Variables ────────────────────────────────────────────────────
product_name   = "ArduinoMate"
target_users   = "Arduino beginners, students, and hobbyists"
problem        = (
    "Beginners struggle to understand Arduino functions, syntax, "
    "and common programming errors without a quick, focused reference."
)
solution       = (
    "ArduinoMate provides an AI-powered knowledge base built from the "
    "official Arduino documentation so students can search, explore, "
    "and learn Arduino concepts instantly."
)
data_source    = "Official Arduino Reference (https://github.com/arduino/reference-en)"
version        = "1.0.0 – Week 1"

# ── Print Project Card ────────────────────────────────────────────────────────
print("=" * 60)
print(f"  {'ARDUINOMATE PROJECT CARD':^56}")
print("=" * 60)
print(f"  Product      : {product_name}")
print(f"  Target Users : {target_users}")
print(f"  Problem      : {problem}")
print(f"  Solution     : {solution}")
print(f"  Data Source  : {data_source}")
print(f"  Version      : {version}")
print("=" * 60)

# ── Personalised Greeting ─────────────────────────────────────────────────────
print()
name     = input("What is your name? ").strip()
question = input("What is your Arduino question? ").strip()

print()
print(f"Hello, {name}! 👋  Welcome to ArduinoMate.")
print()

if question:
    print(f"You asked: \"{question}\"")
    print()
    print(
        "Great question! ArduinoMate's knowledge base covers Arduino "
        "functions, syntax, and common gotchas. As the system grows, "
        "it will give you a smart, context-aware answer. Stay tuned!"
    )
else:
    print("No question entered. Feel free to ask anything about Arduino anytime!")

print()
print("─" * 60)
print("  Tip: Run  python day01_menu.py  to explore the full menu.")
print("─" * 60)
