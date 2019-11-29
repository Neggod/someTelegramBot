import telebot
import re


TOKEN = '773428065:AAFczy9ybU3d7cJzvmpaVscLSn6miZnd3vI'
bot = telebot.TeleBot(TOKEN)
hashtag_pattern = re.compile("(^|\s)#([^\d&%$_-]\S{2,49})\b")

@bot.message_handler(commands=['start', 'help'])
def hello_im_bot(message):
	text = 'Отправьте мне текст для поста в Instagram, и я пришлю в ответ с правильными переносами строк.'
	bot.send_message(message.chat.id, text)


@bot.message_handler(content_types=['text'])
def echo_text(message):
	text = message.text.replace('\n', '\u2800\n')
	len_text = len(text)
	hashtags = len(re.findall(hashtag_pattern, text))
	markup = telebot.types.InlineKeyboardMarkup()
	button = telebot.types.InlineKeyboardButton("{0} из 2200; # - {1}".format(len_text, hashtags),
												callback_data=("instatext", len_text, hashtags))
	markup.add(button)
	bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
	if call.data[0] == 'instatext':
		bot.answer_callback_query(callback_query_id=call.id, text='{0} из 2200; # - {1}'.format(*call.data[1:]))

if __name__ == '__main__':
	bot.polling(none_stop=True, timeout=100)

