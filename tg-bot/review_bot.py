import telebot

API_TOKEN = '7611824592:AAGuohtEp0-doeaxbb445RXG03gmuIhadwc'  # Ваш API токен
CHANNEL_ID = '@review_balemicsstore'  # ID или юзернейм вашего канала

# Инициализация бота
bot = telebot.TeleBot(API_TOKEN)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! 👋\n\n"
                          "Добро пожаловать в наш бот для отправки отзывов!\n\n"
                          "Вы можете предложить свой отзыв о нашем магазине или поделиться фото.\n"
                          "Просто отправьте текст или фото, и мы отправим его для модерации в наш канал. 📝📸\n\n"
                          "Спасибо, что используете наш сервис! 😊")

# Обработчик текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    text = message.text
    bot.send_message(CHANNEL_ID, text)
    bot.reply_to(message, "Ваш текст был отправлен в канал!")


# Обработчик фото
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    # Получаем фото
    photo = message.photo[-1].file_id  # Самое крупное фото
    # Получаем текст от пользователя
    text = message.caption if message.caption else "Без текста."

    # Отправляем фото и текст в канал
    bot.send_photo(CHANNEL_ID, photo, caption=text)
    bot.reply_to(message, "Ваш отзыв с фото был отправлен в канал!")


# Запуск бота
bot.polling(none_stop=True)
