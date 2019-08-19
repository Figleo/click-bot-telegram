import asyncio
import io
import logging
import threading
import time

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InputMediaDocument, KeyboardButton, ReplyKeyboardMarkup
from urllib.request import urlopen
import json
import sqlite3
#--------------------Настройки бота-------------------------

# Ваш токен от BotFather
TOKEN = '960170163:AAH4d9lcEKPIgoMPuA2BWVq7Dq1uFZ5bv-0'

# Логирование
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Ваш айди аккаунта администратора и айди сообщения где хранится файл с данными
admin_id=852450369
config_id=15230
file_id='BQADAgAD6AoAAp1SuEpafJZF0gmlUBYE'


conn = sqlite3.connect(":memory:")  # или :memory: чтобы сохранить в RAM
cursor = conn.cursor()


# #--------------------Получение данных-------------------------
async def get_data():
    # Пересылаем сообщение в данными от админа к админу
    forward_data = await bot.forward_message(admin_id, admin_id, config_id)

    # Получаем путь к файлу, который переслали
    file_data = await bot.get_file(forward_data.document.file_id)

    # Получаем файл по url
    file_url_data = bot.get_file_url(file_data.file_path)

    # Считываем данные с файла
    json_file= urlopen(file_url_data).read()

    # Переводим данные из json в словарь и возвращаем
    return json.loads(json_file)


#--------------------Сохранение данных-------------------------
async def save_data():
    t0=time.time()
    sql = "SELECT * FROM users "
    cursor.execute(sql)
    data = cursor.fetchall()  # or use fetchone()
    try:
        # Переводим словарь в строку
        str_data=json.dumps(data)

        # Обноваляем наш файл с данными
        await bot.edit_message_media(InputMediaDocument(io.StringIO(str_data)), admin_id, config_id)

    except Exception as ex:
        print(ex)
    print('i save')
    print( time.time()-t0)

#--------------------Метод при нажатии start-------------------------
@dp.message_handler(commands='start')
async def start(message: types.Message):
    # Добавляем нового пользователя
    sql_select = "SELECT * FROM users where chatid={}".format(message.chat.id)
    sql_insert = "INSERT INTO users VALUES ({}, '{}', {},{})".format(message.chat.id,message.chat.first_name, 0, 0)
    try:
        cursor.execute(sql_select)
        data = cursor.fetchone()
        if data is None:
            cursor.execute(sql_insert)
            conn.commit()
            await save_data()
    except Exception:
        data = await get_data()
        cursor.execute("CREATE TABLE users (chatid INTEGER , name TEXT, click INTEGER, state INTEGER)")
        cursor.executemany("INSERT INTO users VALUES (?,?,?,?)", data)
        conn.commit()
        cursor.execute(sql_select)
        data = cursor.fetchone()
        if data is  None:
            cursor.execute(sql_insert)
            conn.commit()
            await save_data()
        # Создаем кнопки
    button = KeyboardButton('Клик')
    button2 = KeyboardButton('Рейтинг')
    # Добавляем
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add(button).add(button2)
    # Отправляем сообщение с кнопкой
    await bot.send_message(message.chat.id,'Приветствую {}'.format(message.chat.first_name),reply_markup=kb)



#--------------------Основная логика бота-------------------------
@dp.message_handler()
async def main_logic(message: types.Message):

    t0=time.time()
# Логика для администратора
    if message.text == 'admin':
        cursor.execute("CREATE TABLE users (chatid INTEGER , name TEXT, click INTEGER, state INTEGER)")
        cursor.execute("INSERT INTO users VALUES (1234, 'eee', 1,0)")
        conn.commit()
        sql = "SELECT * FROM users "
        cursor.execute(sql)
        data = cursor.fetchall()
        str_data = json.dumps(data)
        await bot.send_document(message.chat.id, io.StringIO(str_data))
        await bot.send_message(message.chat.id, 'admin_id = {}'.format(message.chat.id))
        await bot.send_message(message.chat.id, 'config_id = {}'.format(message.message_id+1))


# Логика для пользователя
# Получаем данные от телеграма
    try:
        sql = "SELECT * FROM users where chatid={}".format(message.chat.id)
        cursor.execute(sql)
        data = cursor.fetchone()  # or use fetchone()
    except Exception:
        data = await get_data()
        cursor.execute("CREATE TABLE users (chatid INTEGER , name TEXT, click INTEGER, state INTEGER)")
        cursor.executemany("INSERT INTO users VALUES (?,?,?,?)", data)
        conn.commit()
        sql = "SELECT * FROM users where chatid={}".format(message.chat.id)
        cursor.execute(sql)
        data = cursor.fetchone()  # or use fetchone()


    #При нажатии кнопки клик увеличиваем значение click на один и сохраняем
    if data is not None:
        if message.text == 'Клик':
            sql = "UPDATE users SET click = {} WHERE chatid = {}".format(data[2]+1,message.chat.id)
            cursor.execute(sql)
            conn.commit()
            await bot.send_message(message.chat.id, 'Кликов: {} 🏆'.format(data[2]+1))


        # При нажатии кнопки Рейтинг выводим пользоваителю топ 10
        if message.text == 'Рейтинг':
            sql = "SELECT * FROM users ORDER BY click DESC LIMIT 15"
            cursor.execute(sql)
            newlist = cursor.fetchall()  # or use fetchone()
            sql_count = "SELECT COUNT(chatid) FROM users"
            cursor.execute(sql_count)
            count=cursor.fetchone()
            rating='Всего: {}\n'.format(count[0])
            i=1
            for user in newlist:
                rating=rating+str(i)+': '+user[1]+' - '+str(user[2])+'🏆\n'
                i+=1
            await bot.send_message(message.chat.id, rating)

    else:
        await bot.send_message(message.chat.id, 'Вы не разерстрирвоаны')

    print( time.time()-t0)






def timer_start():
    threading.Timer(30.0, timer_start).start()
    try:
        asyncio.run_coroutine_threadsafe(save_data(),bot.loop)
    except Exception as exc:
        pass

#--------------------Запуск бота-------------------------
if __name__ == '__main__':
    timer_start()
    executor.start_polling(dp, skip_updates=True)