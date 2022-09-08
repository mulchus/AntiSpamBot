# конфигурация бота (константы)
token = '5430864257:AAHsIGljFlHg_BpYoW7o9AKqi4Q-hw6tNRc'

black_simvols = set('!"№;%:?*()_+-~!@#$^&\/<>{}[]|1234567890.,=')
user = ''
mat = []
all_types_message = ['audio', 'photo', 'sticker', 'video', 'video_note', 'voice', 'document', 'caption', 'contact', 'location', 'venue', 'animation']
bot_settings = []
# bot_settings['forbidden_message'] = all_types_message # не идет - изменяется и переменная и словарь одновременно
#bot_settings['forbidden_message'] = ['audio', 'photo', 'sticker', 'video', 'video_note', 'voice']
pause = 3

help = '''Бот супербот имеет следующие команды: \n
        /start - запуск на сервере после сбоя бота \n
        /menu - вывод меню \n
        /addword слово - добавить слово в базу мата \n
        /delword слово - удлить слово из базы мата \n
        /show admins - вывести список админов чата \n
        /pause число - изменить паузу отображения замечания'''
