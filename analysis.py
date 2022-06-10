import sqlite3


def connect_db():
    return sqlite3.connect('powerplants.sqlite3')


if __name__ == "__main__":
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""SELECT country, COUNT() as pocet FROM powerplants GROUP BY country LIMIT 10""")
    print("Number of powerplants of first 10 countries sorted alphabetically")
    for row in cursor:
        print(f"{row[0]:5} {row[1]:>5}")

    print(end="\n\n")

    cursor.execute("""SELECT name, primary_fuel, capacity_mw FROM powerplants WHERE country='SVK'""")
    print(f"{'Name of powerplant':65} {'Primary fuel':15} Capacity in megawatts".upper())
    for row in cursor:
        print(f"{row[0]:70} {row[1]:<10} {float(row[2]):10.2f}")

    print(end="\n\n")

    cursor.execute("""SELECT primary_fuel, SUM(capacity_mw) as capacity_sum, COUNT(), AVG(capacity_mw)
                        FROM powerplants GROUP BY primary_fuel ORDER BY capacity_sum DESC""")
    print(f"Primary fuel\tTotal capacity in megawatts\tNumber of powerplants\tAverage capacity".upper())
    for row in cursor:
        print(f"{row[0]:15} {round(row[1]):>20} {round(row[2]):>20} {round(row[3]):>20}")

    db.close()
