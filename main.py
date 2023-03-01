import telebot
from telebot import types
from config import *
import sqlite3
import re
from loguru import logger
import funks
import table_create
from loguru import logger
import threading


# логи


logger.add("debug.log", format="{time} {level} Forder{message}", level="DEBUG", rotation="190 MB", compression="zip")

t1 = threading.Thread(target=funks.random_verse)
t1.start()
        
def registration(query):
  with sqlite3.connect('users.db') as data:
          curs = data.cursor()
          curs.execute("""INSERT INTO users (user_id, first_name, last_name, username, language_code) VALUES (?, ?, ?, ?, ?)""",
                             (query.from_user.id, query.from_user.first_name, query.from_user.last_name, query.from_user.username, query.from_user.language_code))
          curs.execute("""INSERT INTO bible_translations (user_id) VALUES (?)""",
                             (query.from_user.id,))

  #каждый  раз посе отправки результатов мы получаем новый запрос и нужно понимать, новый это запрос или прокркутка, а если прокрутка, то подошел ли к концу перевод или мы продолжаем с ним
@bot.inline_handler(func=lambda query: len(query.query) > 0)
def query_text(query, is_again = None):
  try:
    print(query.offset == '')
    #узнаем какой конкретно перевод нам нужен сейчас
    with sqlite3.connect('users.db') as data:
          curs = data.cursor()
          user_setting = curs.execute("""SELECT * FROM bible_translations WHERE user_id = (?)""", (query.from_user.id,)).fetchone()
          # если нет записи то регистрируем
          if user_setting is None:
            registration(query)
          # если это новый поиск то сбрасываем счетчик переводов
          if query.offset == '' and is_again == None:
            user_setting = curs.execute("""UPDATE bible_translations SET count = 3, was_sended = 0 WHERE user_id == ? RETURNING *""", (query.from_user.id,)).fetchone()
    offset = int(query.offset) if query.offset else 0
    print(user_setting[1], len(user_setting))
    if user_setting[1] >= len(user_setting):
      return None
    base_name = f'{user_setting[user_setting[1]]}.SQLite3'
    print(user_setting)
    # если счетчик превысил количество переводов, то тормозимся
    
    # делаем запрос в бд и находим 6 запросов если есть, при этом нужно нам только 5, но если есть 6ой то мы понимаем, что этот перевод еще не исчерпан
    with sqlite3.connect(base_name) as data:
        curs = data.cursor()
        w = funks.select_request(query)
        curs.execute(w[0], w[1])
        verses = curs.fetchall()
        print(base_name, verses)
      # если перевод исчерпал себя, второе условие условно и оно позволяет выйти за границы нужного числа переводов, чтобы ему не позволить нужно дописать -1
    

    with sqlite3.connect('users.db') as data:
        curs = data.cursor()
        if len(verses) < 5 and user_setting[1] < len(user_setting):
          curs.execute("""UPDATE bible_translations SET count = count + 1 WHERE user_id == ?""", (query.from_user.id,))
          #если перевод исчерпал себя и это последний перевод то не даем офсет чтобы небыло ошибок
        if len(verses) < 6 and user_setting[1] < len(user_setting)-1:
          m_next_offset = str(0)
        else:
          m_next_offset = ''
        
         #если что-то нашел то отмечаем это в базе чтобы не показал что ничего не найдено
        if len(verses) > 0:
          curs.execute("""UPDATE bible_translations SET was_sended = 1 WHERE user_id == ?""", (query.from_user.id,))
        #если ничего не найдено пишем об этом
        
    if len(verses) > 0:
      first_verse = verses[0]
      first_book = funks.what_book(first_verse[0], user_setting[user_setting[1]])
      first_verses_search_markup = types.InlineKeyboardMarkup(row_width=2)
      other_translete_but = types.InlineKeyboardButton(text='Другие переводы', callback_data=f'other_translete|{first_verse[0]}|{first_verse[1]}|{first_verse[2]}|{user_setting[user_setting[1]]}')
      full_chapter_but= types.InlineKeyboardButton(text=f'Полный текст', callback_data=f'full_text|{first_verse[0]}|{first_verse[1]}|{first_verse[2]}|{user_setting[user_setting[1]]}')
      first_verses_search_markup.add(other_translete_but, full_chapter_but)
      if int(first_verse[0]) < 465:
        first_photo = old_testament
      elif int(first_verse[0]) > 465:
        first_photo = new_testament
      first = types.InlineQueryResultArticle(
              id='{!s} {!s}:{!s}'.format(first_verse[0], first_verse[1], first_verse[2]), title="{!s} {!s}:{!s} {!s}".format(first_book[1], first_verse[1], first_verse[2], user_setting[user_setting[1]]),
              description='{!s}'.format(first_verse[3]),
              input_message_content=types.InputTextMessageContent(
              message_text="{!s}  ({!s} {!s}:{!s}) {!s}".format(first_verse[3], first_book[0], first_verse[1], first_verse[2], user_setting[user_setting[1]])), thumb_url=first_photo, thumb_width=48, thumb_height=48, reply_markup=first_verses_search_markup)
    elif len(verses) == 0 and offset == 0 and user_setting[1] >= len(user_setting)-1 and user_setting[2] == 0:
      nothing = types.InlineQueryResultArticle(
              id='nothing', title="Простите, ничего не найдено",
              # Описание отображается в подсказке,
              # message_text - то, что будет отправлено в виде сообщения
              description='Простите, ничего не найдено',
              input_message_content=types.InputTextMessageContent(
              message_text="Простите, ничего не найдено"))
      bot.answer_inline_query(query.id, [nothing, ])
      return None
    elif user_setting[1] < len(user_setting):
      query_text(query, is_again = 1)
      return None
    if len(verses) >= 2:
      second_verse = verses[1]
      second_book = funks.what_book(second_verse[0], user_setting[user_setting[1]])
      second_verses_search_markup = types.InlineKeyboardMarkup(row_width=2)
      other_translete_but = types.InlineKeyboardButton(text='Другие переводы', callback_data=f'other_translete|{second_verse[0]}|{second_verse[1]}|{second_verse[2]}|{user_setting[user_setting[1]]}')
      full_chapter_but= types.InlineKeyboardButton(text=f'Полный текст', callback_data=f'full_text|{second_verse[0]}|{second_verse[1]}|{second_verse[2]}|{user_setting[user_setting[1]]}')
      second_verses_search_markup.add(other_translete_but, full_chapter_but)
      if int(second_verse[0]) < 465:
        second_photo = old_testament
      elif int(second_verse[0]) > 465:
        second_photo = new_testament
      second = types.InlineQueryResultArticle(
              id='{!s} {!s}:{!s}'.format(second_verse[0], second_verse[1], second_verse[2]), title="{!s} {!s}:{!s} {!s}".format(second_book[1], second_verse[1], second_verse[2], user_setting[user_setting[1]]),
              description='{!s}'.format(second_verse[3]),
              input_message_content=types.InputTextMessageContent(
             message_text="{!s}  ({!s} {!s}:{!s}) {!s}".format(second_verse[3], second_book[0], second_verse[1], second_verse[2], user_setting[user_setting[1]])), thumb_url=second_photo, thumb_width=48, thumb_height=48, reply_markup=second_verses_search_markup)
    else:
      #все оффсеты нулевые чтобы дать понять что перевод себя исчерпал кроме одного внизу
      bot.answer_inline_query(query.id, [first, ], next_offset=m_next_offset)
      print('1 after send')
      return None
    if len(verses) >= 3:
      third_verse = verses[2]
      third_book = funks.what_book(third_verse[0], user_setting[user_setting[1]])
      third_verses_search_markup = types.InlineKeyboardMarkup(row_width=2)
      other_translete_but = types.InlineKeyboardButton(text='Другие переводы', callback_data=f'other_translete|{third_verse[0]}|{third_verse[1]}|{third_verse[2]}|{user_setting[user_setting[1]]}')
      full_chapter_but= types.InlineKeyboardButton(text=f'Полный текст', callback_data=f'full_text|{third_verse[0]}|{third_verse[1]}|{third_verse[2]}|{user_setting[user_setting[1]]}')
      third_verses_search_markup.add(other_translete_but, full_chapter_but)
      if int(third_verse[0]) < 465:
        third_photo = old_testament
      elif int(third_verse[0]) > 465:
        third_photo = new_testament
      third = types.InlineQueryResultArticle(
              id='{!s} {!s}:{!s}'.format(third_verse[0], third_verse[1], third_verse[2]), title="{!s} {!s}:{!s} {!s}".format(third_book[1], third_verse[1], third_verse[2], user_setting[user_setting[1]]),
              description='{!s}'.format(third_verse[3]),
              input_message_content=types.InputTextMessageContent(
              message_text="{!s}  ({!s} {!s}:{!s}) {!s}".format(third_verse[3], third_book[0], third_verse[1], third_verse[2], user_setting[user_setting[1]])), thumb_url=third_photo, thumb_width=48, thumb_height=48, reply_markup=third_verses_search_markup)
    else:
        bot.answer_inline_query(query.id, [first, second], next_offset=m_next_offset)
        return None
    if len(verses) >= 4:
      fourth_verse = verses[3]
      fourth_book = funks.what_book(fourth_verse[0], user_setting[user_setting[1]])
      fourth_verses_search_markup = types.InlineKeyboardMarkup(row_width=2)
      other_translete_but = types.InlineKeyboardButton(text='Другие переводы', callback_data=f'other_translete|{fourth_verse[0]}|{fourth_verse[1]}|{fourth_verse[2]}|{user_setting[user_setting[1]]}')
      full_chapter_but= types.InlineKeyboardButton(text=f'Полный текст', callback_data=f'full_text|{fourth_verse[0]}|{fourth_verse[1]}|{fourth_verse[2]}|{user_setting[user_setting[1]]}')
      fourth_verses_search_markup.add(other_translete_but, full_chapter_but)
      if int(fourth_verse[0]) < 465:
        fourth_photo = old_testament
      elif int(fourth_verse[0]) > 465:
        fourth_photo = new_testament
      fourth = types.InlineQueryResultArticle(
              id='{!s} {!s} {!s}'.format(fourth_verse[0], fourth_verse[1], fourth_verse[2]), title="{!s} {!s}:{!s} {!s}".format(fourth_book[1], fourth_verse[1], fourth_verse[2], user_setting[user_setting[1]]),
              description='{!s}'.format(fourth_verse[3]),
              input_message_content=types.InputTextMessageContent(
              message_text="{!s}  ({!s} {!s}:{!s}) {!s}".format(fourth_verse[3], fourth_book[0], fourth_verse[1], fourth_verse[2], user_setting[user_setting[1]])), thumb_url=fourth_photo, thumb_width=48, thumb_height=48, reply_markup=fourth_verses_search_markup)
    else:
          bot.answer_inline_query(query.id, [first, second, third], next_offset=m_next_offset)
          return None
    if len(verses) >= 5:
      fifth_verse = verses[4]
      fifth_book = funks.what_book(fifth_verse[0], user_setting[user_setting[1]])
      fifth_verses_search_markup = types.InlineKeyboardMarkup(row_width=2)
      other_translete_but = types.InlineKeyboardButton(text='Другие переводы', callback_data=f'other_translete|{fifth_verse[0]}|{fifth_verse[1]}|{fifth_verse[2]}|{user_setting[user_setting[1]]}')
      full_chapter_but= types.InlineKeyboardButton(text=f'Полный текст', callback_data=f'full_text|{fifth_verse[0]}|{fifth_verse[1]}|{fifth_verse[2]}|{user_setting[user_setting[1]]}')
      fifth_verses_search_markup.add(other_translete_but, full_chapter_but)
      if int(fifth_verse[0]) < 465:
        fifth_photo = old_testament
      elif int(fifth_verse[0]) > 465:
        fifth_photo = new_testament
      fifth = types.InlineQueryResultArticle(
              id='{!s} {!s} {!s}'.format(fifth_verse[0], fifth_verse[1], fifth_verse[2]), title="{!s} {!s}:{!s} {!s}".format(fifth_book[1], fifth_verse[1], fifth_verse[2], user_setting[user_setting[1]]),
              description='{!s}'.format(fifth_verse[3]),
              input_message_content=types.InputTextMessageContent(
              message_text="{!s}  ({!s} {!s}:{!s}) {!s}".format(fifth_verse[3], fifth_book[0], fifth_verse[1], fifth_verse[2], user_setting[user_setting[1]])), thumb_url=fifth_photo, thumb_width=48, thumb_height=48, reply_markup=fifth_verses_search_markup)
      #только если найдено больше 5 результатов, оффсет 5 потому что это значит что перевод не исчерпан
      if len(verses) > 5:
        m_next_offset = str(offset + 5)
      elif len(verses) == 5:
        with sqlite3.connect('users.db') as data:
          curs = data.cursor()
          curs.execute("""UPDATE bible_translations SET count = count + 1 WHERE user_id == ?""", (query.from_user.id,))
      bot.answer_inline_query(query.id, [first, second, third, fourth, fifth], next_offset=m_next_offset)
      return None
    else:
            m_next_offset = str(0)
            bot.answer_inline_query(query.id, [first, second, third, fourth], next_offset=m_next_offset)
            return None
  except Exception:
    logger.exception('-')
  

@bot.callback_query_handler(func=lambda callback: callback.data)
def all_callback_funk(callback):
  print(callback)
  verse_data = callback.data.split('|')
  book_number = verse_data[1]
  chapter = verse_data[2]
  verse_number = verse_data[3]
  translete = verse_data[4]
  if callback.data == 'other_translete':
    bot.answer_callback_query(callback.id, 'Перевод не ��айден')
    return None
  #сюда входят все изменения текста
  elif 'text' in callback.data:
    if 'full_text' in callback.data:
      text = funks.one_message_middle_verse(book_number, chapter, verse_number, translete)
    elif '⏩' in callback.data:
      text = funks.one_message_first_verse(book_number, chapter, verse_number, translete)
    elif '⏪' in callback.data:
      text = funks.one_message_last_verse(book_number, chapter, verse_number, translete)
    last_used_verse = text[2]
    first_verse = text[1]
    text_message_markup = types.InlineKeyboardMarkup(row_width=3)
    text_forward = types.InlineKeyboardButton(text='⏩', callback_data=f'text⏩|{last_used_verse[0]}|{last_used_verse[1]}|{last_used_verse[2]}|{translete}')
    other_translete_but = types.InlineKeyboardButton(text='Другие переводы', callback_data=f'other_translete_big_text|{first_verse[0]}|{first_verse[1]}|{first_verse[2]}|{translete}')
    text_back = types.InlineKeyboardButton(text='⏪', callback_data=f'text⏪|{first_verse[0]}|{first_verse[1]}|{first_verse[2]}|{translete}')
    text_message_markup.add(text_back, other_translete_but, text_forward)
    if callback.inline_message_id != None:
      bot.edit_message_text(text=text[0], inline_message_id=callback.inline_message_id, parse_mode='MARKDOWN', reply_markup=text_message_markup)
    else:
      bot.edit_message_text(text=text[0], chat_id=callback.from_user.id, message_id=callback.message.id, parse_mode='MARKDOWN', reply_markup=text_message_markup)

bot.infinity_polling()

# logger.exception('polling')
