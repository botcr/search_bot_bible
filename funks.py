import sqlite3
import datetime
import random
import time
from config import bot
from telebot import types

def get_current_msc_time() -> datetime:
    delta = datetime.timedelta(hours=3)
    return datetime.datetime.now(datetime.timezone.utc) + delta

def random_verse():
  while True:
    time_now = get_current_msc_time()
    #только днем и только 2 раза в день в случайное время
    if time_now.strftime('%H') >= '08' and time_now.strftime('%H') <= '22' and random.randint(1, 7) == 1:
          translete = 'NRT'
          with sqlite3.connect('users.db') as data:
            curs = data.cursor()
            last_rowid = curs.execute("""SELECT rowid FROM random_verses ORDER BY rowid DESC LIMIT 1;""").fetchone()[0]
            random_verse_data = curs.execute("""SELECT * FROM random_verses WHERE rowid == ?;""", (random.randint(1, last_rowid),)).fetchone()
          with sqlite3.connect(f'{translete}.SQLite3') as data1:
            curs = data1.cursor()
            text = curs.execute("""SELECT text FROM verses WHERE book_number == ? AND chapter == ? AND verse == ?;""", (random_verse_data[0], random_verse_data[1], random_verse_data[2])).fetchone()[0]
          random_verse_search_markup = types.InlineKeyboardMarkup(row_width=2)
          other_translete_but = types.InlineKeyboardButton(text='Другие переводы', callback_data=f'other_translete|{random_verse_data[0]}|{random_verse_data[1]}|{random_verse_data[2]}|{translete}')
          full_chapter_but= types.InlineKeyboardButton(text=f'Полный текст', callback_data=f'full_text|{random_verse_data[0]}|{random_verse_data[1]}|{random_verse_data[2]}|{translete}')
          random_verse_search_markup.add(other_translete_but, full_chapter_but)
          bot.send_message(477612946, f'{text} ({what_book(random_verse_data[0], translete)[0]} {random_verse_data[1]}:{random_verse_data[2]}) {translete}',reply_markup=random_verse_search_markup)
          bot.send_message(5272770503, f'{text} ({what_book(random_verse_data[0], translete)[0]} {random_verse_data[1]}:{random_verse_data[2]}) {translete}',reply_markup=random_verse_search_markup)
      
    time.sleep(3600)
      
def select_request(query):
  search_data = []
  search_text_parts = ''
  query_words_low = query.query.lower()
  query_words = query_words_low.split(' ')
  i = 0
  for word in query_words:
    final_word = f'%{word}%'
    search_data.append(final_word)
    if i >= 1:
      search_text_parts = search_text_parts + ' AND text LIKE LOWER(?)'
    i+=1
  search_text = f"""SELECT * FROM verses WHERE text_for_search LIKE LOWER(?){search_text_parts} ORDER BY rowid LIMIT 6 OFFSET ?;"""
  search_data.append(int(query.offset) if query.offset else 0)
  return search_text, search_data


def what_book(book, translete):
  #ищет название или номер книги, возвращает кортеж названий или число
  base_name = f'{translete}.SQLite3'
  with sqlite3.connect(base_name) as data:
      curs = data.cursor()
      if type(book) == int:
            return curs.execute("""SELECT short_name, long_name FROM books WHERE book_number == ?;""", (book,)).fetchone()
      elif type(book) == str:
            book_num = curs.execute("""SELECT book_number FROM books WHERE book_number == ?;""", (book,)).fetchone()
            return book_num[0]



def one_message_last_verse(book_number, chapter, verse_number, translete):
  print(book_number, chapter, verse_number, translete)
  base_name = f'{translete}.SQLite3'
  with sqlite3.connect(base_name) as data:
      curs = data.cursor()
      rowid = curs.execute("""SELECT rowid FROM verses WHERE book_number == ? AND chapter == ? AND verse == ?;""", (book_number, chapter, verse_number)).fetchone()[0]
      verses = curs.execute("""SELECT book_number, chapter, verse, text FROM verses WHERE rowid BETWEEN ? AND ? ORDER BY rowid DESC;""", (int(rowid)-60, int(rowid))).fetchall()
  return compil_1_message(verses, book_number, chapter, verse_number, translete, is_bold_main_verse=False, formation='reverse')


def one_message_middle_verse(book_number, chapter, verse_number, translete):
  base_name = f'{translete}.SQLite3'
  with sqlite3.connect(base_name) as data:
      curs = data.cursor()
      rowid = curs.execute("""SELECT rowid FROM verses WHERE book_number == ? AND chapter == ? AND verse == ?;""", (book_number, chapter, verse_number)).fetchone()[0]
      verses = curs.execute("""SELECT book_number, chapter, verse, text FROM verses WHERE rowid BETWEEN ? AND ?;""", (int(rowid)-10, int(rowid)+40)).fetchall()
  return compil_1_message(verses, book_number, chapter, verse_number, translete, is_bold_main_verse=True, formation='direct')
  
def one_message_first_verse(book_number, chapter, verse_number, translete):
  base_name = f'{translete}.SQLite3'
  with sqlite3.connect(base_name) as data:
      curs = data.cursor()
      rowid = curs.execute("""SELECT rowid FROM verses WHERE book_number == ? AND chapter == ? AND verse == ?;""", (book_number, chapter, verse_number)).fetchone()[0]
      verses = curs.execute("""SELECT book_number, chapter, verse, text FROM verses WHERE rowid BETWEEN ? AND ?;""", (int(rowid), int(rowid)+60)).fetchall()
  return compil_1_message(verses, book_number, chapter, verse_number, translete, is_bold_main_verse=False, formation='direct')

def compil_1_message(verses, book_number, chapter, verse_number, translete, is_bold_main_verse=False, formation='direct'):
  text = ''
  #чтобы глава ставилась в начале первого стиха только при прямом формировании текста
  if formation == 'direct':
    i=0; max_len=4060 
  elif formation == 'reverse':
    i=1; max_len=3900
  for verse in verses:
        local_book_number = verse[0]
        local_chapter = verse[1]
        local_verse_number = verse[2]
        verse_text = verse[3]
        if (local_verse_number == 1 and local_chapter == 1) or i == 0:
          #Новая книга
          new_chapter_or_book = f'\n*{what_book(int(local_book_number), translete)[1]}*\n*Глава {local_chapter}*\n\n'
        elif local_verse_number == 1 and local_chapter != 1:
          #Новая глава
          new_chapter_or_book = f'\n*Глава {local_chapter}*\n\n'
        else:
          new_chapter_or_book = ''
        #выделение главного стиха жирным
        if int(local_book_number) == int(book_number) and int(local_chapter) == int(chapter) and int(local_verse_number) == int(verse_number) and is_bold_main_verse == True:
          verse_text = f" *{verse_text}*"
        else:
          verse_text = f" {verse_text}"
        verse_number_for_text = f"_{local_verse_number}_"
        new_addition = f'{new_chapter_or_book}{verse_number_for_text}{verse_text}\n'
        if len(text) + len(new_addition) <= max_len:
          if formation =='direct':
            text = text + new_addition
          elif formation =='reverse':
            text = new_addition + text
          last_verse = verse
        else:
          break
        i+=1
  #дальше компелируем какие стихи были выбраны и отправляем
  #Название книги на самый верх
  if formation =='reverse' and (local_verse_number != 1 or local_chapter != 1):
    new_chapter_or_book = f'\n*{what_book(int(local_book_number), translete)[1]}*\n*Глава {local_chapter}*\n\n'
  else:
    new_chapter_or_book = ''
  if formation =='direct':
    first_verse = verses[0]
  elif formation =='reverse':
    first_verse = last_verse
    last_verse = verses[0]
    print(first_verse, last_verse)
  
  if last_verse[0] != first_verse[0]:
    second_book = f' {what_book(int(last_verse[0]), translete)[0]}'
  else:
    second_book = ''
  if last_verse[1] != first_verse[1] or last_verse[0] != first_verse[0]:
    second_chapter = f' {last_verse[1]}:'
    defis = ' -'
  else:
    second_chapter = ''
    defis = '-'
  final_numbers = f'({what_book(int(first_verse[0]), translete)[0]} {first_verse[1]}:{first_verse[2]}{defis}{second_book}{second_chapter}{last_verse[2]}) {translete}'
  text = new_chapter_or_book + text + final_numbers
  return text, first_verse, last_verse
    
def base_work(base_name):
  import re
  with sqlite3.connect(base_name) as data:
    curs = data.cursor()
    curs.execute("""ALTER TABLE verses ADD COLUMN text_for_search TEXT;""")
    verses = curs.execute("""SELECT * FROM verses;""").fetchall()
    for verse in verses:
      #надо записывать все что удаляем из базы
      verse_text = verse[3]
      deleted_text = re.findall(r'<S>([^<>]+)</S>|<([^<>]+)>|\[([^\[\]]+)\]', verse_text)
      #не включает [] и <>
      with open('base_change_log.txt', 'a') as file:
                  file.write(f"Удалил {deleted_text} из базы {base_name}  {get_current_msc_time()}\n")
      verse_text = re.sub(r'<S>([^<>]+)</S>', '', verse_text)
      verse_text = re.sub(r'<([^<>]+)>|\[([^\[\]]+)\]', '', verse_text)
      verse_text = verse_text.replace('  ',' ')
      low_verse_text = verse_text.lower()
      curs.execute("""UPDATE verses SET text = ?, text_for_search = ? WHERE book_number == ? AND chapter == ? AND verse == ?;""", (verse_text, low_verse_text, verse[0], verse[1], verse[2]))
    print('Закончил')

#base_work('RST.SQLite3')
