from telebot import types


start_markup = types.InlineKeyboardMarkup(row_width=2)
start_markup_btn1 = types.InlineKeyboardButton('Меню', callback_data='menu')
start_markup_btn2 = types.InlineKeyboardButton('HELP', callback_data='help')
start_markup_exit = types.InlineKeyboardButton('Выход', callback_data='exit')
start_markup.add(start_markup_btn1, start_markup_btn2, start_markup_exit)

exit_markup = types.InlineKeyboardMarkup(row_width=1)
exit_markup_btn = types.InlineKeyboardButton('Назад', callback_data='exit')
exit_markup.add(exit_markup_btn)

menu_markup = types.InlineKeyboardMarkup(row_width=2)
menu_markup_fb = types.InlineKeyboardButton('Запрещенные сообщения', callback_data='forbidden_message')
menu_markup_bw = types.InlineKeyboardButton('Плохие слова', callback_data='bad_words')
menu_markup_exit = types.InlineKeyboardButton('Назад', callback_data='exit')
menu_markup.add(menu_markup_fb, menu_markup_bw, menu_markup_exit)

forbidden_message_markup = types.InlineKeyboardMarkup(row_width=2)
forbidden_message_markup_audio = types.InlineKeyboardButton('Аудио', callback_data='audio')
forbidden_message_markup_photo = types.InlineKeyboardButton('Фото', callback_data='photo')
forbidden_message_markup_sticker = types.InlineKeyboardButton('Стикер', callback_data='sticker')
forbidden_message_markup_video = types.InlineKeyboardButton('Видео', callback_data='video')
forbidden_message_markup_video_note = types.InlineKeyboardButton('Видеосообщение', callback_data='video_note')
forbidden_message_markup_voice = types.InlineKeyboardButton('Голос', callback_data='voice')
forbidden_message_markup_exit = types.InlineKeyboardButton('Назад', callback_data='exit')
forbidden_message_markup.add(forbidden_message_markup_audio, forbidden_message_markup_photo, forbidden_message_markup_sticker,
                forbidden_message_markup_video, forbidden_message_markup_video_note, forbidden_message_markup_voice,
                forbidden_message_markup_exit)

bad_words_markup = types.InlineKeyboardMarkup(row_width=2)
bad_words_markup_add = types.InlineKeyboardButton('Добавить', callback_data='bad_words_add')
bad_words_markup_del = types.InlineKeyboardButton('Удалить', callback_data='bad_words_del')
bad_words_markup_exit = types.InlineKeyboardButton('Назад', callback_data='exit')
bad_words_markup.add(bad_words_markup_add, bad_words_markup_del, bad_words_markup_exit)

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

