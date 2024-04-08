import telebot
import time
import markups as m
import json
import config
import logging
import logging.handlers
import os
import schedule
from threading import Thread

from environs import Env
from telebot.apihelper import ApiTelegramException
from datetime import datetime, timedelta


logger = logging.getLogger()
env = Env()
env.read_env()
bot_token = env('BOT_TOKEN')
bot = telebot.TeleBot(bot_token)


def delete_old_users():
    if not config.bot_settings:
        return
    for chat_id, chat_config in config.bot_settings.items():
        # удаляем юзеров, которые больше config.seconds_to_user_be_old секунд назад добавленны в чат
        for user_id, user_config in chat_config['controlled_users'].copy().items():
            if (datetime.strptime(user_config['addition time'], "%d-%m-%Y %H:%M:%S")
                    < datetime.now() - timedelta(seconds=config.seconds_to_user_be_old)):
                logger.info(f'Удаляем юзера {user_id} из чата {chat_id}.')
                config.bot_settings[chat_id]['controlled_users'].pop(user_id)
    save_bot_settings(config.bot_settings)
    

def starting_tasks():
    schedule.every(config.control_period).seconds.do(delete_old_users)
    while True:
        schedule.run_pending()
        time.sleep(60)
        

def checking_for_admin(message):
    try:
        # TODO  AttributeError: 'CallbackQuery' object has no attribute 'chat' if i send only CALL
        admins = bot.get_chat_administrators(message.chat.id)
    except ApiTelegramException:
        send_about_something(message, 'Команда доступна только в группе. В приватном чате нет администраторов.')
        return False
    admins_ids = [admin.user.id for admin in admins]  # список админов
    if message.from_user.id not in admins_ids:  # если команду дал не админ - отлуп
        send_about_something(message, 'У вас недостаточно прав для этой команды.')
        return False
    return admins


# запуск бота для инициализации стартовых процессов:
@bot.message_handler(commands=['start'])
def start(message):
    if not checking_for_admin(message):
        return
    bot.send_message(message.chat.id, f"Меню в чате № {message.chat.id}!", reply_markup=m.start_markup)
    with open('bot_settings.json', 'r') as file:
        config.bot_settings = json.load(file)
    if str(message.chat.id) in config.bot_settings.keys():
        logger.info('Я знаю этот чат!')
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
        with open(config.mat_file) as file:  # создание списка плохих слов из файла txt
            config.mat = file.read().split(', ')
            file.close()
        send_about_something(message, 'Словарь мата загружен', False)
    if not config.finance_words:  # если словарь финансовых понятий еще пустой
        with open(config.finance_words_file) as file:  # создание списка финансовых понятий из файла txt
            config.finance_words = file.read().split(', ')
            file.close()
        send_about_something(message, 'Словарь финансовых понятий загружен', False)
    send_about_something(message, 'Шеф. я запустился. Все ок!')


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
    print(call.message)
    print(call.from_user.id)
    # TODO здесь почему то всегда показывает что кнопку нажал админ!!!
    print(call.message.from_user.id, call.message.chat.id)
    if not checking_for_admin(call):
        return
    try:
        if call.data == "menu":
            send_about_something(call.message, "Настройки бота", True, False, m.menu_markup)
            config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'start_markup'
    
        if call.data == "help":
            config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'start_markup'
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
            if config.bot_settings[str(call.message.chat.id)]['previous_markup'] == 'start_markup':
                bot.send_message(call.message.chat.id, f"Меню в чате № {call.message.chat.id}!",
                                 reply_markup=m.start_markup)
                config.bot_settings[str(call.message.chat.id)]['previous_markup'] = None
            elif config.bot_settings[str(call.message.chat.id)]['previous_markup'] == 'menu_markup':
                bot.send_message(call.message.chat.id, "Настройки бота", reply_markup=m.menu_markup)
                config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'start_markup'
            elif config.bot_settings[str(call.message.chat.id)]['previous_markup'] == 'forbidden_message_markup':
                bot.send_message(call.message.chat.id, "Запрещенные сообщения", reply_markup=m.forbidden_message_markup)
                config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'menu_markup'
            elif config.bot_settings[str(call.message.chat.id)]['previous_markup'] == 'bad_words':
                bot.send_message(call.message.chat.id, "Плохие слова", reply_markup=m.bad_words_markup)
                config.bot_settings[str(call.message.chat.id)]['previous_markup'] = 'menu_markup'
            bot.delete_message(call.message.chat.id, call.message.message_id)
            if config.bot_settings[str(call.message.chat.id)]['previous_message']:
                bot.delete_message(call.message.chat.id,
                                   config.bot_settings[str(call.message.chat.id)]['previous_message'])
                config.bot_settings[str(call.message.chat.id)]['previous_message'] = None
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
        send_about_something(
            message, ''.join(list_admins) + f'\nВсего админов: {len(list_admins)}')


@bot.message_handler(commands=['pause'])
def pause(message):
    if not checking_for_admin(message):
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
    logger.info(message.from_user.id)
    logger.info(message.text)
    message_words = set([word.lower() for word in message.text.split(' ')])
    if (str(message.from_user.id) in config.bot_settings[str(message.chat.id)]['controlled_users'].keys() and
            len(message_words.intersection(config.finance_words)) > 0):
        logger.info(f'Впойман криптоман {message.from_user.username}, удаляем!!!')
        send_about_something(
            message, f'Впойман криптоман {message.from_user.username}, удаляем!!!')
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
            send_about_something(
                message,
                f'Размещение формата {config.other_types_of_message[message.content_type]} запрещено! Удаляю!')
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
    #     config.log_file, maxBytes=(1048576*5), backupCount=3
    # )
    logger_formatter = logging.Formatter(
        '%(asctime)s : %(levelname)s : %(message)s',
        datefmt='%d-%m-%Y %H:%M:%S'
    )
    logger_handler.setFormatter(logger_formatter)
    logger.addHandler(logger_handler)
    return logger


def send_about_something(
        message,
        message_text='',
        dalete_previous_message=True,
        delete_this_message=True,
        markup=None,
):
    """Отправка сообщения и по умолчанию удаление предыдущего и отправленного."""
    info_message = bot.send_message(message.chat.id, message_text, reply_markup=markup)
    time.sleep(config.pause)
    if delete_this_message:
        bot.delete_message(message.chat.id, info_message.message_id)
    if dalete_previous_message:
        bot.delete_message(message.chat.id, message.message_id)


def save_bot_settings(bot_settings):    # сохранение списка настроек разных чатов в файл
    with open('bot_settings.json', 'w+') as file:
        file.write(json.dumps(bot_settings))
        file.close()


def main():
    thread = Thread(target=starting_tasks)
    thread.start()
    configuring_logging()
    if not os.path.exists('bot_settings.json'):
        save_bot_settings(config.bot_settings)
    # TODO переместить сюда или под IF __name__ переменные окружения и инстал бота
    bot.polling(none_stop=True)


if __name__ == "__main__":
    main()
