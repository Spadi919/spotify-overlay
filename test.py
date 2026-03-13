import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="spotify_api",
    charset="utf8mb4",      
    use_unicode=True        
)

cursor = db.cursor()


sql = "select song_name from history order by id desc limit 1;"

cursor.execute(sql)

row = cursor.fetchone()


last_played = row[0]
print(last_played)
print(type(last_played))

print(last_played)

if last_played == "Vivarium":
    print("ado")
else:
    print("no golden ratio :(")