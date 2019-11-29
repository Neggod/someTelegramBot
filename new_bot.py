import telebot

TOKEN = '773428065:AAFczy9ybU3d7cJzvmpaVscLSn6miZnd3vI'
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'help'])
def hello_im_bot(message):
	text = 'Отправьте мне текст для поста в Instagram, и я пришлю в ответ с правильными переносами строк.'
	bot.send_message(message.chat.id, text)


@bot.message_handler(content_types=['text'])
def echo_text(message):
	text = message.text.replace('\n', '\u2800\n')
	bot.send_message(message.chat.id, text)


if __name__ == '__main__':
	bot.polling(none_stop=True, timeout=100)
