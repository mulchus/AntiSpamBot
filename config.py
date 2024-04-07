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
pause = 2
command_from_markup = {}
last_messages = {}

help = '''Бот антиспам имеет следующие команды:
        /start - запуск/перезапуск бота
        /menu - вывод меню
        /addword <bad or finance> слово - добавить слово в базу
        /delword <bad or finance> слово - удалить слово из базы
        /show admins - вывести список админов чата
        /pause число (в секундах) - изменить паузу отображения сообщений'''
