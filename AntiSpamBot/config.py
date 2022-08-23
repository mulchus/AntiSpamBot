# конфигурация бота (константы)
token = '5430864257:AAHsIGljFlHg_BpYoW7o9AKqi4Q-hw6tNRc'

black_simvols = set('!"№;%:?*()_+-~!@#$^&\/<>{}[]|1234567890.,=')
user = ''
mat = []
all_types_message = ['audio', 'photo', 'sticker', 'video', 'video_note', 'voice']
bot_settings = {}
# bot_settings['forbidden_message'] = all_types_message # не идет - изменяется и переменная и словарь одновременно
bot_settings['forbidden_message'] = ['audio', 'photo', 'sticker', 'video', 'video_note', 'voice']
pause = 3

help = 'Бот супебот имеет следующие команды:' \
       '/addword слово - добавить слово в базу мата' \
       '/delword слово - удлить слово из базы мата' \
       '/show admins - вывести список админов чата' \
       '/pause число - изменить паузу отображения замечания'

#