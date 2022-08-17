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
    with open('wordfilter.txt', newline='') as f:  # создание списка плохих слов из файла csv
        config.mat = f.read().split(', ')
        f.close()
    bot.send_message(message.chat.id, f'group_id = {message.chat.id}')


@bot.message_handler(commands=['addword'])
def addword(message):
    _, newword = message.text.split(maxsplit=1)
    if newword not in str(config.mat).lower():
        with open('wordfilter.txt', 'a') as f:
            f.write(', ' + newword)
            f.close()
            config.mat.append(newword)
            bot.send_message(message.chat.id, f'В базу плохих слов добавлено слово {newword}')
    else:
        bot.send_message(message.chat.id, f'В базе плохих слов есть слово {newword}')

@bot.message_handler(commands=['show'])  # вывод сообщений, возможных к обработке
def show(message):
    # print(f'message {message}')
    #bot.send_message(message.chat.id, f'group_id = {message}')
    print(f'message = {message}')

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
    for word in message.text.split(' '):
        supword = (''.join(c for c in word if c not in config.black_sibvols)).lower()
        for word_from_slovar in config.mat:
            if supword == word_from_slovar.lower():  # уменьшаем слово
                bot.send_message(message.chat.id, f'Зачем ругаешься? Ты сказал {word}!')



# проверка поступившего сообщения на графику, стикеры, видео, аудио и удаление его, а также позже - удаление
# сообщения бота
@bot.message_handler(content_types=['audio', 'photo', 'sticker', 'video', 'video_note', 'voice'])
def bad_message(message):
    if message.content_type in config.bot_settings['forbidden_message']:
        info_message = bot.send_message(message.chat.id, f'Че за херня? Удаляю!')
        bot.delete_message(message.chat.id, message.message_id)
        time.sleep(2)
        print(info_message)
        bot.delete_message(info_message.chat.id, info_message.message_id)

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
