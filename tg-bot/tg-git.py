import telebot
import sqlite3
import requests
import base64
import uuid
from io import BytesIO
from telebot import types
import pandas as pd
from datetime import datetime
from yookassa import Configuration


Configuration.account_id = "494827"
Configuration.secret_key = "test_2gNRcPISYGzkhl9uWBq2R-VIaP6YLuOBQULNIsEQiKM"
REDIRECT_URL = 'https://yourwebsite.com/payment_success'  # URL для завершения оплаты

auth_string = f"{Configuration.account_id}:{Configuration.secret_key}"
auth_base64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
idempotence_key = str(uuid.uuid4())

# Основные настройки для API ЮKassa
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {auth_base64}"  # Используем корректно закодированную строку
}

# Передаем сюда токен, который получили от FatherBot
bot = telebot.TeleBot("7961802459:AAEQp7XwPCdbTEyKmdXxF-cTrxWsiqn_QKI")

# Хранилище данных о заказах
user_orders = {}

#----------------------------------------tg-bot---------------------------------------

# Обработка команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, f"Добро пожаловать в BaleMiscStore, {message.from_user.first_name}! 👋\n\n"
                                      "🛒 Мы рады видеть вас в нашем онлайн-магазине!\n"
                                      "🛍️ Здесь вы найдете широкий ассортимент товаров, чтобы удовлетворить все ваши нужды.\n\n"
                                      "Введите команду /help для получения информации.\n\n"
                                      "Наш сайт: https://sharlotta03.github.io/Project/"
                                      "Мы также рады сообщить, что у нас есть специальный бот, в который вы можете отправлять отзывы о нашей продукции: @review_balemicsstore_bot.\n"
                                      "Ваши отзывы публикуются в нашем канале, чтобы другие могли увидеть ваш опыт: https://t.me/review_balemicsstore\n\n"
                                      "Мы стараемся усовершенствовать бот нашего магазина, если у вас есть предложения или замечания, напишите нам: @BMS_support_bot")
    choose_category(message)
    user_orders[message.chat.id] = {}

@bot.message_handler(commands=['catalog'])
def seng_catalog(message):
    choose_category(message)


@bot.message_handler(commands=['contact'])
def contact(message):
    username = 'BMS_support_bot'
    contact_link = f"tg://resolve?domain={username}"

    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Связаться с нами", url=contact_link)
    markup.add(button)

    bot.send_message(message.chat.id, "Нажмите кнопку ниже, чтобы связаться с нами:", reply_markup=markup)


@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(message.chat.id, "ℹ️ <b>Помощь в BaleMicsStore</b>\n\n"
                                      "Добро пожаловать в раздел помощи! Здесь вы найдете информацию о том, как использовать наш онлайн-магазин.\n\n"
                                      "📦 <b>Доступные команды:</b>\n"
                                      "/start - Начать общение с ботом и получить приветственное сообщение.\n"
                                      "/catalog - Просмотреть каталог товаров и найти то, что вам нужно.\n"
                                      "/contact - Связаться с нашей службой поддержки для получения дополнительной информации.\n\n"
                                      "🛍️ <b>Покупка товаров:</b>\n"
                                      "Чтобы купить товар, просто перейдите в каталог, выберите нужный товар и следуйте инструкциям для оформления заказа.\n\n"
                                      "💬 <b>Служба поддержки:</b>\n"
                                      "Если у вас возникли вопросы, не стесняйтесь обращаться в службу поддержки: @BMS_support_bot\n"
                                      "- Мы доступны с понедельника по пятницу с 9:00 до 18:00.\n\n"
                                      "📞 <b>Обратная связь:</b>\n"
                                      "Мы всегда рады вашим отзывам! Если у вас есть предложения или замечания, напишите нам: @BMS_support_bot",
                     parse_mode="html")


def choose_category(message):
    markup = types.InlineKeyboardMarkup()
    categories = ['lipsticks', 'eyeshadow', 'eyeliner', 'concealer', 'foundation', 'mascara', 'powder']

    for category_name in categories:
        button = types.InlineKeyboardButton(text=category_name.capitalize(), callback_data=f"category_{category_name}")
        markup.add(button)

    bot.send_message(message.chat.id, "Выберите категорию товаров:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('category_'))
def handle_category_selection(call):
    category_name = call.data.split('_')[1]
    conn = sqlite3.connect('db/database.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT name, price, stock_quantity FROM {category_name}")
    products = cursor.fetchall()

    if products:
        product_list = '\n'.join([f"{name} - {price} руб." for name, price, stock_quantity in products])
        message = (f"Товары в категории {category_name.capitalize()}:\n\n"
                   f"Выберите товар, чтобы узнать больше:")

        markup = types.InlineKeyboardMarkup()
        for name, price, stock_quantity in products:
            button_text = f"{name} - {price} руб."
            button = types.InlineKeyboardButton(text=button_text, callback_data=f"product_{name}_{category_name}")
            markup.add(button)

        # Добавляем кнопку для возврата к выбору категорий
        back_button = types.InlineKeyboardButton(text="Обратно к каталогу", callback_data="back_to_categories")
        markup.add(back_button)

        bot.send_message(call.message.chat.id, message, reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, f'К сожалению, в категории {category_name.capitalize()} нет товаров.')

    conn.close()


# Обработчик кнопки "Назад к категориям"
@bot.callback_query_handler(func=lambda call: call.data == "back_to_categories")
def back_to_categories(call):
    choose_category(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
def handle_product_selection(call):
    product_name, category_name = call.data.split('_')[1:]
    conn = sqlite3.connect('db/database.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT price, description, image_path, stock_quantity FROM {category_name} WHERE name = ?",
                   (product_name,))
    product = cursor.fetchone()

    if product:
        price, description, image_path, stock_quantity = product
        if stock_quantity > 0:
            message = (f"<b>Название: {product_name}</b>\n"
                       f"<b>Цена: {price} руб.</b>\n"
                       f"<b>Описание:</b> {description}")

            if image_path:
                photo = BytesIO(image_path)
                markup = types.InlineKeyboardMarkup()
                pay_button = types.InlineKeyboardButton(text="Заказать", callback_data=f"pay_{product_name}_{price}")

                # Кнопка "Назад" возвращает пользователя к товарам этой категории
                back_button = types.InlineKeyboardButton(text="Назад",
                                                         callback_data=f"back_to_category_{category_name}")
                markup.add(pay_button, back_button)

                bot.send_photo(call.message.chat.id, photo, caption=message, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(call.message.chat.id, message)
        else:
            bot.send_message(call.message.chat.id, f"Ой, к сожалению, товар {product_name} закончился. 😔 Но не переживай, мы обязательно пополним запасы! Может быть, тебе понравится что-то другое? 🛍️")
    else:
        bot.send_message(call.message.chat.id, f"Товар '{product_name}' не найден.")

# Обработчик кнопки "Назад"
@bot.callback_query_handler(func=lambda call: call.data.startswith('back_to_category_'))
def handle_back_to_category(call):
    category_name = call.data.split('_')[3]  # Извлекаем название категории из callback_data
    conn = sqlite3.connect('db/database.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT name, price, stock_quantity FROM {category_name}")
    products = cursor.fetchall()

    if products:
        product_list = '\n'.join([f"{name} - {price} руб." for name, price, stock_quantity in products])
        message = (f"Товары в категории {category_name.capitalize()}:\n\n"
                   f"Выберите товар, чтобы узнать больше:")

        markup = types.InlineKeyboardMarkup()
        for name, price, stock_quantity in products:
            button_text = f"{name} - {price} руб."
            button = types.InlineKeyboardButton(text=button_text, callback_data=f"product_{name}_{category_name}")
            markup.add(button)

        # Кнопка для возврата назад
        back_button = types.InlineKeyboardButton(text="Назад", callback_data=f"back_to_category_{category_name}")
        markup.add(back_button)

        bot.send_message(call.message.chat.id, message, reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, f'К сожалению, в категории {category_name.capitalize()} нет товаров.')

    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def handle_order(call):
    product_name = call.data.split('_')[1]
    price = call.data.split('_')[2]

    # Сохраняем данные о заказе в памяти
    user_orders[call.message.chat.id] = {
        'product_name': product_name,
        'price': price
    }

    # Запрашиваем имя пользователя
    bot.send_message(call.message.chat.id,
                     "Пожалуйста, введите ваше имя:",
                     parse_mode="html")


@bot.message_handler(func=lambda message: message.chat.id in user_orders and 'user_name' not in user_orders[message.chat.id])
def get_user_name(message):
    # Проверка, что имя не было уже сохранено
    if 'user_name' not in user_orders[message.chat.id]:
        # Сохраняем имя пользователя, введенное вручную
        user_orders[message.chat.id]['user_name'] = message.text.strip()

    # Запрашиваем адрес доставки
    bot.send_message(message.chat.id,
                     "Теперь, пожалуйста, укажите ваш адрес доставки:\n",
                     parse_mode="html")

#---------------------------------------------------payment-----------------------------------------------------------

# Код для обработки запроса на оплату
@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def process_payment(call):
    try:
        # Учетные данные
        account_id = "494827"
        secret_key = "test_2gNRcPISYGzkhl9uWBq2R-VIaP6YLuOBQULNIsEQiKM"

        # Кодирование учетных данных
        credentials = f"{account_id}:{secret_key}".encode("utf-8")
        encoded_credentials = base64.b64encode(credentials).decode("utf-8")

        # Генерация Idempotence-Key
        idempotence_key = str(uuid.uuid4())

        # Заголовки для запроса
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded_credentials}",
            "Idempotence-Key": idempotence_key
        }

        # Данные для платежа (обратите внимание, что сумма указывается как строка с точкой)
        payment_data = {
            "amount": {
                "value": str(price),  # Пример суммы в рублях
                "currency": "RUB"
            },
            "capture": True,
            "confirmation": {
                "type": "redirect",
                "return_url": "https://yourwebsite.com/payment_success"  # Ссылка для возврата после оплаты
            },
            "description": "Тестовый платеж"
        }

        # Отправка запроса на создание платежа
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            json=payment_data,
            headers=headers
        )

        # Обработка ответа
        if response.status_code == 200:
            confirmation_url = response.json()["confirmation"]["confirmation_url"]
            bot.send_message(call.message.chat.id, f"Перейдите по ссылке для завершения платежа: {confirmation_url}")
        else:
            bot.send_message(call.message.chat.id, f"Ошибка при создании платежа: {response.json()}")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Произошла ошибка: {e}")

@bot.message_handler(func=lambda message: message.chat.id in user_orders and 'delivery_address' not in user_orders[message.chat.id])
def get_delivery_address(message):
    # Сохраняем адрес
    delivery_address = message.text.strip()
    user_orders[message.chat.id]['delivery_address'] = delivery_address

    # Получаем данные из user_orders
    user_id = message.chat.id
    user_name = user_orders[user_id]['user_name']  # Имя, которое пользователь ввел
    product_name = user_orders[user_id]['product_name']
    price = user_orders[user_id]['price']
    order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Сохраняем в таблицу
    save_order_to_excel(user_id, user_name, product_name, price, order_date, delivery_address)
    # Генерация ссылки для оплаты
    payment_link = generate_payment_link(price, user_id)

    # Отправка сообщения пользователю
    bot.send_message(message.chat.id, f"Ваш заказ почти оформлен!\n\n"
                                          f"📦 Товар: <b>{product_name}</b>\n"
                                          f"💰 Цена: <b>{price} руб.</b>\n"
                                          f"🏠 Адрес доставки: <b>{delivery_address}</b>\n\n"
                                          f"Перейдите по ссылке для завершения платежа: {payment_link}\n\n"
                                          f"В случае ошибки обращайтесь в службу поддержки: @BMS_support_bot  ",
                                          parse_mode="html")

def generate_payment_link(price, order_id):
        # Пример использования реального API для генерации ссылки на оплату
        account_id = "494827"
        secret_key = "test_2gNRcPISYGzkhl9uWBq2R-VIaP6YLuOBQULNIsEQiKM"

        # Кодирование учетных данных
        credentials = f"{account_id}:{secret_key}".encode("utf-8")
        encoded_credentials = base64.b64encode(credentials).decode("utf-8")

        # Генерация Idempotence-Key
        idempotence_key = str(uuid.uuid4())

        # Заголовки для запроса
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded_credentials}",
            "Idempotence-Key": idempotence_key
        }

        # Данные для платежа
        payment_data = {
            "amount": {
                "value": str(price),  # Преобразуем цену в строку
                "currency": "RUB"
            },
            "capture": True,
            "confirmation": {
                "type": "redirect",
                "return_url": "https://yourwebsite.com/payment_success"  # Укажите URL возврата
            },
            "description": f"Оплата заказа #{order_id}",
            "metadata": {
                "order_id": order_id  # Добавляем order_id в метаданные
            }
        }

        # Отправка запроса на создание платежа
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            json=payment_data,
            headers=headers
        )

        # Обработка ответа
        if response.status_code == 200:
            confirmation_url = response.json()["confirmation"]["confirmation_url"]
            return confirmation_url
        else:
            return "Произошла ошибка при создании ссылки для оплаты. Попробуйте позже."

#----------------------------------excel-----------------------------------------

# Сохранение данных в Excel
def save_order_to_excel(user_id, user_name, product_name, price, order_date, delivery_address):
    file_path = "orders.xlsx"
    try:
        # Пытаемся загрузить существующий файл Excel
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        # Если файл не существует, создаем новый DataFrame
        df = pd.DataFrame(columns=["User ID", "User Name", "Product Name", "Price", "Order Date", "Delivery Address"])

    # Добавляем новый заказ
    new_order = pd.DataFrame([[user_id, user_name, product_name, price, order_date, delivery_address]],
                             columns=["User ID", "User Name", "Product Name", "Price", "Order Date", "Delivery Address"])
    df = pd.concat([df, new_order], ignore_index=True)

    # Сохраняем данные обратно в Excel
    df.to_excel(file_path, index=False)

bot.polling(none_stop=True)
