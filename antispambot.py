import telebot
import time
import markups as m
import json
import config
import logging
import logging.handlers
import os

from environs import Env
from telebot.apihelper import ApiTelegramException
# from telebot.util import update_types
from datetime import datetime

previous_markup = None
previous_message = None

LOGFILE = 'logs.txt'
logger = logging.getLogger()
env = Env()
env.read_env()
bot_token = env('BOT_TOKEN')
bot = telebot.TeleBot(bot_token)


# кнопка СТАРТ
# button_start = KeyboardButton('СТАРТ!')
# greet_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(KeyboardButton('СТАРТ!'))

def checking_for_admin(message):
    try:
        admins = bot.get_chat_administrators(message.chat.id)
    except ApiTelegramException:
        info_message = bot.send_message(
            message.chat.id, f'Команда доступна только в группе. В приватном чате нет администраторов.')
        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
        return False
    admins_id = [admins[i].user.id for i in range(len(admins))]  # список админов
    if message.from_user.id not in admins_id:  # если команду дал не админ - отлуп
        info_message = bot.send_message(message.chat.id, f'У вас недостаточно прав для этой команды')
        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
        return False
    return admins


# запуск бота для инициализации стартовых процессов:
@bot.message_handler(commands=['start'])
def start(message):
    if not checking_for_admin(message):
        return
    bot.send_message(message.chat.id, f"Меню в чате № {message.chat.id}!", reply_markup=m.start_markup)
    with open('bot_settings.json', 'r+') as file:
        config.bot_settings = json.load(file)
    if str(message.chat.id) in config.bot_settings.keys():
        logger.info('Я знаю этот чат!')
    else:   # если знакомый чат не найден - добавляем текущий чат в список конфига
        chat_settings = {'forbidden_messages': list(config.other_types_of_message.keys()), 'controlled_users': {}}
        config.bot_settings[str(message.chat.id)] = chat_settings
        save_bot_settings(config.bot_settings)
    if not config.mat:  # если словарь мата еще пустой
        with open(config.mat_file) as file:  # создание списка плохих слов из файла txt
            config.mat = file.read().split(', ')
            file.close()
        info_message = bot.send_message(message.chat.id, f'Словарь мата загружен')
        del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
    if not config.finance_words:  # если словарь финансовых понятий еще пустой
        with open(config.finance_words_file) as file:  # создание списка финансовых понятий из файла txt
            config.finance_words = file.read().split(', ')
            file.close()
        info_message = bot.send_message(message.chat.id, f'Словарь финансовых понятий загружен')
        del_bot_mes(message.chat.id, info_message.message_id, 0)
    info_message = bot.send_message(message.chat.id, f'Шеф. я запустился. Все ок!')  # , reply_markup=m.end_markup
    del_bot_mes(message.chat.id, info_message.message_id, 0)


# вызов меню:
@bot.message_handler(commands=['menu'])
def menu(message):
    if not checking_for_admin(message):
        return
    if config.mat:  # если словарь мата не пустой (признак, что бот ранее стартовал нормально)
        bot.send_message(message.chat.id, f"Меню в чате № {message.chat.id}!", reply_markup=m.start_markup)
    else:
        send_about_something(message, 'Для начаоа работы жми /start')


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global previous_markup
    global previous_message
    try:
        if call.data == "menu":
            bot.send_message(call.message.chat.id, "Настройки бота", reply_markup=m.menu_markup)
            del_bot_mes(call.message.chat.id, call.message.message_id, 0)
            previous_markup = 'start_markup'
            previous_message = 0
    
        if call.data == "help":
            previous_markup = 'start_markup'
            bot.send_message(call.message.chat.id, f'Помощь\n{config.help}', reply_markup=m.exit_markup)
            del_bot_mes(call.message.chat.id, call.message.message_id, 0)
    
        if call.data == "forbidden_messages":
            del_bot_mes(call.message.chat.id, call.message.message_id, 0)  # и всё последнее сообщение
            previous_markup = 'menu_markup'
            previous_message = 0
            bot.send_message(call.message.chat.id,
                             f'Нажмите для изменения доступности:',
                             reply_markup=m.forbidden_message_markup)
            forbidden_messages = ", ".join([config.other_types_of_message[type_name] for type_name in
                                            config.bot_settings[str(call.message.chat.id)]["forbidden_messages"]])
            bot.send_message(call.message.chat.id, f'Запрещенные сообщения: {forbidden_messages}')

        if call.data == "bad_words":
            del_bot_mes(call.message.chat.id, call.message.message_id, 0)  # и всё последнее сообщение
            previous_markup = 'menu_markup'
            previous_message = 0
            bot.send_message(call.message.chat.id, "Плохие слова", reply_markup=m.bad_words_markup)
    
        if call.data == "bad_words_add":
            previous_markup = 'menu_markup'
            previous_message = 0
            last_message = bot.send_message(call.message.chat.id, "Какое слово добавить?")
            config.command_from_markup[call.message.chat.id] = 'addword'
            bot.register_next_step_handler(last_message, add_word, 'bad')
        
        if call.data == "bad_words_del":
            previous_markup = 'menu_markup'
            previous_message = 0
            last_message = bot.send_message(call.message.chat.id, "Какое слово удалить?")
            config.command_from_markup[call.message.chat.id] = 'delword'
            bot.register_next_step_handler(last_message, del_word, 'bad')

        if call.data == "finance_words":
            del_bot_mes(call.message.chat.id, call.message.message_id, 0)  # и всё последнее сообщение
            previous_markup = 'menu_markup'
            previous_message = 0
            bot.send_message(call.message.chat.id, "Финансовые слова", reply_markup=m.finance_words_markup)

        if call.data == "finance_words_add":
            previous_markup = 'menu_markup'
            previous_message = 0
            last_message = bot.send_message(call.message.chat.id, "Какое слово добавить?")
            config.command_from_markup[call.message.chat.id] = 'addword'
            bot.register_next_step_handler(last_message, add_word, 'finance')

        if call.data == "finance_words_del":
            previous_markup = 'menu_markup'
            previous_message = 0
            last_message = bot.send_message(call.message.chat.id, "Какое слово удалить?")
            config.command_from_markup[call.message.chat.id] = 'delword'
            bot.register_next_step_handler(last_message, del_word, 'finance')
    
        if call.data in config.other_types_of_message.keys():
            previous_markup = 'menu_markup'
            previous_message = 0
            if call.data in config.bot_settings[str(call.message.chat.id)]['forbidden_messages']:
                config.bot_settings[str(call.message.chat.id)]['forbidden_messages'].remove(call.data)
                info_message = bot.send_message(
                    call.message.chat.id,
                    f'Cообщения типа "{config.other_types_of_message[call.data]}" разрешены.')
                del_bot_mes(call.message.chat.id, info_message.message_id, 0)
                save_bot_settings(config.bot_settings)
            else:
                config.bot_settings[str(call.message.chat.id)]['forbidden_messages'].append(call.data)
                info_message = bot.send_message(
                    call.message.chat.id,
                    f'Cообщения типа "{config.other_types_of_message[call.data]}" запрещены.',
                )
                del_bot_mes(call.message.chat.id, info_message.message_id, 0)
                save_bot_settings(config.bot_settings)
            forbidden_messages = ", ".join([config.other_types_of_message[type_name] for type_name in
                                            config.bot_settings[str(call.message.chat.id)]["forbidden_messages"]])
            previous_message = bot.send_message(call.message.chat.id, f'Запрещенные сообщения: {forbidden_messages}')
            del_bot_mes(call.message.chat.id, previous_message.message_id-2, 0)
    
        if call.data == "exit":
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
            bot.delete_message(call.message.chat.id, call.message.message_id)
            if previous_message:
                bot.delete_message(call.message.chat.id, previous_message)
    except Exception as error:
        logger.error(error)


# Добавление плохих слов в БД
@bot.message_handler(commands=['addword'])
def add_word(message, word_type='bad'):
    def add_word_to_file(file_name, word, data_list_name):
        with open(file_name, 'a') as file:
            file.write(', ' + word)
            file.close()
            data_list_name.append(word)
            send_about_something(message, f'В базу {word_type.upper()} добавлено слово "{word}"')
            return
    try:
        if not checking_for_admin(message):
            return
        if config.command_from_markup[message.chat.id]:
            message.text = 'addword ' + message.text
        _, new_word = message.text.split(maxsplit=1)
        new_word = new_word.lower()
        if word_type == 'bad' and new_word not in config.mat:
            add_word_to_file(config.mat_file, new_word, config.mat)
        elif word_type == 'finance' and new_word not in config.finance_words:
            add_word_to_file(config.finance_words_file, new_word, config.finance_words)
        else:
            send_about_something(message, f'В базе {word_type.upper()} уже есть слово "{new_word}"')
        if config.command_from_markup[message.chat.id]:
            del_bot_mes(message.chat.id, message.message_id - 1, 0)
            config.command_from_markup[message.chat.id] = None
    except Exception as error:
        logger.error(error)


# Удаление слов из БД
@bot.message_handler(commands=['delword'])
def del_word(message, word_type='bad'):
    def del_word_from_file(file_name, word, data_list_name):
        with open(file_name, 'w') as file:
            data_list_name.remove(word)
            file.write(', '.join(data_list_name))
            file.close()
            send_about_something(message, f'Из базы {word_type.upper()} удалено слово "{word}"')
            return
    try:
        if not checking_for_admin(message):
            return
        if config.command_from_markup[message.chat.id]:
            message.text = 'delword ' + message.text
        _, removing_word = message.text.split(maxsplit=1)
        removing_word = removing_word.lower()
        if word_type == 'bad' and removing_word in config.mat:
            del_word_from_file(config.mat_file, removing_word, config.mat)
        elif word_type == 'finance' and removing_word in config.finance_words:
            del_word_from_file(config.finance_words_file, removing_word, config.finance_words)
        else:
            send_about_something(message, f'В базе {word_type.upper()} нет слова "{removing_word}"')
        if config.command_from_markup[message.chat.id]:
            del_bot_mes(message.chat.id, message.message_id - 1, 0)
            config.command_from_markup[message.chat.id] = None
    except Exception as error:
        logger.error(error)


# вывод сообщений, возможных к обработке
@bot.message_handler(commands=['show'])
def show(message):
    admins = checking_for_admin(message)
    if not admins:
        return
    try:
        _, object_ = message.text.split(maxsplit=1)
    except ValueError:
        send_about_something(message, 'Неверно введена команда. Проверьте формат через /help')
        return
    
    if object_ == 'admins':  # если команда "/show admins", то вывод админов:
        list_admins = [
            f'Админ {num+1}: @{admin.user.username}{", бот" if admin.user.is_bot else ""}\n'
            for num, admin in enumerate(admins)
        ]
        send_about_something(message, ''.join(list_admins) + f'\nВсего админов: {len(list_admins)}')


@bot.message_handler(commands=['pause'])
def pause(message):
    if not checking_for_admin(message):
        return
    try:
        _, sec = message.text.split(maxsplit=1)
    except ValueError:
        send_about_something(message, 'Неверно введена команда. Проверьте формат через /help')
        return
    if sec.isdigit() and (0 < int(sec) <= 5):
        config.pause = int(sec)
        send_about_something(message, f'Пауза отображения сообщения бота теперь = {sec} секунд')
    else:
        send_about_something(message, 'Значение должно быть числом от 0.1 до 5')


@bot.message_handler(commands=['help'])
def help_(message):
    bot.send_message(message.chat.id, config.help)


# проверка поступившего сообщения на плохие слова
@bot.message_handler(content_types=['text'])
def check_for_bad_text(message):
    logger.info(message.from_user.id)
    logger.info(message.text)
    message_words = set([word.lower() for word in message.text.split(' ')])
    if (str(message.from_user.id) in config.bot_settings[str(message.chat.id)]['controlled_users'].keys() and
            len(message_words.intersection(config.finance_words)) > 0):
        logger.info(f'Впойман криптоман {message.from_user.username}, удаляем!!!')
        send_about_something(message, f'Впойман криптоман {message.from_user.username}, удаляем!!!')
        bot.kick_chat_member(message.chat.id, message.from_user.id)
        return
    try:
        mats_words = []
        for word in message.text.split(' '):
            supword = (''.join(c for c in word if c not in config.black_simvols)).lower()
            if supword in config.mat:   # проверяем на мат
                mats_words.append(word)
        if len(mats_words) > 0:
            send_about_something(message, f'Зачем ругаешься? Ты сказал "{", ".join(mats_words)}"!')
    except Exception as error:
        logger.error(error)


# проверка поступившего сообщения на графику, стикеры, видео, аудио и удаление его, а также позже - удаление
# сообщения бота
@bot.message_handler(content_types=config.other_types_of_message)
def check_for_bad_message(message):
    try:
        if message.content_type in config.bot_settings[str(message.chat.id)]['forbidden_messages']:
            info_message = bot.send_message(
                message.chat.id,
                f'Размещение формата {config.other_types_of_message[message.content_type]} запрещено! Удаляю!')
            del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
    except Exception as error:
        logger.error(error)
    
    
@bot.chat_member_handler()
def check_member_login(updated):
    try:
        if updated.new_chat_member.status == 'member':
            if (str(updated.new_chat_member.user.id) in
                    config.bot_settings[str(updated.chat.id)]['controlled_users'].keys()):
                logger.info(
                    f'Я знаю этого юзера {updated.new_chat_member.user.username} {updated.new_chat_member.user.id}!')
            else:
                logger.info(f'Я не знаю этого юзера {updated.new_chat_member.user.username}'
                            f' {updated.new_chat_member.user.id}. Добавил.')
                config.bot_settings[str(updated.chat.id)]['controlled_users'][str(updated.new_chat_member.user.id)] = \
                    {'addition time': datetime.now().strftime("%d-%m-%Y %H:%M:%S")}
                save_bot_settings(config.bot_settings)
    except Exception as error:
        logger.error(error)
        

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


def send_about_something(message, message_text='', delete_second_message=True):
    # отправляем информационное сообщение
    info_message = bot.send_message(message.chat.id, message_text)
    # и удаляем предыдущее сообщение (message.message_id) и при соблюдении условия - последнее (info_message.message_id)
    if not delete_second_message:
        del_bot_mes(message.chat.id, message.message_id, 0)
        return
    del_bot_mes(message.chat.id, message.message_id, info_message.message_id)
    
    
def create_bot_settings_file():
    # os.mknod('bot_settings.json')
    with open('bot_settings.json', 'w+') as file:
        file.write('{}')
        file.close()


# функция удаления команды пользователя и сообщения бота через время = config.pause
def del_bot_mes(chat_id, mes_id, info_mes_id):
    time.sleep(config.pause)
    bot.delete_message(chat_id, mes_id)
    if info_mes_id:
        bot.delete_message(chat_id, info_mes_id)


def save_bot_settings(bot_settings):    # сохранение списка настроек разных чатов в файл
    f = open('bot_settings.json', 'w+')
    f.seek(0)
    f.write(json.dumps(bot_settings))
    f.close()


def main():
    configuring_logging()
    # logger.info('ЗАПУСТИЛСЯ')
    if not os.path.exists('bot_settings.json'):
        create_bot_settings_file()
    # TODO переместить сюда или под IF __name__ переменные окружения и инстал бота
    # bot.infinity_polling(allowed_updates=update_types)
    bot.polling(none_stop=True)


if __name__ == "__main__":
    main()
