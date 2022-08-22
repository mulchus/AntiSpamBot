from telebot import types

start_markup = types.InlineKeyboardMarkup(row_width=2)
start_markup_btn1 = types.InlineKeyboardButton('СТАРТ', callback_data='start')
start_markup_btn2 = types.InlineKeyboardButton('DEL', callback_data='del')
start_markup.add(start_markup_btn1, start_markup_btn2)



# start_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='ПРИВЕТУСЫ')
# start_markup_btn1 = types.KeyboardButton('/start')
# start_markup_btn2 = types.KeyboardButton('/del')
# start_markup.add(start_markup_btn1, start_markup_btn2)
#
# end_markup = types.ReplyKeyboardRemove()

