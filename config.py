# конфигурация бота (константы)

black_simvols = set('!"№;%:?*()_+-~!@#$^&\\/<>{}[]|1234567890.,=')
user = ''
mat = []
mat_file = 'wordfilter.txt'
finance_words = []
finance_words_file = 'finance_words.txt'
other_types_of_message = {'audio': 'аудио', 'photo': 'фото', 'sticker': 'стикер', 'video': 'видео',
                          'video_note': 'видеосообщение', 'voice': 'голос', 'document': 'документ',
                          'caption': 'подпись', 'contact': 'контакт', 'location': 'локация',
                          'venue': 'место встречи', 'animation': 'анимация (gif)'}
bot_settings = {}
pause = 1
command_from_markup = []

help = '''Бот супербот имеет следующие команды:
        /start - запуск на сервере после сбоя бота 
        /menu - вывод меню 
        /addword слово - добавить слово в базу мата 
        /delword слово - удлить слово из базы мата 
        /show admins - вывести список админов чата 
        /pause число (в секундах) - изменить паузу отображения замечания'''
