
# ArduinoMate Command Line Interface

from app.records import (
    load_records,
    search,
    count_by,
    get_by_id
)


def main():

    while True:

        print("\n===== ARDUINOMATE REFERENCE LIBRARY =====")
        print("1. Display all Arduino functions")
        print("2. Search Arduino function")
        print("3. Count functions by category")
        print("4. Find function by ID")
        print("0. Exit")

        choice = input("\nEnter your choice: ")

        if choice == "1":

            for index, record in enumerate(load_records(), start=1):
                print(f"\nID: {index}")
                print("Function:", record["function_name"])
                print("Category:", record["category"])
                print("Syntax:", record["syntax"])
                print("Returns:", record["returns"])
                print("Gotcha:", record["common_gotcha"])
                print("Source:", record["source_url"])

        elif choice == "2":

            keyword = input("Enter search keyword: ")
            results = search(keyword)

            if results:
                for record in results:
                    print(
                        record["function_name"],
                        "-",
                        record["category"]
                    )
            else:
                print("No records found.")

        elif choice == "3":

            counts = count_by()

            print("\nCategory Counts:")

            for category, total in counts.items():
                print(f"{category}: {total}")

        elif choice == "4":

            record_id = int(input("Enter record ID (1-20): "))
            record = get_by_id(record_id)

            if record:
                print("\nFunction:", record["function_name"])
                print("Syntax:", record["syntax"])
                print("Returns:", record["returns"])
                print("Gotcha:", record["common_gotcha"])
                print("Source:", record["source_url"])
            else:
                print("Record not found.")

        elif choice == "0":

            print("Thank you for using ArduinoMate!")
            break

        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
