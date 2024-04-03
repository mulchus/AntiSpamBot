# конфигурация бота (константы)

black_simvols = set('!"№;%:?*()_+-~!@#$^&\\/<>{}[]|1234567890.,=')
user = ''
mat = []
financial_words = []
other_types_of_message = ['audio', 'photo', 'sticker', 'video', 'video_note', 'voice', 'document', 'caption', 'contact', 'location', 'venue', 'animation']
bot_settings = {}
# bot_settings['forbidden_message'] = forbidden_messages # не идет - изменяется и переменная и словарь одновременно
#bot_settings['forbidden_message'] = ['audio', 'photo', 'sticker', 'video', 'video_note', 'voice']
pause = 1
command_from_markup = []

help = '''Бот супербот имеет следующие команды:
        /start - запуск на сервере после сбоя бота 
        /menu - вывод меню 
        /addword слово - добавить слово в базу мата 
        /delword слово - удлить слово из базы мата 
        /show admins - вывести список админов чата 
        /pause число (в секундах) - изменить паузу отображения замечания'''
