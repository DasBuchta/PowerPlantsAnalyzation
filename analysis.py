import sqlite3


def connect_db():
    return sqlite3.connect('powerplants.sqlite3')


if __name__ == "__main__":
    db = connect_db()
    cursor = db.cursor()

    # cursor.execute("""SELECT country, COUNT() FROM powerplants GROUP BY country""")
    cursor.execute("""SELECT name, primary_fuel FROM powerplants WHERE country='SVK'""")
    cursor.execute("""SELECT primary_fuel, SUM(generation_gwh_2013), SUM(generation_gwh_2019) 
                        FROM powerplants GROUP BY primary_fuel""")
    cursor.execute("""SELECT other_fuel1, SUM(generation_gwh_2013), SUM(generation_gwh_2019) 
                        FROM powerplants GROUP BY other_fuel1""")

    for row in cursor:
        print(row)

    db.close()
