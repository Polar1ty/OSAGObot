import config
import telebot
from telebot import types
import urllib.parse
import dbworker
from datetime import datetime
import requests
import sqlite3 as sql
import json
import random

bot = telebot.TeleBot(config.TOKEN)

def log(message):
    print("<!------!>")
    print(datetime.now())
    print("Сообщение от {0} {1} (id = {2}) \n {3}".format(message.from_user.first_name,
                                                              message.from_user.last_name,
                                                              str(message.from_user.id), message.text))

def tariff_parsing(tariff):
    insurer_name = tariff['tariff']['insurer']['namePrint']
    payment = tariff['payment']
    franchise = tariff['tariff']['franchise']
    id = tariff['tariff']['id']
    type = tariff['tariff']['type']
    discounted_payment = tariff['discountedPayment']
    malus = tariff['tariff']['minBonusMalus']
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text='Оформити', callback_data=id)
    markup.add(button)
    return insurer_name, payment, franchise, id, markup, type, discounted_payment, malus


def city_into_dict(piece_of_json):
    """Парсинг названия города и его id из json-а"""
    dictionary = {
        'name_full': piece_of_json['nameFull'],
        'id': piece_of_json['id']
    }
    print(dictionary)
    return dictionary

# connection = sql.connect('DATABASE.sqlite')
# q = connection.cursor()
# q.execute('''
# 			CREATE TABLE "user" (
# 				'id' TEXT,
# 				'model_car' TEXT,
# 				'vin_code' TEXT,
# 				'number_car' TEXT,
# 				'category' TEXT,
# 				'car_year' TEXT,
# 				'surname' TEXT,
# 				'name' TEXT,
# 				'patronymic' TEXT,
# 				'date_of_birth' TEXT,
# 				'address' TEXT,
# 				'inn' TEXT,
# 				'email' TEXT,
# 				'phone' TEXT
# 			)''')
# connection.commit()
# q.close()
# connection.close()
#
# connection = sql.connect('DATABASE.sqlite')
# q = connection.cursor()
# q.execute('''
# 			CREATE TABLE "passport" (
# 			    'id' TEXT,
# 			    'series' TEXT,
# 			    'number' TEXT,
# 			    'date' TEXT,
# 			    'issued_by' TEXT
# 			)''')
# connection.commit()
# q.close()
# connection.close()

# connection = sql.connect('DATABASE.sqlite')
# q = connection.cursor()
# q.execute('''
# 			CREATE TABLE "utility" (
# 			    'id' TEXT,
# 			    'cities' TEXT,
# 			    'final_city_id' TEXT,
# 			    'tariffs' TEXT,
# 			    'tariff_type' TEXT,
# 			    'tariff_id' TEXT,
# 			    'tariff_payment' TEXT,
# 			    'tariff_discounted_payment' TEXT,
# 			    'tariff_name' TEXT,
# 			    'contract_ids' TEXT
# 			)''')
# connection.commit()
# q.close()
# connection.close()

utility = {}


def date_from_to(message):
    date_raw = message.date
    date_from = datetime.fromtimestamp(int(date_raw)).strftime('%Y-%m-%d %H:%M:%S')
    date_from_list = date_from.split(' ')
    day_plus_one = int(date_from_list[0].split('-')[2]) + 1
    date_plus_one_day = date_from_list[0].split('-')[0] + '-' + date_from_list[0].split('-')[1] + '-' + str(
        day_plus_one).zfill(2)  # Завтрашняя дата
    if str(day_plus_one) == '32' or str(day_plus_one) == '31':
        day_plus_one = '1'
        month_plus_one = int(date_from_list[0].split('-')[1]) + 1
        date_plus_one_day = date_from_list[0].split('-')[0] + '-' + str(month_plus_one).zfill(2) + '-' + str(
        day_plus_one).zfill(2)  # Завтрашняя дата
    date_from_ewa = date_plus_one_day + 'T22:00:00.000+0000'  # Дата в формате евы
    date_from_for_req = date_from_ewa.split('T')[0]  # Дата нужна для запрос на поиск полиса ОСАГО
    year_plus_one = int(date_from_ewa.split('-')[0]) + 1
    list_without_Y = date_from.split(' ')[0].split('-')[1:3]
    not_list = '-' + list_without_Y[0] + '-' + list_without_Y[1]
    date_to_ewa = str(year_plus_one) + not_list + 'T' + date_from_list[1] + '.000+0000'  # Дата в формате евы
    date_to_for_req = date_to_ewa.split('T')[0]  # Дата нужна для запрос на поиск полиса ОСАГО
    print(date_from_ewa)
    return date_from_for_req, date_to_for_req, date_from_ewa


headers = {
    'content-type': 'application/x-www-form-urlencoded',
}
data = {
    'email': config.email,
    'password': config.password  # hashed
}
response = requests.post('https://web.ewa.ua/ewa/api/v9/user/login', headers=headers, data=data)
# 'https://web.ewa.ua/ewa/api/v9/tariff/choose/policy?salePoint=32070&customerCategory=NATURAL&taxi=false&autoCategory=B1&registrationPlace=7&outsideUkraine=false&registrationType=PERMANENT_WITHOUT_OTK&dateFrom=2019-12-01&dateTo=2020-11-30&usageMonths=0
#                                                        salePoint        customerCategory         taxi          category            id                 outside_ua        registration_type                date_from_req_      date_to_req      usage_months
cookie = response.json()['sessionId']
sale_point = response.json()['user']['salePoint']['id']
user = response.json()['user']['id']
company_id = response.json()['user']['salePoint']['company']['id']
company_type = response.json()['user']['salePoint']['company']['type']
customer_category = 'NATURAL'
outside_ua = 'false'
taxi = 'false'
registration_type = 'PERMANENT_WITHOUT_OTK'
usage_mounths = '0'

cookies = {
    'JSESSIONID': cookie
}
headers = {
    'content-type': 'application/json'
}


@bot.message_handler(commands=['reset'])
def reset(message):
    try:
        dbworker.clear_db(message.chat.id)
        utility.pop(str(message.chat.id) + 'city1')
        utility.pop(str(message.chat.id) + 'city2')
        utility.pop(str(message.chat.id) + 'city3')
        utility.pop(str(message.chat.id) + 'city4')
        utility.pop(str(message.chat.id) + 'tariff1')
        utility.pop(str(message.chat.id) + 'tariff2')
        utility.pop(str(message.chat.id) + 'tariff3')
        utility.pop(str(message.chat.id) + 'tariff4')
        utility.pop(str(message.chat.id) + 'tariff5')
        utility.pop(str(message.chat.id) + 'tariff6')
        utility.pop(str(message.chat.id) + 'tariff7')
        utility.pop(str(message.chat.id) + 'tariff8')
        bot.send_message(message.chat.id,
                         '🚀База тимчасових станів очищена.\n Щоб почати оформлення спочатку напишіть /start')
    except FileNotFoundError:
        utility.pop(str(message.chat.id) + 'city1')
        utility.pop(str(message.chat.id) + 'city2')
        utility.pop(str(message.chat.id) + 'city3')
        utility.pop(str(message.chat.id) + 'city4')
        utility.pop(str(message.chat.id) + 'tariff1')
        utility.pop(str(message.chat.id) + 'tariff2')
        utility.pop(str(message.chat.id) + 'tariff3')
        utility.pop(str(message.chat.id) + 'tariff4')
        utility.pop(str(message.chat.id) + 'tariff5')
        utility.pop(str(message.chat.id) + 'tariff6')
        utility.pop(str(message.chat.id) + 'tariff7')
        utility.pop(str(message.chat.id) + 'tariff8')
        bot.send_message(message.chat.id, 'Ще не було скоєно ніяких дій🧐')
    except KeyError:
        bot.send_message(message.chat.id,
                         '🚀База тимчасових станів очищена.\n Щоб почати оформлення спочатку напишіть /start')


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, 'Зверніться в службу підтримки🏳\n +380XX-XXX-XX-XX')


@bot.message_handler(commands=['rules'])
def rules(message):
    bot.send_message(message.chat.id,
                     '❗Сессія триває 15 хвилин❗\nТобіж у вас є 15 хвилин, щоб ввести всі дані та дійти до оплати.\nУгода (далі - "правила", "угода") ресурсу та бота Zaraz Polis (далі - «Ресурс») Використання інформаційно-аналітичного ресурсу Zaraz Polis Користувачем означає, що Користувач приймає і зобов\'язується дотримуватися всіх нижченаведених умов цієї Угоди. Адміністрація ресурсу залишає за собою право вносити до Угоди зміни, які вступають в силу з моменту публікації. Подальше використання ресурсу після внесення подібних змін означає вашу згоду з ними.\n Повна угода за посиланям - http://zarazpolis.pp.ua/confidentiality.html')


@bot.message_handler(commands=['start'])
def hello(message):
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("SELECT EXISTS(SELECT 1 FROM user WHERE id='%s')" % message.from_user.id)
    results1 = q.fetchone()
    if results1[0] != 1:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button1 = types.KeyboardButton('Оформити ОСЦВ 🚗')
        markup.add(button1)
        bot.send_message(message.chat.id,
                         'Добридень {0.first_name}, вас вітає бот для оформлення ОСЦВ - {1.first_name}🚘 \n❗Зауважте, сессія триває 15 хвилин❗'.format(
                             message.from_user, bot.get_me()), reply_markup=markup)
        q.execute("INSERT INTO 'user' (id) VALUES ('%s')" % message.from_user.id)
        connection.commit()
        q.close()
        connection.close()
        utility = {
            str(message.chat.id) + 'city1': '',
            str(message.chat.id) + 'city2': '',
            str(message.chat.id) + 'city3': '',
            str(message.chat.id) + 'city4': '',
            str(message.chat.id) + 'final_city_id': '',
            str(message.chat.id) + 'tariff1': '',
            str(message.chat.id) + 'tariff2': '',
            str(message.chat.id) + 'tariff3': '',
            str(message.chat.id) + 'tariff4': '',
            str(message.chat.id) + 'tariff5': '',
            str(message.chat.id) + 'tariff6': '',
            str(message.chat.id) + 'tariff7': '',
            str(message.chat.id) + 'tariff8': '',
            str(message.chat.id) + 'tariff_type': '',
            str(message.chat.id) + 'tariff_id': '',
            str(message.chat.id) + 'tariff_payment': '',
            str(message.chat.id) + 'tariff_discounted_payment': '',
            str(message.chat.id) + 'tariff_name': '',
            str(message.chat.id) + 'contract_id': '',
            str(message.chat.id) + 'min_bonus_malus': '',
            str(message.chat.id) + 'car_year': '',
            str(message.chat.id) + 'order': ''
        }
    else:
        bot.send_message(message.chat.id, 'Я пам\'ятаю вас! Якщо все вірно натисніть - Так✅\n Якщо треба змінити особисту інформацію або ж паспортні дані натисніть - Змінити❎\nЩоб змінити транспортний засіб, або тариф. Натисніть - Спочатку🔄')
        connection.commit()
        q.close()
        connection.close()
        utility = {
            str(message.chat.id) + 'city1': '',
            str(message.chat.id) + 'city2': '',
            str(message.chat.id) + 'city3': '',
            str(message.chat.id) + 'city4': '',
            str(message.chat.id) + 'final_city_id': '',
            str(message.chat.id) + 'tariff1': '',
            str(message.chat.id) + 'tariff2': '',
            str(message.chat.id) + 'tariff3': '',
            str(message.chat.id) + 'tariff4': '',
            str(message.chat.id) + 'tariff5': '',
            str(message.chat.id) + 'tariff6': '',
            str(message.chat.id) + 'tariff7': '',
            str(message.chat.id) + 'tariff8': '',
            str(message.chat.id) + 'tariff_type': '',
            str(message.chat.id) + 'tariff_id': '',
            str(message.chat.id) + 'tariff_payment': '',
            str(message.chat.id) + 'tariff_discounted_payment': '',
            str(message.chat.id) + 'tariff_name': '',
            str(message.chat.id) + 'contract_id': '',
            str(message.chat.id) + 'min_bonus_malus': '',
            str(message.chat.id) + 'car_year': '',
            str(message.chat.id) + 'order': ''
        }
        prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Оформити ОСЦВ 🚗')
def auto_number(message):
    bot.send_message(message.chat.id, 'Введіть номерний знак ✍')
    dbworker.set_state(message.chat.id, config.States.S_NUMBER_CAR.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_NUMBER_CAR.value)
def asking_city(message):
    log(message)
    number_car = urllib.parse.quote(message.text)
    url = f'https://web.ewa.ua/ewa/api/v9/auto/mtibu/number?query={number_car}'
    response = requests.get(url, headers=headers, cookies=cookies)
    try:
        model = response.json()[0]['modelText']
        vin_code = str(response.json()[0]['bodyNumber']).upper()
        car_nmb = response.json()[0]['stateNumber']
        category = response.json()[0]['category']
        if category == 'D1' or category == 'D2':
            bot.send_message(message.chat.id,
                             'Страховка автобусів не підтримується. Напишіть /reset щоб почати спочатку')
        else:
            # запись в базу
            connection = sql.connect('DATABASE.sqlite')
            q = connection.cursor()
            q.execute("UPDATE user SET number_car='%s',category='%s',model_car='%s',vin_code='%s' WHERE id='%s'" % (
                message.text, category, model, vin_code, message.from_user.id))
            connection.commit()
            q.close()
            connection.close()
            bot.send_message(message.chat.id,
                             'Модель: {0}\nVIN-код: {1}\nНомерний знак: {2}'.format(model, vin_code, car_nmb))
            bot.send_message(message.chat.id, 'Введіть місто прописки🏢')
            dbworker.set_state(message.chat.id, config.States.S_SEARCH_CITY.value)
    except IndexError:
        bot.send_message(message.chat.id, 'Такого номера не існує. Спробуйте ще раз')


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_SEARCH_CITY.value)
def final_city(message):
    log(message)
    registration_city = urllib.parse.quote(message.text)
    url = f'https://web.ewa.ua/ewa/api/v9/place?country=UA&query={registration_city}'
    city_response = requests.get(url, headers=headers, cookies=cookies)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if city_response.json() == []:
        bot.send_message(message.chat.id, 'Таке місто не знайдено. Спробуйте ще раз')
        dbworker.set_state(message.chat.id, config.States.S_SEARCH_CITY.value)
    else:
        try:
            city1 = city_into_dict(city_response.json()[0])
            city2 = city_into_dict(city_response.json()[1])
            city3 = city_into_dict(city_response.json()[2])
            city4 = city_into_dict(city_response.json()[3])
        except IndexError:
            pass
        try:
            utility.update({str(message.chat.id) + 'city1': city1})
            utility.update({str(message.chat.id) + 'city2': city2})
            utility.update({str(message.chat.id) + 'city3': city3})
            utility.update({str(message.chat.id) + 'city4': city4})
        except UnboundLocalError:
            pass
        try:
            button1 = types.KeyboardButton(utility.get(str(message.chat.id) + 'city1')['name_full'])
            button2 = types.KeyboardButton(utility.get(str(message.chat.id) + 'city2')['name_full'])
            button3 = types.KeyboardButton(utility.get(str(message.chat.id) + 'city3')['name_full'])
            button4 = types.KeyboardButton(utility.get(str(message.chat.id) + 'city4')['name_full'])
        except TypeError:
            pass
        try:
            markup.add(button1)
            markup.add(button2)
            markup.add(button3)
            markup.add(button4)
        except:
            pass
        bot.send_message(message.chat.id, 'Виберіть місто🏙', reply_markup=markup)
        dbworker.set_state(message.chat.id, config.States.S_REGISTRATION_CITY.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_REGISTRATION_CITY.value)
def submitting(message):
    bot.send_message(message.chat.id, 'Список доступних полісів ОСАЦВ📊⬇')
    try:
        if message.text == utility.get(str(message.chat.id) + 'city1')['name_full']:
            id = utility.get(str(message.chat.id) + 'city1')['id']
            utility.update({str(message.chat.id) + 'final_city_id': id})
        if message.text == utility.get(str(message.chat.id) + 'city2')['name_full']:
            id = utility.get(str(message.chat.id) + 'city2')['id']
            utility.update({str(message.chat.id) + 'final_city_id': id})
        if message.text == utility.get(str(message.chat.id) + 'city3')['name_full']:
            id = utility.get(str(message.chat.id) + 'city3')['id']
            utility.update({str(message.chat.id) + 'final_city_id': id})
        if message.text == utility.get(str(message.chat.id) + 'city4')['name_full']:
            id = utility.get(str(message.chat.id) + 'city4')['id']
            utility.update({str(message.chat.id) + 'final_city_id': id})
    except IndexError:
        pass
    except TypeError:
        pass
    date_for_req = date_from_to(message)
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("SELECT * from user WHERE id='%s'" % message.from_user.id)
    results = q.fetchall()
    connection.commit()
    q.close()
    connection.close()
    url = f'https://web.ewa.ua/ewa/api/v9/tariff/choose/policy?salePoint={sale_point}&customerCategory={customer_category}&taxi={taxi}&autoCategory={str(results[0][4])}&registrationPlace={id}&outsideUkraine={outside_ua}&registrationType={registration_type}&dateFrom={date_for_req[0]}&dateTo={date_for_req[1]}&usageMonths={usage_mounths}'
    response = requests.get(url, headers=headers, cookies=cookies)
    try:
        tariff1 = tariff_parsing(response.json()[0])
        tariff2 = tariff_parsing(response.json()[1])
        tariff3 = tariff_parsing(response.json()[2])
        tariff4 = tariff_parsing(response.json()[3])
        tariff5 = tariff_parsing(response.json()[4])
        tariff6 = tariff_parsing(response.json()[5])
        tariff7 = tariff_parsing(response.json()[6])
        tariff8 = tariff_parsing(response.json()[7])
    except IndexError:
        pass
    try:
        utility.update({str(message.chat.id) + 'tariff1': tariff1})
        utility.update({str(message.chat.id) + 'tariff2': tariff2})
        utility.update({str(message.chat.id) + 'tariff3': tariff3})
        utility.update({str(message.chat.id) + 'tariff4': tariff4})
        utility.update({str(message.chat.id) + 'tariff5': tariff5})
        utility.update({str(message.chat.id) + 'tariff6': tariff6})
        utility.update({str(message.chat.id) + 'tariff7': tariff7})
        utility.update({str(message.chat.id) + 'tariff8': tariff8})
    except:
        pass
    try:
        bot.send_message(message.chat.id,
                     f'👔Страховик: {utility.get(str(message.chat.id) + "tariff8")[0]}\n💵Вартість: {utility.get(str(message.chat.id) + "tariff8")[1]}\n💼Франшиза: {utility.get(str(message.chat.id) + "tariff8")[2]}',
                     reply_markup=utility.get(str(message.chat.id) + "tariff8")[4])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                     f'👔Страховик: {utility.get(str(message.chat.id) + "tariff7")[0]}\n💵Вартість: {utility.get(str(message.chat.id) + "tariff7")[1]}\n💼Франшиза: {utility.get(str(message.chat.id) + "tariff7")[2]}',
                     reply_markup=utility.get(str(message.chat.id) + "tariff7")[4])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                     f'👔Страховик: {utility.get(str(message.chat.id) + "tariff6")[0]}\n💵Вартість: {utility.get(str(message.chat.id) + "tariff6")[1]}\n💼Франшиза: {utility.get(str(message.chat.id) + "tariff6")[2]}',
                     reply_markup=utility.get(str(message.chat.id) + "tariff6")[4])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                     f'👔Страховик: {utility.get(str(message.chat.id) + "tariff5")[0]}\n💵Вартість: {utility.get(str(message.chat.id) + "tariff5")[1]}\n💼Франшиза: {utility.get(str(message.chat.id) + "tariff5")[2]}',
                     reply_markup=utility.get(str(message.chat.id) + "tariff5")[4])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                     f'👔Страховик: {utility.get(str(message.chat.id) + "tariff4")[0]}\n💵Вартість: {utility.get(str(message.chat.id) + "tariff4")[1]}\n💼Франшиза: {utility.get(str(message.chat.id) + "tariff4")[2]}',
                     reply_markup=utility.get(str(message.chat.id) + "tariff4")[4])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                     f'👔Страховик: {utility.get(str(message.chat.id) + "tariff3")[0]}\n💵Вартість: {utility.get(str(message.chat.id) + "tariff3")[1]}\n💼Франшиза: {utility.get(str(message.chat.id) + "tariff3")[2]}',
                     reply_markup=utility.get(str(message.chat.id) + "tariff3")[4])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                     f'👔Страховик: {utility.get(str(message.chat.id) + "tariff2")[0]}\n💵Вартість: {utility.get(str(message.chat.id) + "tariff2")[1]}\n💼Франшиза: {utility.get(str(message.chat.id) + "tariff2")[2]}',
                     reply_markup=utility.get(str(message.chat.id) + "tariff2")[4])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                     f'👔Страховик: {(utility.get(str(message.chat.id) + "tariff1"))[0]}\n💵Вартість: {(utility.get(str(message.chat.id) + "tariff1"))[1]}\n💼Франшиза: {(utility.get(str(message.chat.id) + "tariff1"))[2]}',
                     reply_markup=utility.get(str(message.chat.id) + "tariff1")[4])
    except TypeError:
        pass


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        print(call.data, type(call.data))
        print(utility.get(str(call.message.chat.id) + 'tariff1')[3], type(utility.get(str(call.message.chat.id) + 'tariff1')[3]))
        if int(call.data) == utility.get(str(call.message.chat.id) + 'tariff1')[3]:
            utility.update(
                {str(call.message.chat.id) + 'tariff_id': utility.get(str(call.message.chat.id) + "tariff1")[3]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_type': utility.get(str(call.message.chat.id) + "tariff1")[5]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_payment': utility.get(str(call.message.chat.id) + "tariff1")[1]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_discounted_payment': utility.get(str(call.message.chat.id) + "tariff1")[6]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_name': utility.get(str(call.message.chat.id) + "tariff1")[0]})
            utility.update(
                {str(call.message.chat.id) + 'min_bonus_malus': utility.get(str(call.message.chat.id) + "tariff1")[7]})
            if utility.get(str(call.message.chat.id) + 'car_year') == None:
                bot.send_message(call.message.chat.id,
                             'Відмінно! Теперь введіть будь ласка рік випуску вашого авто(пункт B.2 тех паспорта)↘')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Напишіть ваше прізвище(українською):')
                dbworker.set_state(call.message.chat.id, config.States.S_SURNAME.value)
        if int(call.data) == utility.get(str(call.message.chat.id) + 'tariff2')[3]:
            utility.update(
                {str(call.message.chat.id) + 'tariff_id': utility.get(str(call.message.chat.id) + "tariff2")[3]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_type': utility.get(str(call.message.chat.id) + "tariff2")[5]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_payment': utility.get(str(call.message.chat.id) + "tariff2")[1]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_discounted_payment':
                     utility.get(str(call.message.chat.id) + "tariff2")[6]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_name': utility.get(str(call.message.chat.id) + "tariff2")[0]})
            utility.update(
                {str(call.message.chat.id) + 'min_bonus_malus': utility.get(str(call.message.chat.id) + "tariff2")[7]})
            if utility.get(str(call.message.chat.id) + 'car_year') == None:
                bot.send_message(call.message.chat.id,
                                 'Відмінно! Теперь введіть будь ласка рік випуску вашого авто(пункт B.2 тех паспорта)↘')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Напишіть ваше прізвище(українською):')
                dbworker.set_state(call.message.chat.id, config.States.S_SURNAME.value)
        if int(call.data) == utility.get(str(call.message.chat.id) + 'tariff3')[3]:
            utility.update(
                {str(call.message.chat.id) + 'tariff_id': utility.get(str(call.message.chat.id) + "tariff3")[3]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_type': utility.get(str(call.message.chat.id) + "tariff3")[5]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_payment': utility.get(str(call.message.chat.id) + "tariff3")[1]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_discounted_payment':
                     utility.get(str(call.message.chat.id) + "tariff3")[6]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_name': utility.get(str(call.message.chat.id) + "tariff3")[0]})
            utility.update(
                {str(call.message.chat.id) + 'min_bonus_malus': utility.get(str(call.message.chat.id) + "tariff3")[7]})
            if utility.get(str(call.message.chat.id) + 'car_year') == None:
                bot.send_message(call.message.chat.id,
                                 'Відмінно! Теперь введіть будь ласка рік випуску вашого авто(пункт B.2 тех паспорта)↘')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Напишіть ваше прізвище(українською):')
                dbworker.set_state(call.message.chat.id, config.States.S_SURNAME.value)
        if int(call.data) == utility.get(str(call.message.chat.id) + 'tariff4')[3]:
            utility.update(
                {str(call.message.chat.id) + 'tariff_id': utility.get(str(call.message.chat.id) + "tariff4")[3]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_type': utility.get(str(call.message.chat.id) + "tariff4")[5]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_payment': utility.get(str(call.message.chat.id) + "tariff4")[1]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_discounted_payment':
                     utility.get(str(call.message.chat.id) + "tariff4")[6]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_name': utility.get(str(call.message.chat.id) + "tariff4")[0]})
            utility.update(
                {str(call.message.chat.id) + 'min_bonus_malus': utility.get(str(call.message.chat.id) + "tariff4")[7]})
            if utility.get(str(call.message.chat.id) + 'car_year') == None:
                bot.send_message(call.message.chat.id,
                                 'Відмінно! Теперь введіть будь ласка рік випуску вашого авто(пункт B.2 тех паспорта)↘')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Напишіть ваше прізвище(українською):')
                dbworker.set_state(call.message.chat.id, config.States.S_SURNAME.value)
        if int(call.data) == utility.get(str(call.message.chat.id) + 'tariff5')[3]:
            utility.update(
                {str(call.message.chat.id) + 'tariff_id': utility.get(str(call.message.chat.id) + "tariff5")[3]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_type': utility.get(str(call.message.chat.id) + "tariff5")[5]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_payment': utility.get(str(call.message.chat.id) + "tariff5")[1]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_discounted_payment':
                     utility.get(str(call.message.chat.id) + "tariff5")[6]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_name': utility.get(str(call.message.chat.id) + "tariff5")[0]})
            utility.update(
                {str(call.message.chat.id) + 'min_bonus_malus': utility.get(str(call.message.chat.id) + "tariff5")[7]})
            if utility.get(str(call.message.chat.id) + 'car_year') == None:
                bot.send_message(call.message.chat.id,
                                 'Відмінно! Теперь введіть будь ласка рік випуску вашого авто(пункт B.2 тех паспорта)↘')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Напишіть ваше прізвище(українською):')
                dbworker.set_state(call.message.chat.id, config.States.S_SURNAME.value)
        if int(call.data) == utility.get(str(call.message.chat.id) + 'tariff6')[3]:
            utility.update(
                {str(call.message.chat.id) + 'tariff_id': utility.get(str(call.message.chat.id) + "tariff6")[3]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_type': utility.get(str(call.message.chat.id) + "tariff6")[5]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_payment': utility.get(str(call.message.chat.id) + "tariff6")[1]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_discounted_payment':
                     utility.get(str(call.message.chat.id) + "tariff6")[6]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_name': utility.get(str(call.message.chat.id) + "tariff6")[0]})
            utility.update(
                {str(call.message.chat.id) + 'min_bonus_malus': utility.get(str(call.message.chat.id) + "tariff6")[7]})
            if utility.get(str(call.message.chat.id) + 'car_year') == None:
                bot.send_message(call.message.chat.id,
                                 'Відмінно! Теперь введіть будь ласка рік випуску вашого авто(пункт B.2 тех паспорта)↘')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Напишіть ваше прізвище(українською):')
                dbworker.set_state(call.message.chat.id, config.States.S_SURNAME.value)
        if int(call.data) == utility.get(str(call.message.chat.id) + 'tariff7')[3]:
            utility.update(
                {str(call.message.chat.id) + 'tariff_id': utility.get(str(call.message.chat.id) + "tariff7")[3]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_type': utility.get(str(call.message.chat.id) + "tariff7")[5]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_payment': utility.get(str(call.message.chat.id) + "tariff7")[1]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_discounted_payment':
                     utility.get(str(call.message.chat.id) + "tariff7")[6]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_name': utility.get(str(call.message.chat.id) + "tariff7")[0]})
            utility.update(
                {str(call.message.chat.id) + 'min_bonus_malus': utility.get(str(call.message.chat.id) + "tariff7")[7]})
            if utility.get(str(call.message.chat.id) + 'car_year') == None:
                bot.send_message(call.message.chat.id,
                                 'Відмінно! Теперь введіть будь ласка рік випуску вашого авто(пункт B.2 тех паспорта)↘')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Напишіть ваше прізвище(українською):')
                dbworker.set_state(call.message.chat.id, config.States.S_SURNAME.value)
        if int(call.data) == utility.get(str(call.message.chat.id) + 'tariff8')[3]:
            utility.update(
                {str(call.message.chat.id) + 'tariff_id': utility.get(str(call.message.chat.id) + "tariff8")[3]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_type': utility.get(str(call.message.chat.id) + "tariff8")[5]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_payment': utility.get(str(call.message.chat.id) + "tariff8")[1]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_discounted_payment':
                     utility.get(str(call.message.chat.id) + "tariff8")[6]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_name': utility.get(str(call.message.chat.id) + "tariff8")[0]})
            utility.update(
                {str(call.message.chat.id) + 'min_bonus_malus': utility.get(str(call.message.chat.id) + "tariff8")[7]})
            if utility.get(str(call.message.chat.id) + 'car_year') == None:
                bot.send_message(call.message.chat.id,
                                 'Відмінно! Теперь введіть будь ласка рік випуску вашого авто(пункт B.2 тех паспорта)↘')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Напишіть ваше прізвище(українською):')
                dbworker.set_state(call.message.chat.id, config.States.S_SURNAME.value)
    except IndexError:
        pass
    except TypeError:
        pass


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_CAR_YEAR.value)
def car_year_taking(message):
    log(message)
    car_year = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET car_year='%s' WHERE id='%s'" % (car_year, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    # database
    bot.send_message(message.chat.id, 'Напишіть ваше прізвище(українською):')
    dbworker.set_state(message.chat.id, config.States.S_SURNAME.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_SURNAME.value)
def surname_taking(message):
    log(message)
    surname = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET surname='%s' WHERE id='%s'" % (surname, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    # database
    bot.send_message(message.chat.id, "Напишіть ваше ім'я (українською):")
    dbworker.set_state(message.chat.id, config.States.S_NAME.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_NAME.value)
def name_taking(message):
    log(message)
    name = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET name='%s' WHERE id='%s'" % (name, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    # database
    bot.send_message(message.chat.id, 'Як вас звати по-батькові?(українською):')
    dbworker.set_state(message.chat.id, config.States.S_PATRONYMIC.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_PATRONYMIC.value)
def patronymic_taking(message):
    log(message)
    patronymic = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET patronymic='%s' WHERE id='%s'" % (patronymic, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    # database
    bot.send_message(message.chat.id, 'Напишіть дату вашого народження(в форматі РРРР-ММ-ДД):')
    dbworker.set_state(message.chat.id, config.States.S_DATE_OF_BIRTH.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_DATE_OF_BIRTH.value)
def date_of_birth_taking(message):
    log(message)
    date_of_birth = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET date_of_birth='%s' WHERE id='%s'" % (date_of_birth, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    # database
    bot.send_message(message.chat.id, 'Напишіть адресу вашої прописки (в форматі:Місто,Вулиця,Дім,Квартира):')
    dbworker.set_state(message.chat.id, config.States.S_ADDRESS.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ADDRESS.value)
def address_taking(message):
    log(message)
    address = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET address='%s' WHERE id='%s'" % (address, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    # database
    bot.send_message(message.chat.id, 'Введіть ваш ІНН(10 цифр):')
    dbworker.set_state(message.chat.id, config.States.S_INN.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_INN.value)
def inn_taking(message):
    log(message)
    inn = message.text
    if len(inn) != 10:
        bot.send_message(message.chat.id, 'Ідентифікаційний код має містити 10 цифр. Спробуйте ще')
        dbworker.set_state(message.chat.id, config.States.S_INN.value)
    else:
        connection = sql.connect('DATABASE.sqlite')
        q = connection.cursor()
        q.execute("UPDATE user SET inn='%s' WHERE id='%s'" % (inn, message.from_user.id))
        connection.commit()
        q.close()
        connection.close()
        # database
        bot.send_message(message.chat.id, 'Введіть ваш email(сюди буде висланий поліс):')
        dbworker.set_state(message.chat.id, config.States.S_EMAIL.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_EMAIL.value)
def email_taking(message):
    log(message)
    email = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET email='%s' WHERE id='%s'" % (email, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    # database
    bot.send_message(message.chat.id, 'Введіть ваш мобільний номер телефону(повинен починатися на +380):')
    dbworker.set_state(message.chat.id, config.States.S_PHONE.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_PHONE.value)
def phone_taking(message):
    log(message)
    phone = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET phone='%s' WHERE id='%s'" % (phone, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    bot.send_message(message.chat.id, 'Введіть серію паспорта: ')
    dbworker.set_state(message.chat.id, config.States.S_SERIES.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_SERIES.value)
def series_taking(message):
    log(message)
    series = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("SELECT EXISTS(SELECT 1 FROM passport WHERE id='%s')" % message.from_user.id)
    results1 = q.fetchone()
    if results1[0] != 1:
        q.execute("INSERT INTO 'passport' (id) VALUES ('%s')" % message.from_user.id)
    q.execute("UPDATE passport SET series='%s' WHERE id='%s'" % (series, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    bot.send_message(message.chat.id, 'Введіть номер паспорта: ')
    dbworker.set_state(message.chat.id, config.States.S_NUMBER.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_NUMBER.value)
def number_taking(message):
    log(message)
    number = message.text
    if len(number) != 6:
        bot.send_message(message.chat.id, 'Номер паспорта має містити 6 цифр. Спробуйте ще')
        dbworker.set_state(message.chat.id, config.States.S_NUMBER.value)
    else:
        connection = sql.connect('DATABASE.sqlite')
        q = connection.cursor()
        q.execute("UPDATE passport SET number='%s' WHERE id='%s'" % (number, message.from_user.id))
        connection.commit()
        q.close()
        connection.close()
        bot.send_message(message.chat.id, 'Введіть дату видачі паспорта(в формате ГГГГ-ММ-ДД): ')
        dbworker.set_state(message.chat.id, config.States.S_DATE.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_DATE.value)
def date_taking(message):
    log(message)
    date = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE passport SET date='%s' WHERE id='%s'" % (date, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    bot.send_message(message.chat.id, 'Введіть орган видачі паспорта: ')
    dbworker.set_state(message.chat.id, config.States.S_ISSUED_BY.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ISSUED_BY.value)
def issued_taking(message):
    log(message)
    issued_by = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE passport SET issued_by='%s' WHERE id='%s'" % (issued_by, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


def prefinal(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button1 = types.KeyboardButton('Так✔')
    button2 = types.KeyboardButton('Змінити✖')
    button3 = types.KeyboardButton('Спочатку🔄')
    markup.add(button1, button2, button3)
    bot.send_message(message.chat.id, 'Підтвердіть правильність введених данних')
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("SELECT * from user WHERE id='%s'" % message.from_user.id)
    results = q.fetchall()
    q.execute("SELECT * from passport WHERE id='%s'" % message.from_user.id)
    results1 = q.fetchall()
    connection.commit()
    q.close()
    connection.close()
    bot.send_message(message.chat.id,
                     f"Інформація про авто🚗⬇\n\nМодель:  {results[0][1]}\nVIN-код:  {results[0][2]}\nНомер машини:  {results[0][3]}\nКатегорія:  {results[0][4]}\nРік випуску:  {results[0][5]}\n\nОсобиста інформація🤵⬇\n\nПрізвище:  {results[0][6]}\nІм'я:  {results[0][7]}\nПо-батькові:  {results[0][8]}\nДата народждения:  {results[0][9]}\nАдреса прописки:  {results[0][10]}\nІНН:  {results[0][11]}\nEMAIL:  {results[0][12]}\nТелефон:  {results[0][13]}\n\nПаспортні дані📖⬇\n\nСерія паспорта:  {results1[0][1]}\nНомер паспорта:  {results1[0][2]}\nДата видачі:  {results1[0][3]}\nОрган видачі:  {results1[0][4]}",
                     reply_markup=markup)
    dbworker.clear_db(message.chat.id)


@bot.message_handler(func=lambda message: message.text == 'Спочатку🔄')
def again(message):
    auto_number(message)


@bot.message_handler(func=lambda message: message.text == 'Так✔')
def yes(message):
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("SELECT * from user WHERE id='%s'" % message.from_user.id)
    results = q.fetchall()
    q.execute("SELECT * from passport WHERE id='%s'" % message.from_user.id)
    results1 = q.fetchall()
    model = urllib.parse.quote(results[0][1])
    connection.commit()
    q.close()
    connection.close()

    bot.send_message(message.chat.id, 'Добре!👍 Переходжу до формування договору📝\nЗачекайте⏳',
                     reply_markup=types.ReplyKeyboardRemove())

    d = date_from_to(message)

    url = f'https://web.ewa.ua/ewa/api/v9/auto_model/maker_and_model?query={model}'
    response = requests.get(url, headers=headers, cookies=cookies)
    try:
        model_id = response.json()[0]['id']
        marka_id = response.json()[0]['autoMaker']['id']
        modelText = results[0][1]
        contract_data = {
            'type': 'epolicy',
            'salePoint': {'id': sale_point,
                          'company': {
                              'type': company_type,
                              'id': company_id
                          }},
            'user': {'id': user},
            'payment': str(utility.get(str(message.chat.id) + 'tariff_payment')),
            'brokerDiscountedPayment': str(utility.get(str(message.chat.id) + 'tariff_discounted_payment')),
            'tariff': {
                'type': str(utility.get(str(message.chat.id) + 'tariff_type')),
                'id': str(utility.get(str(message.chat.id) + 'tariff_id'))
            },
            'date': datetime.fromtimestamp(int(message.date)).strftime('%Y-%m-%d'),
            'dateFrom': d[2],
            'customer': {
                'code': results[0][11],
                'nameLast': results[0][7],
                'nameFirst': results[0][6],
                'nameMiddle': results[0][8],
                'address': results[0][10],
                'phone': results[0][13],
                'email': results[0][12],
                'birthDate': results[0][9],
                'document': {
                    'type': 'PASSPORT',
                    'series': results1[0][1],
                    'number': results1[0][2],
                    'date': results1[0][3],
                    'issuedBy': results1[0][4]
                }
            },
            'insuranceObject': {
                'type': 'auto',
                'category': results[0][4],
                'model': {
                    'id': model_id,
                    'autoMaker': {
                        'id': marka_id
                    }
                },
                'modelText': modelText,
                'bodyNumber': results[0][2],
                'stateNumber': str(results[0][3]).upper(),
                'registrationPlace': {
                    'id': str(utility.get(str(message.chat.id) + 'final_city_id')),
                },
                'registrationType': registration_type,  # нужно где-то брать
                'year': results[0][5],
            },
            'state': 'DRAFT',
            'bonusMalus': utility.get(str(message.chat.id) + 'min_bonus_malus')
        }
        print(model_id, marka_id)
        print(contract_data['date'])
        print(contract_data['dateFrom'])
    except IndexError:
        modelText = results[0][1]
        contract_data = {
            'type': 'epolicy',
            'salePoint': {'id': sale_point,
                          'company': {
                              'type': company_type,
                              'id': company_id
                          }},
            'user': {'id': user},
            'payment': str(utility.get(str(message.chat.id) + 'tariff_payment')),
            'brokerDiscountedPayment': str(utility.get(str(message.chat.id) + 'tariff_discounted_payment')),
            'tariff': {
                'type': str(utility.get(str(message.chat.id) + 'tariff_type')),
                'id': str(utility.get(str(message.chat.id) + 'tariff_id'))
            },
            'date': datetime.fromtimestamp(int(message.date)).strftime('%Y-%m-%d'),
            'dateFrom': d[2],
            'customer': {
                'code': results[0][11],
                'nameLast': results[0][7],
                'nameFirst': results[0][6],
                'nameMiddle': results[0][8],
                'address': results[0][10],
                'phone': results[0][13],
                'email': results[0][12],
                'birthDate': results[0][9],
                'document': {
                    'type': 'PASSPORT',
                    'series': results1[0][1],
                    'number': results1[0][2],
                    'date': results1[0][3],
                    'issuedBy': results1[0][4]
                }
            },
            'insuranceObject': {
                'type': 'auto',
                'category': results[0][4],
                'modelText': modelText,
                'bodyNumber': results[0][2],
                'stateNumber': str(results[0][3]).upper(),
                'registrationPlace': {
                    'id': utility.get(str(message.chat.id) + 'final_city_id'),
                },
                'registrationType': registration_type,  # нужно где-то брать
                'year': results[0][5],
            },
            'state': 'DRAFT',
            'bonusMalus': utility.get(str(message.chat.id) + 'min_bonus_malus')
        }
        print(f"Нету информации о машине {modelText}")
        print(contract_data['date'])
        print(contract_data['dateFrom'])
    url_for_save_contract = 'https://web.ewa.ua/ewa/api/v9/contract/save'
    json_string = json.dumps(contract_data)
    r = requests.post(url_for_save_contract, headers=headers, cookies=cookies,
                      data=json_string)  # Перевод договора в состояние ЧЕРНОВИК
    print(r)
    bad_data = 0
    try:
        id_contract = r.json()['id']
        utility.update({str(message.chat.id) + 'contract_id': id_contract})
    except KeyError:
        print('Какое-то из значений было введено неправильно')
        bot.send_message(message.chat.id, 'Якісь дані були введені некоректно. Спробуйте ще')
        bad_data = 1
    if bad_data == 1:
        auto_number(message)
    else:
        contract = utility.get(str(message.chat.id) + 'contract_id')
        url_for_req = f'https://web.ewa.ua/ewa/api/v9/contract/{contract}/state/REQUEST'
        r1 = requests.post(url_for_req, headers=headers, cookies=cookies)  # перевод договора в состояние ЗАЯВЛЕН
        print(r1)
        url_for_otp = f'https://web.ewa.ua/ewa/api/v9/contract/{contract}/otp/send?customer=true'
        r_otp = requests.get(url_for_otp, headers=headers, cookies=cookies)
        print(r_otp)
        bot.send_message(message.chat.id,
                         'Вам на телефон було відправлено СМС з паролем для укладання договору📲\nВведіть пароль з повідомлення✏')
        dbworker.set_state(message.chat.id, config.States.S_OTP.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_OTP.value)
def otp(message):
    otp = message.text
    contract = utility.get(str(message.chat.id) + 'contract_id')
    url_otp_2 = f'https://web.ewa.ua/ewa/api/v9/contract/{contract}/otp?customer={otp}'
    r_otp_2 = requests.get(url_otp_2, headers=headers, cookies=cookies)
    print(r_otp_2)
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("SELECT * from user WHERE id='%s'" % message.from_user.id)
    results = q.fetchall()
    connection.commit()
    q.close()
    connection.close()

    # WAY FOR PAY

    random_integer = random.randint(10000, 99999)
    payment = utility.get(str(message.chat.id) + 'tariff_payment')
    product_name = f"ОСАЦВ від - {utility.get(str(message.chat.id) + 'tariff_name')}"
    # # # запрос в платежную систему
    # stri = f'zarazpolis_pp_ua;https://t.me/osago_insurance_bot;order{str(random_integer)};{message.date};1;UAH;{product_name};1;1'  # payment
    # key = config.wfp_key
    # hash = hmac.new(key.encode('utf-8'), stri.encode('utf-8')).hexdigest()
    # print(hash)
    # d = {
    #     "transactionType": "CREATE_INVOICE",
    #     "merchantAccount": "zarazpolis_pp_ua",
    #     "merchantDomainName": "https://t.me/osago_insurance_bot",
    #     "merchantSignature": hash,
    #     "apiVersion": 1,
    #     "language": 'ru',
    #     "serviceUrl": 'http://serviceurl.com',
    #     "orderReference": f'order{str(random_integer)}',  # тут мое рандомное число
    #     "orderDate": message.date,
    #     "amount": '1',  # r.json()['insuranceObject']['payment']
    #     "currency": "UAH",
    #     "orderTimeout": 86400,
    #     "productName": [product_name],
    #     "productPrice": ['1'],  # r.json()['insuranceObject']['payment']
    #     "productCount": [1],
    #     "clientFirstName": results[0][6],
    #     "clientLastName": results[0][7],
    #     # "clientEmail": results[0][12],
    #     "clientPhone": results[0][13]
    # }
    # d_dumped = json.dumps(d)
    # print(d)
    # r2 = requests.post('https://api.wayforpay.com/api', data=d_dumped)
    # print(r2)
    # print(r2.json())
    # invoice = r2.json()['invoiceUrl']
    # bot.send_message(message.chat.id, f'Для оплаты перейдите по ссылке💳⬇\n{invoice}')
    # # Здесь должна быть проверка статуса платежа
    # stri1 = f'zarazpolis_pp_ua;order{str(random_integer)}'
    # hash1 = hmac.new(key.encode('utf-8'), stri1.encode('utf-8')).hexdigest()
    # print(hash1)
    # d1 = {
    #     "transactionType": "CHECK_STATUS",
    #     "merchantAccount": "zarazpolis_pp_ua",
    #     "orderReference": f'order{str(random_integer)}',
    #     "merchantSignature": hash1,
    #     "apiVersion": 1
    # }
    # d1_dumped = json.dumps(d1)
    # print(d1)
    # bot.send_message(message.chat.id,
    #                  'Після оплати очікуйте підтверждження платежа⏳(зазвичай це займає ~5-10 хвилин)\nКоли платіж буди прийнятий вам на електронну пошту прийде повідомлення📧')
    # while True:
    #     r3 = requests.post('https://api.wayforpay.com/api', data=d1_dumped)
    #     print(r3.json())
    #     print(r3.json()['transactionStatus'])
    #     if r3.json()['transactionStatus'] == 'Approved':
    #         print('Платёж прошел. Всё найс')
    #         bot.send_message(message.chat.id,
    #                          'Платіж пройшов успішно!📠 Незабаром ваш на пошту прийде ваш поліс ОСАЦВ📬')
    #         url_for_emi = f'https://web.ewa.ua/ewa/api/v9/contract/{contract_ids[0]}/state/EMITTED'
    #         rf = requests.post(url_for_emi, headers=headers, cookies=cookies)  # перевод договора в состояние ЗАЯВЛЕН
    #         print(rf)
    #         print(rf.json())
    #         break
    #     if r3.json()['transactionStatus'] == 'Expired':
    #         bot.send_message(message.chat.id,
    #                          'Закінчився термін оплати. Перезапустіть бота /reset щоб почати оформлення з початку')
    #         break

    # LIQPAY
    order = f'order{str(random_integer)}'
    amount = round(payment * 100.)
    bot.send_invoice(message.chat.id,
                     title=product_name,
                     description='Страховий поліс ОСАЦВ',
                     invoice_payload=order,
                     provider_token=config.liqpay_token,
                     currency='UAH',
                     prices=[types.LabeledPrice(label='Полис', amount=amount)],
                     start_parameter='true',
                     photo_url='https://2.bp.blogspot.com/-u0_YERWDpQI/UiD3FMlV1yI/AAAAAAAAHJA/LhZtLmVkTvw/s1600/Mantenimiento.jpg')
    utility.update({str(message.chat.id) + 'order': order})


@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types='successful_payment')
def process_successful_payment(message: types.Message):
    print(message.successful_payment)
    # total_amount = message.successful_payment['total_amount']  TypeError: 'SuccessfulPayment' object is not subscriptable
    # payload = message.successful_payment['invoice_payload']
    print('Платёж прошел. Всё найс')
    contract = utility.get(str(message.chat.id) + 'contract_id')
    url_for_emi = f'https://web.ewa.ua/ewa/api/v9/contract/{contract}/state/EMITTED'
    rf = requests.post(url_for_emi, headers=headers, cookies=cookies)  # перевод договора в состояние ЗАКЛЮЧЕН
    print(rf)
    bot.send_message(message.chat.id,
                     'Платіж пройшов успішно!📠 Незабаром ваш на пошту прийде ваш поліс ОСЦВ📬')
    dbworker.clear_db(message.chat.id)
    try:
        utility.pop(str(message.chat.id) + 'city1')
        utility.pop(str(message.chat.id) + 'city2')
        utility.pop(str(message.chat.id) + 'city3')
        utility.pop(str(message.chat.id) + 'city4')
        utility.pop(str(message.chat.id) + 'tariff1')
        utility.pop(str(message.chat.id) + 'tariff2')
        utility.pop(str(message.chat.id) + 'tariff3')
        utility.pop(str(message.chat.id) + 'tariff4')
        utility.pop(str(message.chat.id) + 'tariff5')
        utility.pop(str(message.chat.id) + 'tariff6')
        utility.pop(str(message.chat.id) + 'tariff7')
        utility.pop(str(message.chat.id) + 'tariff8')
        utility.pop(str(message.chat.id) + 'car_year')
    except KeyError:
        pass



@bot.message_handler(func=lambda message: message.text == 'Змінити✖')
def no(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button1 = types.KeyboardButton('Рік випуску')
    button2 = types.KeyboardButton('Прізвище')
    button3 = types.KeyboardButton("І'мя")
    button4 = types.KeyboardButton('По-батькові')
    button5 = types.KeyboardButton('Дата нарождения')
    button6 = types.KeyboardButton('Адреса прописки')
    button7 = types.KeyboardButton('ІНН')
    button8 = types.KeyboardButton('EMAIL')
    button9 = types.KeyboardButton('Телефон')
    button10 = types.KeyboardButton('Серія паспорта')
    button11 = types.KeyboardButton('Номер паспорта')
    button12 = types.KeyboardButton('Дата видачі')
    button13 = types.KeyboardButton('Орган видачі')
    markup.add(button1, button2, button3, button4, button5, button6, button7, button8, button9, button10, button11,
               button12, button13)
    bot.send_message(message.chat.id, 'Виберіть що хочете змінити:', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Рік випуску')
def car_year_set(message):
    bot.send_message(message.chat.id, 'Введіть рік випуску:')
    dbworker.set_state(message.chat.id, config.States.S1_CAR_YEAR.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_CAR_YEAR.value)
def car_year_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET car_year='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Прізвище')
def surname_set(message):
    bot.send_message(message.chat.id, 'Введіть ваше прізвище(українською):')
    dbworker.set_state(message.chat.id, config.States.S1_SURNAME.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_SURNAME.value)
def surname_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET surname='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == "І'мя")
def name_set(message):
    bot.send_message(message.chat.id, 'Введіть ваше імя(українською):')
    dbworker.set_state(message.chat.id, config.States.S1_NAME.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_NAME.value)
def name_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET name='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'По-батькові')
def patronymic_set(message):
    bot.send_message(message.chat.id, 'Введіть ваше імя по батькові(українською):')
    dbworker.set_state(message.chat.id, config.States.S1_PATRONYMIC.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_PATRONYMIC.value)
def patronymic_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET patronymic='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Дата нарождения')
def date_set(message):
    bot.send_message(message.chat.id, 'Введіть вашу дату нарождения(в форматі РРРР-ММ-ДД):')
    dbworker.set_state(message.chat.id, config.States.S1_DATE_OF_BIRTH.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_DATE_OF_BIRTH.value)
def date_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET date_of_birth='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Адреса прописки')
def address_set(message):
    bot.send_message(message.chat.id, 'Введіть вашу адресу прописки(в форматі "Місто,Вулиця,Дім,Квартира"):')
    dbworker.set_state(message.chat.id, config.States.S1_ADDRESS.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_ADDRESS.value)
def address_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET address='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'ІНН')
def inn_set(message):
    bot.send_message(message.chat.id, 'Введіть ваш ІНН(10 цифр):')
    dbworker.set_state(message.chat.id, config.States.S1_INN.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_INN.value)
def inn_taking_again(message):
    log(message)
    v = message.text
    if len(v) != 10:
        bot.send_message(message.chat.id, 'Ідентифікаційний код має містити 10 цифр. Спробуйте ще')
        inn_set(message)
    else:
        connection = sql.connect('DATABASE.sqlite')
        q = connection.cursor()
        q.execute("UPDATE user SET inn='%s' WHERE id='%s'" % (v, message.from_user.id))
        connection.commit()
        q.close()
        connection.close()
        prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'EMAIL')
def email_set(message):
    bot.send_message(message.chat.id, 'Введіть ваш email(сюди буде висланий поліс):')
    dbworker.set_state(message.chat.id, config.States.S1_EMAIL.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_EMAIL.value)
def email_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET email='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Телефон')
def phone_set(message):
    bot.send_message(message.chat.id, 'Введіть ваш  моібльний номер телефону:')
    dbworker.set_state(message.chat.id, config.States.S1_PHONE.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_PHONE.value)
def phone_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET phone='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Серія паспорта')
def series_set(message):
    bot.send_message(message.chat.id, 'Введіть вашу серію паспорта:')
    dbworker.set_state(message.chat.id, config.States.S1_SERIES.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_SERIES.value)
def series_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE passport SET series='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Номер паспорта')
def number_set(message):
    bot.send_message(message.chat.id, 'Введіть ваш номер паспорта:')
    dbworker.set_state(message.chat.id, config.States.S1_NUMBER.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_NUMBER.value)
def number_taking_again(message):
    log(message)
    v = message.text
    if len(v) != 6:
        bot.send_message(message.chat.id, 'Номер паспорта має містити 6 цифр. Спробуйте ще')
        dbworker.set_state(message.chat.id, config.States.S1_NUMBER.value)
    else:
        connection = sql.connect('DATABASE.sqlite')
        q = connection.cursor()
        q.execute("UPDATE passport SET number='%s' WHERE id='%s'" % (v, message.from_user.id))
        connection.commit()
        q.close()
        connection.close()
        prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Дата видачі')
def date_set(message):
    bot.send_message(message.chat.id, 'Введіть дату видачі паспорта(в форматі РРРР-ММ-ДД):')
    dbworker.set_state(message.chat.id, config.States.S1_DATE.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_DATE.value)
def date_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE passport SET date='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Орган видачі')
def issued_set(message):
    bot.send_message(message.chat.id, 'Введіть орган видачі паспорта:')
    dbworker.set_state(message.chat.id, config.States.S1_ISSUED_BY.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_ISSUED_BY.value)
def issued_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE passport SET issued_by='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


"""
    Баги:
        Иногда не работает поиск по номеру авто
    Перспективы:
        распознавание документа(тех паспорт авто)
        BankID
        Напоминалка за 2 до конца полиса
        QR - code с Liqpay для оплаты с компа
"""

# BOT RUNNING
if __name__ == '__main__':
    bot.polling(none_stop=True)
