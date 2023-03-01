import sqlite3

with sqlite3.connect('users.db', timeout=15000) as data:
            curs = data.cursor()
            curs.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id TEXT NOT NULL PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            language_code TEXT
            )""")
  
            curs.execute("""CREATE TABLE IF NOT EXISTS bible_translations (
            user_id TEXT NOT NULL PRIMARY KEY,
            count INTEGER DEFAULT 3,
            was_sended INTEGER DEFAULT 0,
            first TEXT DEFAULT RST,
            second TEXT DEFAULT NRT,
            third TEXT DEFAULT РБО
            )""")
    
            #curs.execute("""DROP TABLE random_verses""")
            curs.execute("""CREATE TABLE IF NOT EXISTS random_verses (
            book_number INTEGER NOT NULL,
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL
            )""")
