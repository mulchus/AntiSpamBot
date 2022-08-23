from telebot import types

start_markup = types.InlineKeyboardMarkup(row_width=2)
start_markup_btn1 = types.InlineKeyboardButton('Меню', callback_data='menu')
start_markup_btn2 = types.InlineKeyboardButton('HELP', callback_data='help')
start_markup.add(start_markup_btn1, start_markup_btn2)

menu_markup = types.InlineKeyboardMarkup(row_width=2)
menu_markup_btn1 = types.InlineKeyboardButton('Запрещенные сообщения', callback_data='forbidden_message')
menu_markup_btn2 = types.InlineKeyboardButton('Плохие слова', callback_data='bad_words')
menu_markup.add(menu_markup_btn1, menu_markup_btn2)

forbidden_message_markup = types.InlineKeyboardMarkup(row_width=6)
forbidden_message_markup_audio = types.InlineKeyboardButton('Аудио', callback_data='audio')
forbidden_message_markup_photo = types.InlineKeyboardButton('Фото', callback_data='photo')
forbidden_message_markup_sticker = types.InlineKeyboardButton('Стикер', callback_data='sticker')
forbidden_message_markup_video = types.InlineKeyboardButton('Аудио', callback_data='video')
forbidden_message_markup_video_note = types.InlineKeyboardButton('Аудио', callback_data='video_note')
forbidden_message_markup_voice = types.InlineKeyboardButton('Аудио', callback_data='voice')
menu_markup.add(forbidden_message_markup_audio, forbidden_message_markup_photo, forbidden_message_markup_sticker,
                forbidden_message_markup_video, forbidden_message_markup_video_note, forbidden_message_markup_voice)

y_n_markup = types.InlineKeyboardMarkup(row_width=2)
y_n_markup_y = types.InlineKeyboardButton('Да', callback_data='yes')
y_n_markup_n = types.InlineKeyboardButton('Нет', callback_data='no')
y_n_markup.add(y_n_markup_y, y_n_markup_n)


# start_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='ПРИВЕТУСЫ')
# start_markup_btn1 = types.KeyboardButton('/start')
# start_markup_btn2 = types.KeyboardButton('/del')
# start_markup.add(start_markup_btn1, start_markup_btn2)
#
# end_markup = types.ReplyKeyboardRemove()

