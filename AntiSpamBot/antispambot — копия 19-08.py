import config
import telebot
from datetime import datetime
import time

bot = telebot.TeleBot(config.token)

time_start = ''
time_end = ''


# запуск бота для инициализации стартовых процессов:
@bot.message_handler(commands=['start'])
def start(message):
    with open('wordfilter.txt') as f:  # создание списка плохих слов из файла csv
        config.mat = f.read().split(', ')
        f.close()
        info_message = bot.send_message(message.chat.id, f'Шеф. я запустился. Все ок!')
        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)

#
# функция удаления команды пользователя и сообщения бота через время = config.pause
def del_bot_mes(chat_id, mes_id, info_mes_id):
        bot.delete_message(chat_id, mes_id)
        time.sleep(config.pause)
        bot.delete_message(chat_id, info_mes_id)


# Добавление плохих слов в БД
@bot.message_handler(commands=['addword'])
def addword(message):
    _, newword = message.text.split(maxsplit=1)
    if newword not in config.mat:
        with open('wordfilter.txt', 'a') as f:
            f.write(', ' + newword)
            f.close()
            config.mat.append(newword)
            info_message = bot.send_message(message.chat.id, f'В базу плохих слов добавлено слово "{newword}"')
            del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
    else:
        info_message = bot.send_message(message.chat.id, f'В базе плохих слов есть слово "{newword}"')
        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)


# Удаление слов из БД
@bot.message_handler(commands=['delword'])
def delword(message):
    _, word = message.text.split(maxsplit=1)
    if word in config.mat:
        with open('wordfilter.txt', 'w') as f:
            config.mat.remove(word)
            f.write(', '.join(config.mat))
            f.close()
            info_message = bot.send_message(message.chat.id, f'Из базы плохих слов удалено слово "{word}"')
            del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
    else:
        info_message = bot.send_message(message.chat.id, f'В базе плохих слов нет слова "{word}"')
        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)


# вывод сообщений, возможных к обработке
@bot.message_handler(commands=['show'])
def show(message):
    # print(f'message {message}')
    # bot.send_message(message.chat.id, f'group_id = {message.group_id}')
    # print(f'message = {message}')
    try:
        _, object = message.text.split(maxsplit=1)
    except ValueError:
        info_message = bot.send_message(message.chat.id, f'Неверно введена команда. Проверьте формат через /help')
        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
    else:
        admins = bot.get_chat_administrators(message.chat.id)
        admins_id = []
        for i in range(len(admins)):  # формируем список ID админов чата из списка инфо об админах
            admins_id.append(admins[i].user.id)
        if message.from_user.id not in admins_id: # если команду дал не админ - отлуп
            info_message = bot.send_message(message.chat.id, f'У вас недостаточно прав для этой команды')
            del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
        elif object == 'admins': # если команда "/show admins", то вывод админов:
            list_admins = ''
            for i in range(len(admins)):
                list_admins += (f'Админ №{i+1}: {admins[i].user.username}, бот? {admins[i].user.is_bot}\n')
            info_message = bot.send_message(message.chat.id, list_admins)
            del_bot_mes(message.chat.id, message.message_id, info_message.message_id)


@bot.message_handler(commands=['delete'])  # , func=lambda message: message.entities is not None and message.chat.id == message.chat.id )
def delete(message):
    # print(message)
    _, user, time_1, time_2 = message.text.split(maxsplit=3)
    print(datetime.fromtimestamp(message.date + 10800).strftime("%H:%M"))
    try:
        time_start_ = datetime.combine(datetime.now().date(), datetime.strptime(time_1, "%H-%M").time())
    except ValueError:
        bot.send_message(message.chat.id,
                         f'Неверно введена команда {message.text}. Правильный формат /delete ММ-ЧЧ ММ-ЧЧ')
    else:
        time_start_sec = int((time_start_ - datetime(1970, 1, 1)).total_seconds() - 10800)
        # print(time_start_)
        print(time_start_sec)
        time_end_ = datetime.combine(datetime.now().date(), datetime.strptime(time_2, "%H-%M").time())
        time_end_sec = int((time_end_ - datetime(1970, 1, 1)).total_seconds() - 10800)
        # print(time_end_)
        print(time_end_sec)

        # for i in range(time_end_sec, time_start_sec, -1):

        # ВОТ ЗДЕСЬ НАДО НАУЧИТЬСЯ ПРОхОДИТЬ ПО ДРУГИМ ПЕРЕМЕННЫМ СООбЩЕНИЯ
        for y in message.id:  # Пройдёмся по всем entities в поисках ссылок
            # url - обычная ссылка, text_link - ссылка, скрытая под текстом
            if message.from_user.username == user and message.date in range(time_start_sec, time_end_sec):
                print(message.date)
                # Мы можем не проверять chat.id, он проверяется ещё в хэндлере
                bot.delete_message(message.chat.id, message.message_id)
                print(f'Удалено сообщение от {message.from_user.username}, {message.chat.id}, {message.id}')
            else:
                return

# проверка поступившего сообщения на плохие слова
@bot.message_handler(content_types=['text'])
def bad_text(message):
    mats_words = ''
    for word in message.text.split(' '):
        supword = (''.join(c for c in word if c not in config.black_simvols)).lower()
        for word_from_slovar in config.mat:
            if supword == word_from_slovar:  # упроверяем на мат
                mats_words += (word + ', ')
    if mats_words != '':
        info_message = bot.send_message(message.chat.id, f'Зачем ругаешься? Ты сказал "{mats_words[:-2]}"!')
        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)


# проверка поступившего сообщения на графику, стикеры, видео, аудио и удаление его, а также позже - удаление
# сообщения бота
@bot.message_handler(content_types=['audio', 'photo', 'sticker', 'video', 'video_note', 'voice'])
def bad_message(message):
    if message.content_type in config.bot_settings['forbidden_message']:
        info_message = bot.send_message(message.chat.id, f'Размещение формата \b{message.content_type}\b запрещено! Удаляю!')


        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)

# @bot.message_handler(func=lambda message: message.entities is not None and message.chat.id == message.chat.id)
# def delete_links(message):
#     for entity in message.entities:  # Пройдёмся по всем entities в поисках ссылок
#         # url - обычная ссылка, text_link - ссылка, скрытая под текстом
#         if entity.type in ["url", "text_link"]:
#             # Мы можем не проверять chat.id, он проверяется ещё в хэндлере
#             bot.delete_message(message.chat.id, message.message_id)
#         else:
#             return

# time_start = datetime.fromtimestamp(time_1).strftime("%H:%M")
# time_end = datetime.fromtimestamp(time_2).strftime("%H:%M")


# print(msg)
# time.sleep(2)
# bot.edit_message_text(chat_id = message.chat.id, message_id = msg.message_id, text = f'ой, ты написал "{message.text}"')
# tb.edit_message_text(new_text, chat_id, message_id)
# photo = open('/tmp/photo.png', 'rb')
# tb.send_photo(chat_id, photo)
# tb.send_photo(chat_id, "FILEID")

bot.polling(none_stop=True)
