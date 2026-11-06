
# ArduinoMate Menu Program

while True:
    print("\n===== ARDUINOMATE MENU =====")
    print("1. About ArduinoMate")
    print("2. Sample Questions")
    print("3. Arduino Rule Check")
    print("0. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":
        print("\nArduinoMate helps beginners learn Arduino.")

    elif choice == "2":
        print("\nSample Questions:")
        print("1. What is Arduino?")
        print("2. What is a digital pin?")
        print("3. What is an LED?")

    elif choice == "3":
        pin = int(input("Enter Arduino pin number: "))

        if pin >= 0 and pin <= 13:
            print("Valid digital pin number for Arduino Uno.")
        else:
            print("Invalid digital pin number for Arduino Uno.")

    elif choice == "0":
        print("Thank you for using ArduinoMate!")
        break

    else:
        print("Invalid choice. Please try again.")
