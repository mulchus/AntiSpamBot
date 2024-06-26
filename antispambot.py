import telebot
import time
import markups as m
import json
import config
import logging
import logging.handlers
import os
import schedule
import string

from threading import Thread
from pathlib import Path
from requests.exceptions import ConnectionError

from environs import Env
from telebot.apihelper import ApiTelegramException
from telebot.util import update_types
from datetime import datetime, timedelta


logger = logging.getLogger()
env = Env()
env.read_env()
bot_token = env('BOT_TOKEN')
bot = telebot.TeleBot(bot_token)
BASE_DIR = Path(__file__).resolve().parent


def delete_old_users():
    if not config.bot_settings:
        return
    for chat_id, chat_config in config.bot_settings.items():
        # удаляем юзеров, которые больше config.seconds_to_user_be_old секунд назад добавленны в чат
        for user_id, user_config in chat_config['controlled_users'].copy().items():
            if (datetime.strptime(user_config['addition time'], "%d-%m-%Y %H:%M:%S")
                    < datetime.now() - timedelta(seconds=config.seconds_to_user_be_old)):
                logger.info(f'Удаляем контроль юзера {user_id} из чата {chat_id}.')
                config.bot_settings[chat_id]['controlled_users'].pop(user_id)
    save_bot_settings(config.bot_settings)
    

def starting_tasks():
    schedule.every(config.control_period).seconds.do(delete_old_users)
    while True:
        schedule.run_pending()
        time.sleep(60)


def checking_for_admin(user_id: int, chat_id: int):
    try:
        admins = bot.get_chat_administrators(chat_id)
    except ApiTelegramException:
        return False, 'Команда доступна только в группе. В приватном чате нет администраторов.'
    admins_ids = [admin.user.id for admin in admins]  # список админов
    if user_id not in admins_ids:  # если команду дал не админ - отлуп
        return False, 'У вас недостаточно прав для этой команды.'
    return admins, 'Ок.'


# запуск бота для инициализации стартовых процессов:
@bot.message_handler(commands=['start'])
def start(message):
    result, message_text = checking_for_admin(message.from_user.id, message.chat.id)
    if not result:
        send_about_something(message, message_text)
        return
    with open(Path.joinpath(BASE_DIR, 'bot_settings.json'), 'r') as file:
        config.bot_settings = json.load(file)
    if str(message.chat.id) in config.bot_settings.keys():
        config.bot_settings[str(message.chat.id)]['previous_markup'] = None
        config.bot_settings[str(message.chat.id)]['previous_message'] = None
        save_bot_settings(config.bot_settings)
    else:   # если знакомый чат не найден - добавляем текущий чат в список конфига
        chat_settings = {
            'forbidden_messages': list(config.other_types_of_message.keys()),
            'controlled_users': {},
            'previous_markup': None,
            'previous_message': None,
        }
        config.bot_settings[str(message.chat.id)] = chat_settings
        save_bot_settings(config.bot_settings)
    if not config.mat:  # если словарь мата еще пустой
        with open(Path.joinpath(BASE_DIR, config.mat_file), encoding='utf-8') as file:
            # создание списка плохих слов из файла txt
            config.mat = file.read().split(', ')
            file.close()
        send_about_something(message, 'Словарь мата загружен', False)
    if not config.finance_words:  # если словарь финансовых понятий еще пустой
        with open(Path.joinpath(BASE_DIR, config.finance_words_file), encoding='utf-8') as file:
            # создание списка финансовых понятий из файла txt
            config.finance_words = file.read().split(', ')
            file.close()
        send_about_something(message, 'Словарь финансовых понятий загружен', False)
    if not config.stop_words:  # если словарь стоп-слов еще пустой
        with open(Path.joinpath(BASE_DIR, 'stopwords.txt'), 'r', encoding='utf-8') as file:
            config.stop_words = file.read().splitlines()
    send_about_something(message, 'Шеф. я запустился. Все ок!')
    logger.info(f'Запуск в чате {message.chat.id}.')


# вызов меню:
@bot.message_handler(commands=['menu'])
def menu(message):
    result, message_text = checking_for_admin(message.from_user.id, message.chat.id)
    if not result:
        send_about_something(message, message_text)
        return
    if config.mat:  # если словарь мата не пустой (признак, что бот ранее стартовал нормально)
        bot.send_message(message.chat.id, f"Меню в чате № {message.chat.id}!", reply_markup=m.menu_markup)
        bot.delete_message(message.chat.id, message.message_id)
    else:
        send_about_something(message, 'Для начаоа работы жми /start')


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    result, message_text = checking_for_admin(call.from_user.id, call.message.chat.id)
    if not result:
        send_about_something(call.message, message_text)
        return
    try:
        if call.data == "menu":
            config.bot_settings[str(call.message.chat.id)]['previous_markup'] = ''
            send_about_something(call.message, "Настройки бота", True, False, m.menu_markup)
    
        if call.data == "help":
            config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'menu_markup'
            send_about_something(call.message, f'Помощь\n{config.help}', True, False, m.exit_markup)
    
        if call.data == "forbidden_messages":
            config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'menu_markup'
            send_about_something(call.message, 'Нажмите для изменения доступности:',
                                 True, False, m.forbidden_message_markup)
            forbidden_messages = ", ".join([config.other_types_of_message[type_name] for type_name in
                                            config.bot_settings[str(call.message.chat.id)]["forbidden_messages"]])
            bot.send_message(call.message.chat.id, f'Запрещенные сообщения: {forbidden_messages}')

        if call.data == "bad_words":
            config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'menu_markup'
            send_about_something(call.message, "Плохие слова", True, False, m.bad_words_markup)
   
        if call.data == "bad_words_add":
            config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'menu_markup'
            last_message = bot.send_message(call.message.chat.id, "Какое слово добавить?")
            config.command_from_markup[call.message.chat.id] = 'addword'
            bot.register_next_step_handler(last_message, add_word, 'bad')
        
        if call.data == "bad_words_del":
            config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'menu_markup'
            last_message = bot.send_message(call.message.chat.id, "Какое слово удалить?")
            config.command_from_markup[call.message.chat.id] = 'delword'
            bot.register_next_step_handler(last_message, del_word, 'bad')

        if call.data == "finance_words":
            config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'menu_markup'
            send_about_something(call.message, "Финансовые слова", True, False, m.finance_words_markup)

        if call.data == "finance_words_add":
            config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'menu_markup'
            last_message = bot.send_message(call.message.chat.id, "Какое слово добавить?")
            config.command_from_markup[call.message.chat.id] = 'addword'
            bot.register_next_step_handler(last_message, add_word, 'finance')

        if call.data == "finance_words_del":
            config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'menu_markup'
            last_message = bot.send_message(call.message.chat.id, "Какое слово удалить?")
            config.command_from_markup[call.message.chat.id] = 'delword'
            bot.register_next_step_handler(last_message, del_word, 'finance')
        
        if call.data == "analysis":
            config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'menu_markup'
            last_message = send_about_something(
                call.message, "Введите или перешлите сообщение для анализа на криптоматику.",
                True, False, m.exit_markup)
            bot.register_next_step_handler(last_message, analysis_text_to_crypto)
    
        if call.data in config.other_types_of_message.keys():
            config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'menu_markup'
            if call.data in config.bot_settings[str(call.message.chat.id)]['forbidden_messages']:
                config.bot_settings[str(call.message.chat.id)]['forbidden_messages'].remove(call.data)
                send_about_something(call.message,
                                     f'Cообщения типа "{config.other_types_of_message[call.data]}" разрешены.',
                                     False, True)
                save_bot_settings(config.bot_settings)
            else:
                config.bot_settings[str(call.message.chat.id)]['forbidden_messages'].append(call.data)
                send_about_something(call.message,
                                     f'Cообщения типа "{config.other_types_of_message[call.data]}" запрещены.',
                                     False, True)
                save_bot_settings(config.bot_settings)
            forbidden_messages = ", ".join([config.other_types_of_message[type_name] for type_name in
                                            config.bot_settings[str(call.message.chat.id)]["forbidden_messages"]])
            config.bot_settings[str(call.message.chat.id)]['previous_message'] = \
                (bot.send_message(call.message.chat.id, f'Запрещенные сообщения: {forbidden_messages}')).message_id
            bot.delete_message(call.message.chat.id,
                               config.bot_settings[str(call.message.chat.id)]['previous_message']-2)

        if call.data == "exit":
            if config.bot_settings[str(call.message.chat.id)]['previous_markup'] == 'menu_markup':
                config.bot_settings[str(call.message.chat.id)]['previous_markup'] = None
                send_about_something(call.message, f"Меню в чате № {call.message.chat.id}!",
                                     True, False, m.menu_markup)
            elif config.bot_settings[str(call.message.chat.id)]['previous_markup'] == 'forbidden_message_markup':
                config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'menu_markup'
                send_about_something(call.message, "Запрещенные сообщения",
                                     True, False, m.forbidden_message_markup)
            elif config.bot_settings[str(call.message.chat.id)]['previous_markup'] == 'bad_words':
                config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'menu_markup'
                send_about_something(call.message, "Плохие слова", True, False, m.bad_words_markup)
            if config.bot_settings[str(call.message.chat.id)]['previous_message']:
                bot.delete_message(call.message.chat.id,
                                   config.bot_settings[str(call.message.chat.id)]['previous_message'])
                config.bot_settings[str(call.message.chat.id)]['previous_message'] = None
    except Exception as error:
        logger.error(error)


@bot.message_handler(commands=['analysis'])
def analysis_text_to_crypto(message):
    try:
        result, message_text = checking_for_admin(message.from_user.id, message.chat.id)
        if not result:
            send_about_something(message, message_text)
            return
        words = set([get_supword(word.lower()) for word in message.text.split()
                     if word.lower() not in config.stop_words])
        possible_words = [word for word in words if word not in config.finance_words]
        send_about_something(message, f'Возможные слова: {", ".join(possible_words)}', True, False)
        if config.command_from_markup[message.chat.id]:
            bot.delete_message(message.chat.id, message.message_id - 1)
            config.command_from_markup[message.chat.id] = None
    except Exception as error:
        logger.error(error)


# Добавление плохих слов в БД
@bot.message_handler(commands=['addword'])
def add_word(message, word_type='bad'):
    def add_word_to_file(file_name, word, data_list_name):
        with open(Path.joinpath(BASE_DIR, file_name), 'a', encoding='utf-8') as file:
            file.write(', ' + word)
            file.close()
            data_list_name.append(word)
            send_about_something(message, f'В базу {word_type.upper()} добавлено слово "{word}"')
            return
    try:
        result, message_text = checking_for_admin(message.from_user.id, message.chat.id)
        if not result:
            send_about_something(message, message_text)
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
            send_about_something(
                message, f'В базе {word_type.upper()} уже есть слово "{new_word}"')
        if config.command_from_markup[message.chat.id]:
            bot.delete_message(message.chat.id, message.message_id - 1)
            config.command_from_markup[message.chat.id] = None
    except Exception as error:
        logger.error(error)


# Удаление слов из БД
@bot.message_handler(commands=['delword'])
def del_word(message, word_type='bad'):
    def del_word_from_file(file_name, word, data_list_name):
        with open(Path.joinpath(BASE_DIR, file_name), 'w', encoding='utf-8') as file:
            data_list_name.remove(word)
            file.write(', '.join(data_list_name))
            file.close()
            send_about_something(message, f'Из базы {word_type.upper()} удалено слово "{word}"')
            return
    try:
        result, message_text = checking_for_admin(message.from_user.id, message.chat.id)
        if not result:
            send_about_something(message, message_text)
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
            send_about_something(
                message, f'В базе {word_type.upper()} нет слова "{removing_word}"')
        if config.command_from_markup[message.chat.id]:
            bot.delete_message(message.chat.id, message.message_id - 1)
            config.command_from_markup[message.chat.id] = None
    except Exception as error:
        logger.error(error)


# вывод сообщений, возможных к обработке
@bot.message_handler(commands=['show'])
def show(message):
    result, message_text = checking_for_admin(message.from_user.id, message.chat.id)
    if not result:
        send_about_something(message, message_text)
        return
    try:
        _, object_ = message.text.split(maxsplit=1)
    except ValueError:
        send_about_something(message, 'Неверно введена команда. Проверьте формат через /help')
        return
    
    if object_ == 'admins':  # если команда "/show admins", то вывод админов:
        list_admins = [
            f'Админ {num+1}: @{admin.user.username}{", бот" if admin.user.is_bot else ""}\n'
            for num, admin in enumerate(result)
        ]
        send_about_something(
            message, ''.join(list_admins) + f'\nВсего админов: {len(list_admins)}')


@bot.message_handler(commands=['pause'])
def pause(message):
    result, message_text = checking_for_admin(message.from_user.id, message.chat.id)
    if not result:
        send_about_something(message, message_text)
        return
    try:
        _, sec = message.text.split(maxsplit=1)
    except ValueError:
        send_about_something(message, 'Неверно введена команда. Проверьте формат через /help')
        return
    try:
        if 0 < float(sec) <= 5:
            config.pause = float(sec)
            send_about_something(message, f'Пауза отображения сообщения бота теперь = {sec} секунд')
        else:
            send_about_something(message, 'Значение должно быть числом от 0.1 до 5')
    except ValueError:
        send_about_something(message, 'Значение должно быть числом от 0.1 до 5')


@bot.message_handler(commands=['help'])
def help_(message):
    bot.send_message(message.chat.id, config.help)


# проверка поступившего сообщения на плохие слова
@bot.message_handler(content_types=['text'])
def check_for_bad_text(message):
    message_words = set([word.lower() for word in message.text.split(' ')])
    if (str(message.from_user.id) in config.bot_settings[str(message.chat.id)]['controlled_users'].keys() and
            (len(message_words.intersection(config.finance_words)) > 0 or
                (0 < len([char for char in message.text.lower() if char in list(string.ascii_lowercase)]) /
             len(message.text) < 0.35))):
        message_text = f'Впойман криптоман {message.from_user.username} {message.from_user.id}, удаляем!!!'
        logger.info(message_text)
        send_about_something(message, message_text)
        bot.kick_chat_member(message.chat.id, message.from_user.id)
        return
    
    try:
        mats_words = []
        for word in message.text.split(' '):
            supword = get_supword(word)
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
        if (str(message.from_user.id) in config.bot_settings[str(message.chat.id)]['controlled_users'].keys() and
                message.content_type in config.bot_settings[str(message.chat.id)]['forbidden_messages']):
            send_about_something(
                message,
                f'Размещение формата {config.other_types_of_message[message.content_type]} запрещено! Удаляю!')
    except Exception as error:
        logger.error(error)
    

@bot.chat_member_handler()
def check_member_login(updated):
    try:
        user = updated.new_chat_member.user
        if updated.new_chat_member.status == 'member':
            message_text = (f'знаю этого юзера '
                            f'{user.id}'
                            f'{(", " + user.username) if user.username else ""}'                            
                            f'{(", " + user.first_name) if user.first_name else ""}'
                            f'{(", " + user.last_name) if user.last_name else ""}'
                            f'{", бот" if user.is_bot else ", не бот"}.')
            if (str(user.id) in
                    config.bot_settings[str(updated.chat.id)]['controlled_users'].keys()):
                logger.info('Я ' + message_text)
            else:
                logger.info(f'Я не ' + message_text + ' Добавил.')
                config.bot_settings[str(updated.chat.id)]['controlled_users'][str(user.id)] = \
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
    # logger_handler = logging.StreamHandler()
    logger_handler = logging.handlers.RotatingFileHandler(
        Path.joinpath(BASE_DIR, config.log_file), maxBytes=(1048576*5), backupCount=3
    )
    logger_formatter = logging.Formatter(
        '%(asctime)s : %(levelname)s : %(message)s',
        datefmt='%d-%m-%Y %H:%M:%S'
    )
    logger_handler.setFormatter(logger_formatter)
    logger.addHandler(logger_handler)
    return logger


def send_about_something(
        message: telebot.types.Message,
        message_text: str = '',
        dalete_previous_message: bool = True,
        delete_this_message: bool = True,
        markup: telebot.types.InlineKeyboardMarkup = None,
):
    """Отправка сообщения и по умолчанию удаление предыдущего и отправленного."""
    info_message = bot.send_message(message.chat.id, message_text, reply_markup=markup)
    time.sleep(config.pause)
    if delete_this_message:
        bot.delete_message(message.chat.id, info_message.message_id)
    if dalete_previous_message:
        bot.delete_message(message.chat.id, message.message_id)
    return info_message


def save_bot_settings(bot_settings: dict):    # сохранение списка настроек разных чатов в файл
    with open(Path.joinpath(BASE_DIR, 'bot_settings.json'), 'w+') as file:
        file.write(json.dumps(bot_settings))
        file.close()


def get_supword(word: str) -> str:
    return (''.join(c for c in word if c not in config.black_simvols)).lower()
    

def main():
    thread = Thread(target=starting_tasks)
    thread.start()
    configuring_logging()
    if not os.path.exists('bot_settings.json'):
        save_bot_settings(config.bot_settings)

    while True:
        try:
            bot.polling(allowed_updates=update_types, none_stop=True)
        except ConnectionError as error:
            logger.error(f'Потеря или ошибка соединения. {error}')
            time.sleep(15)
        except Exception as err:
            logger.error('Бот упал c неизвестной ошибкой:')
            logger.exception(err)


if __name__ == "__main__":
    main()
