import telebot
import time
import markups as m
import json
import config
import logging
import logging.handlers
import os

from environs import Env
# from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiTelegramException
from telebot.util import update_types
from datetime import datetime

previous_markup = None
previous_message = None
time_start = ''
time_end = ''

LOGFILE = 'logs.txt'
logger = logging.getLogger()
env = Env()
env.read_env()
bot_token = env('BOT_TOKEN')
bot = telebot.TeleBot(bot_token)


# кнопка СТАРТ
# button_start = KeyboardButton('СТАРТ!')
# greet_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(KeyboardButton('СТАРТ!'))


# запуск бота для инициализации стартовых процессов:
@bot.message_handler(commands=['start'])
def start(message):
    logger.info('СТАРТУЮ!!!')
    bot.send_message(message.chat.id, f"Меню в чате № {message.chat.id}!", reply_markup=m.start_markup)
    with open('bot_settings.json', 'r+') as file:
        config.bot_settings = json.load(file)
        logger.info(config.bot_settings)
        # logger.info(config.bot_settings.keys())
    if str(message.chat.id) in config.bot_settings.keys():
        logger.info('Я знаю этот чат!')
    else:   # если знакомый чат не найден - добавляем текущий чат в список конфига
        chat_settings = {'forbidden_messages': config.other_types_of_message, 'controlled_users': {}}
        config.bot_settings[str(message.chat.id)] = chat_settings
        save_bot_settings(config.bot_settings)
        logger.info(config.bot_settings)
    if not config.mat:  # если словарь мата еще пустой
        with open('wordfilter.txt') as file:  # создание списка плохих слов из файла txt
            config.mat = file.read().split(', ')
            file.close()
        info_message = bot.send_message(message.chat.id, f'Словарь мата загружен')
        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
        # time.sleep(config.pause)
        # time.sleep(config.pause)
    if not config.financial_words:  # если словарь финансовых понятий еще пустой
        with open('financial_words.txt') as file:  # создание списка финансовых понятий из файла txt
            config.financial_words = file.read().split(', ')
            file.close()
        info_message = bot.send_message(message.chat.id, f'Словарь финансовых понятий загружен')
        del_bot_mes(message.chat.id, info_message.message_id, 0)
    info_message = bot.send_message(message.chat.id, f'Шеф. я запустился. Все ок!')  # , reply_markup=m.end_markup
    del_bot_mes(message.chat.id, info_message.message_id, 0)


# вызов меню:
@bot.message_handler(commands=['menu'])
def menu(message):
    if config.mat:  # если словарь мата не пустой (признак, что бот ранее стартовал нормально)
        bot.send_message(message.chat.id, f"Меню в чате № {message.chat.id}!", reply_markup=m.start_markup)


def save_bot_settings(bot_settings):    # сохранение списка настроек разных чатов в файл
    f = open('bot_settings.json', 'w+')
    f.seek(0)
    f.write(json.dumps(bot_settings))
    f.close()


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global previous_markup
    global previous_message
    # global info_message
    # try:
    if call.message:

        if call.data == "menu":
            del_bot_mes(call.message.chat.id, call.message.message_id, 0)
            bot.send_message(call.message.chat.id, "Настройки бота", reply_markup=m.menu_markup)
            previous_markup = 'start_markup'
            previous_message = 0

        if call.data == "help":
            # print(config.help)
            # bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
            #                              reply_markup='')  # удаляем кнопки у последнего сообщения
            del_bot_mes(call.message.chat.id, call.message.message_id, 0)
            previous_markup = 'start_markup'
            previous_message = (bot.send_message(call.message.chat.id, config.help)).message_id
            bot.send_message(call.message.chat.id, "Помощь", reply_markup=m.exit_markup)

        #TODO подставить русские названия на клавиатуру
        if call.data == "forbidden_messages":
            del_bot_mes(call.message.chat.id, call.message.message_id, 0)  # и всё последнее сообщение
            previous_markup = 'menu_markup'
            previous_message = 0
            if str(call.message.chat.id) in config.bot_settings.keys():
                bot.send_message(call.message.chat.id,
                                 f'Запрещенные сообщения: '
                                 f'{config.bot_settings[str(call.message.chat.id)]["forbidden_messages"]}',
                                 reply_markup=m.forbidden_message_markup)

        if call.data == "bad_words":
            del_bot_mes(call.message.chat.id, call.message.message_id, 0)  # и всё последнее сообщение
            previous_markup = 'menu_markup'
            previous_message = 0
            bot.send_message(call.message.chat.id, "Плохие слова", reply_markup=m.bad_words_markup)

        if call.data == "bad_words_add":
            # del_bot_mes(call.message.chat.id, call.message.message_id, 0)  # и всё последнее сообщение
            # previous_markup = 'menu_markup'
            # previous_message = 0
            mess = bot.send_message(call.message.chat.id, "Какое слово добавить?")
            config.command_from_markup = 'addword'
            bot.register_next_step_handler(mess, addword(bot.message_handler(content_types=['text'])))
            # if call.message.text == 'ля':
            #     bot.send_message(call.message.chat.id, 'Верный ответ!')

        if call.data in config.other_types_of_message.keys():
            previous_markup = 'menu_markup'
            previous_message = 0
            if str(call.message.chat.id) in config.bot_settings.keys():
                if call.data in config.bot_settings[str(call.message.chat.id)]['forbidden_messages']:
                    (config.bot_settings[str(call.message.chat.id)]['forbidden_messages']).remove(call.data)
                    mes1 = bot.send_message(call.message.chat.id, f"Cообщения типа {call.data} разрешены")
                    time.sleep(config.pause)
                    del_bot_mes(call.message.chat.id, mes1.message_id, 0)
                    save_bot_settings(config.bot_settings)
                else:
                    (config.bot_settings[str(call.message.chat.id)]['forbidden_messages']).append(call.data)
                    mes1 = bot.send_message(call.message.chat.id, f"Cообщения типа {call.data} запрещены")
                    time.sleep(config.pause)
                    del_bot_mes(call.message.chat.id, mes1.message_id, 0)
                    save_bot_settings(config.bot_settings)
        # print(config.forbidden_messages)

        if call.data == "exit":
            # print(call.message.message_id)
            # bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
            #                               reply_markup='')  # удаляем кнопки у последнего сообщения
            bot.delete_message(call.message.chat.id, call.message.message_id)
            if previous_message:
                bot.delete_message(call.message.chat.id, previous_message)
            if previous_markup == 'start_markup':
                bot.send_message(call.message.chat.id, f"Меню в чате № {call.message.chat.id}!",
                                 reply_markup=m.start_markup)
                previous_markup = ''
            elif previous_markup == 'menu_markup':
                bot.send_message(call.message.chat.id, "Настройки бота", reply_markup=m.menu_markup)
                previous_markup = 'start_markup'
            elif previous_markup == 'forbidden_message_markup':
                bot.send_message(call.message.chat.id, "Запрещенные сообщения", reply_markup=m.forbidden_message_markup)
                previous_markup = 'menu_markup'
            elif previous_markup == 'bad_words':
                bot.send_message(call.message.chat.id, "Плохие слова", reply_markup=m.bad_words_markup)
                previous_markup = 'menu_markup'

    # except Exception as e:
    #     print(repr(e))


# функция удаления команды пользователя и сообщения бота через время = config.pause
def del_bot_mes(chat_id, mes_id, info_mes_id):
    time.sleep(config.pause)
    bot.delete_message(chat_id, mes_id)
    if info_mes_id:
        time.sleep(config.pause)
        bot.delete_message(chat_id, info_mes_id)


# Добавление плохих слов в БД
@bot.message_handler(commands=['addword'])
def addword(message):
    if config.command_from_markup:
        message = bot.message_handler(content_types=['text'])
        message.text = 'addword ' + message.text
    try:
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
    except Exception as e:
        logger.error(repr(e))
    if config.command_from_markup:
        config.command_from_markup = None


# Удаление слов из БД
@bot.message_handler(commands=['delword'])
def delword(message):
    try:
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
    except Exception as e:
        logger.error(repr(e))


# вывод сообщений, возможных к обработке
@bot.message_handler(commands=['show'])
def show(message):
    # print(f'message {message}')
    # bot.send_message(message.chat.id, f'group_id = {message.group_id}')
    # print(f'message = {message}')
    try:
        _, object_ = message.text.split(maxsplit=1)
    except ValueError:
        info_message = bot.send_message(message.chat.id, f'Неверно введена команда. Проверьте формат через /help')
        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
        return
    try:
        admins = bot.get_chat_administrators(message.chat.id)
    except ApiTelegramException:
        info_message = bot.send_message(
            message.chat.id, f'Команда доступна только в группе. В приватном чате нет администраторов.')
        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
        return
    admins_id = [admins[i].user.id for i in range(len(admins))]  # список админов

    if message.from_user.id not in admins_id:  # если команду дал не админ - отлуп
        info_message = bot.send_message(message.chat.id, f'У вас недостаточно прав для этой команды')
        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
    elif object_ == 'admins':  # если команда "/show admins", то вывод админов:
        list_admins = ''
        for i in range(len(admins)):
            list_admins += f'Админ №{i+1}: {admins[i].user.username}, Бот = {admins[i].user.is_bot}\n'
        info_message = bot.send_message(message.chat.id, list_admins)
        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)


@bot.message_handler(commands=['pause'])
def pause(message):
    try:
        _, sec = message.text.split(maxsplit=1)
    except ValueError:
        info_message = bot.send_message(message.chat.id, f'Неверно введена команда. Проверьте формат через /help')
        del_bot_mes(message.chat.id, info_message.message_id, 0)
    else:
        if sec.isdigit():
            config.pause = int(sec)
            info_message = bot.send_message(message.chat.id, f'Пауза отображения сообщения бота теперь = {sec} секунд')
            del_bot_mes(message.chat.id, info_message.message_id, 0)
        else:
            info_message = bot.send_message(message.chat.id, f'Неверно введена команда. Проверьте формат через /help')
            del_bot_mes(message.chat.id, info_message.message_id, 0)


@bot.message_handler(commands=['help'])
def help_(message):
    bot.send_message(message.chat.id, config.help)


@bot.message_handler(commands=['delete'])
# , func=lambda message: message.entities is not None and message.chat.id == message.chat.id )
def delete(message):
    # print(message)
    _, user, time_1, time_2 = message.text.split(maxsplit=3)
    logger.info(datetime.fromtimestamp(message.date + 10800).strftime("%H:%M"))
    try:
        time_start_ = datetime.combine(datetime.now().date(), datetime.strptime(time_1, "%H-%M").time())
    except ValueError:
        bot.send_message(message.chat.id,
                         f'Неверно введена команда {message.text}. Правильный формат /delete ММ-ЧЧ ММ-ЧЧ')
    else:
        time_start_sec = int((time_start_ - datetime(1970, 1, 1)).total_seconds() - 10800)
        # print(time_start_)
        logger.info(time_start_sec)
        time_end_ = datetime.combine(datetime.now().date(), datetime.strptime(time_2, "%H-%M").time())
        time_end_sec = int((time_end_ - datetime(1970, 1, 1)).total_seconds() - 10800)
        # print(time_end_)
        logger.info(time_end_sec)

        # for i in range(time_end_sec, time_start_sec, -1):

        # ВОТ ЗДЕСЬ НАДО НАУЧИТЬСЯ ПРОхОДИТЬ ПО ДРУГИМ ПЕРЕМЕННЫМ СООбЩЕНИЯ
        for _ in message.id:  # Пройдёмся по всем entities в поисках ссылок
            # url - обычная ссылка, text_link - ссылка, скрытая под текстом
            if message.from_user.username == user and message.date in range(time_start_sec, time_end_sec):
                logger.info(message.date)
                # Мы можем не проверять chat.id, он проверяется ещё в хэндлере
                bot.delete_message(message.chat.id, message.message_id)
                logger.info(f'Удалено сообщение от {message.from_user.username}, {message.chat.id}, {message.id}')
            else:
                return


# проверка поступившего сообщения на плохие слова
@bot.message_handler(content_types=['text'])
def bad_text(message):
    logger.info(message.from_user.id)
    logger.info(message.text)


    message_words = set([word.lower() for word in message.text.split(' ')])
    if (str(message.from_user.id) in config.bot_settings[str(message.chat.id)]['controlled_users'].keys() and
            len(message_words.intersection(config.financial_words)) > 0):
        logger.info(f'Впойман криптоман {message.from_user.username}, удаляем!!!')
        info_message = bot.send_message(message.chat.id, f'Впойман криптоман {message.from_user.username}, удаляем!!!')
        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
        bot.kick_chat_member(message.chat.id, message.from_user.id)
        return
    try:
        mats_words = []
        for word in message.text.split(' '):
            supword = (''.join(c for c in word if c not in config.black_simvols)).lower()
            if supword in config.mat:   # проверяем на мат
                mats_words.append(word)
        if len(mats_words) > 0:
            info_message = bot.send_message(message.chat.id, f'Зачем ругаешься? Ты сказал "{mats_words}"!')
            del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
    except Exception as e:
        logger.error(repr(e))


# проверка поступившего сообщения на графику, стикеры, видео, аудио и удаление его, а также позже - удаление
# сообщения бота
@bot.message_handler(content_types=config.other_types_of_message)
def bad_message(message):
    logger.info(message.chat.id)
    logger.info(message.content_type)
    try:
        # for chat_settings in config.bot_settings:
        #     if message.chat.id in chat_settings.values():
        if message.content_type in config.bot_settings[str(message.chat.id)]['forbidden_messages']:
            info_message = bot.send_message(message.chat.id, f'Размещение формата \
                                                    \b{message.content_type}\b запрещено! Удаляю!')
            del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
    except Exception as e:
        logger.error(repr(e))
    
    
@bot.chat_member_handler()
def check_member_login(updated):
    try:
        if updated.new_chat_member.status == 'member':
            if str(updated.new_chat_member.user.id) in config.bot_settings[str(updated.chat.id)]['controlled_users'].keys():
                logger.info(f'Я знаю этого юзера {updated.new_chat_member.user.username} {updated.new_chat_member.user.id}!')
            else:
                logger.info(f'Я не знаю этого юзера {updated.new_chat_member.user.username}'
                            f' {updated.new_chat_member.user.id}. Добавил.')
                config.bot_settings[str(updated.chat.id)]['controlled_users'][str(updated.new_chat_member.user.id)] = \
                    {'addition time': datetime.now().strftime("%d-%m-%Y %H:%M:%S")}
                save_bot_settings(config.bot_settings)
    except Exception as e:
        logger.error(repr(e))
        

# @bot.message_handler(func=lambda message: message.entities is not None and message.chat.id == message.chat.id)
# def delete_links(message):
#     for entity in message.entities:  # Пройдёмся по всем entities в поисках ссылок
#         # url - обычная ссылка, text_link - ссылка, скрытая под текстом
#         if entity.type in ["url", "text_link"]:
#             # Мы можем не проверять chat.id, он проверяется ещё в хэндлере
#             bot.delete_message(message.chat.id, message.message_id)
#         else:
#             return



def configuring_logging():
    logger.setLevel(logging.INFO)
    logger_handler = logging.StreamHandler()
    # logger_handler = logging.handlers.RotatingFileHandler(
    #     LOGFILE, maxBytes=(1048576*5), backupCount=3
    # )
    logger_formatter = logging.Formatter(
        '%(asctime)s : %(levelname)s : %(message)s',
        datefmt='%d-%m-%Y %H:%M:%S'
    )
    logger_handler.setFormatter(logger_formatter)
    logger.addHandler(logger_handler)
    return logger


def create_bot_settings_file():
    # os.mknod('bot_settings.json')
    with open('bot_settings.json', 'w+') as file:
        file.write('{}')
        file.close()


def main():
    configuring_logging()
    # logger.info('ЗАПУСТИЛСЯ')
    if not os.path.exists('bot_settings.json'):
        create_bot_settings_file()
    #TODO переместить сюда или под IF __name__ переменные окружения и инстал бота
    bot.infinity_polling(allowed_updates=update_types)


if __name__ == "__main__":
    main()

