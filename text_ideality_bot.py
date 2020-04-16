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
import tg_analytic
import os
import time

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
    tg_analytic.statistics(message.chat.id, message.text)
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
                         'Тепер все має працювати як слід!\nДля початку роботи натисніть /start')
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
    except KeyError:
        bot.send_message(message.chat.id,
                         'Тепер все має працювати як слід!\nДля початку роботи натисніть /start')


@bot.message_handler(commands=['help'])
def help(message):
    tg_analytic.statistics(message.chat.id, message.text)
    bot.send_message(message.chat.id, 'Напишіть ваше питання, воно буде надіслане до оператора служби підтримки.')
    dbworker.set_state(message.chat.id, config.States.S_HELP.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_HELP.value)
def getting_help_msg(message):
    help_msg = message.text
    try:
        doc_type = utility.get(str(message.chat.id) + 'doc_type')
    except KeyError:
        doc_type = ' '
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("SELECT * from user WHERE id='%s'" % message.from_user.id)
    results = q.fetchall()
    q.execute("SELECT * from passport WHERE id='%s'" % message.from_user.id)
    results1 = q.fetchall()
    connection.commit()
    q.close()
    connection.close()
    try:
        model = results[0][1]
    except IndexError:
        model = ''
    try:
        VIN = results[0][2]
    except IndexError:
        VIN = ''
    try:
        reg_number = results[0][3]
    except IndexError:
        reg_number = ''
    try:
        category = results[0][4]
    except IndexError:
        category = ''
    try:
        year_car = results[0][5]
    except IndexError:
        year_car = ''
    try:
        surname = results[0][6]
    except IndexError:
        surname = ''
    try:
        name = results[0][7]
    except IndexError:
        name = ''
    try:
        patronymic = results[0][8]
    except IndexError:
        patronymic = ''
    try:
        birth = results[0][9]
    except IndexError:
        birth = ''
    try:
        reg_addres = results[0][10]
    except IndexError:
        reg_addres = ''
    try:
        INN = results[0][11]
    except IndexError:
        INN = ''
    try:
        email = results[0][12]
    except IndexError:
        email = ''
    try:
        phone = results[0][13]
    except IndexError:
        phone = ''
    try:
        series = results1[0][1]
    except IndexError:
        series = ''
    try:
        doc_num = results1[0][2]
    except IndexError:
        doc_num = ''
    try:
        date = results1[0][3]
    except IndexError:
        date = ''
    try:
        organ = results1[0][4]
    except IndexError:
        organ = ''
    with open(f'{message.from_user.id}.txt', 'a', encoding='utf8') as f:
        f.write(
            f"# -*- coding: utf8 -*-\n\n\nДані автомобіля🚘\n\nМодель:  {model}\nVIN-код:  {VIN}\nРеєстраційний номер:  {reg_number}\nКатегорія:  {category}\nРік випуску:  {year_car}\n\nВаша особиста інформація😉\n\nПрізвище:  {surname}\nІм'я:  {name}\nПо-батькові:  {patronymic}\nДата народждения:  {birth}\nАдреса реєстрації:  {reg_addres}\nІНПП:  {INN}\nEMAIL:  {email}\nТелефон:  {phone}\n\nДані вашого документа📖\n\nТип документа: {doc_type}\nСерія/Запис документа:  {series}\nНомер документа:  {doc_num}\nДата видачі:  {date}\nОрган, що видав:  {organ}")
        time.sleep(1)
    bot.send_document(config.help_chat_id, open(f'{message.from_user.id}.txt', 'r', encoding='utf8'),
                      caption=f'Автор питання: @{message.from_user.username}\nПитання: {help_msg}')
    os.remove(f'{message.from_user.id}.txt')
    bot.send_message(message.chat.id, 'Ваше питання в обробці. Незабаром Вам відповість наш оператор')
    dbworker.clear_db(message.chat.id)


@bot.message_handler(commands=['rules'])
def rules(message):
    tg_analytic.statistics(message.chat.id, message.text)
    bot.send_message(message.chat.id,
                     'У вас є 15 хвилин для того, щоби завершити оплату та отримання полісу у форматі PDF, тому радимо одразу мати під рукою усі необхідні документи - свідоцтво про реєстрацію транспортного засобу (техпаспорт), паспорт, id-карту або посвідчення водія.\n\nВводити інформацію слід українською мовою, аби у майбутньому уникнути будь-яких непорозумінь при настанні страхового випадку.\n\nОплата відбувається за допомогою платіжного сервісу Liqpay безпосередньо з мобільної версії Telegram, при використанні desktop-версії оплата наразі не підтримується (у розробці).\n\nПри виникненні технічних помилок потрібно перезавантажити бота, натиснувши /reset, і почати спочатку.\n\nПри виникненні питань фінансового характеру зверніться до служби підтримки, натиснувши /help.\n\nДоговір оферти за посиланням: http://zarazpolis.pp.ua/confidentiality.html')


@bot.message_handler(commands=['start'])
def hello(message):
    tg_analytic.statistics(message.chat.id, message.text)
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("SELECT EXISTS(SELECT 1 FROM user WHERE id='%s')" % message.from_user.id)
    results1 = q.fetchone()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button1 = types.KeyboardButton('ПІДІБРАТИ ПОЛІС 🚘')
    markup.add(button1)
    bot.send_message(message.chat.id,
                     'Вітаємо, {0.first_name}! Я - бот {1.first_name}, готовий працювати.\nПочати - /start\nПерезавантажити бота - /reset\nПравила користування - /rules\nДопомога - /help'.format(
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
        str(message.chat.id) + 'doc_type': '',
        str(message.chat.id) + 'contract_id': '',
        str(message.chat.id) + 'min_bonus_malus': '',
        str(message.chat.id) + 'car_year': '',
        str(message.chat.id) + 'order': '',
        str(message.chat.id) + 'car_changer': ''
    }

    # Saved for better times

    # else:
    #     bot.send_message(message.chat.id,
    #                      'Я пам\'ятаю вас! Якщо все вірно натисніть - Так✅\n Якщо треба змінити особисту інформацію або ж паспортні дані натисніть - Змінити❎\nЩоб змінити транспортний засіб, або тариф. Натисніть - Спочатку🔄')
    #     connection.commit()
    #     q.close()
    #     connection.close()
    #     utility = {
    #         str(message.chat.id) + 'city1': '',
    #         str(message.chat.id) + 'city2': '',
    #         str(message.chat.id) + 'city3': '',
    #         str(message.chat.id) + 'city4': '',
    #         str(message.chat.id) + 'final_city_id': '',
    #         str(message.chat.id) + 'tariff1': '',
    #         str(message.chat.id) + 'tariff2': '',
    #         str(message.chat.id) + 'tariff3': '',
    #         str(message.chat.id) + 'tariff4': '',
    #         str(message.chat.id) + 'tariff5': '',
    #         str(message.chat.id) + 'tariff6': '',
    #         str(message.chat.id) + 'tariff7': '',
    #         str(message.chat.id) + 'tariff8': '',
    #         str(message.chat.id) + 'tariff_type': '',
    #         str(message.chat.id) + 'tariff_id': '',
    #         str(message.chat.id) + 'tariff_payment': '',
    #         str(message.chat.id) + 'tariff_discounted_payment': '',
    #         str(message.chat.id) + 'tariff_name': '',
    #         str(message.chat.id) + 'doc_type': '',
    #         str(message.chat.id) + 'contract_id': '',
    #         str(message.chat.id) + 'min_bonus_malus': '',
    #         str(message.chat.id) + 'car_year': '',
    #         str(message.chat.id) + 'order': ''
    #     }
    #     prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'ПІДІБРАТИ ПОЛІС 🚘')
def auto_number(message):
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
    except KeyError:
        pass
    bot.send_message(message.chat.id, 'Введіть реєстраційний номер авто (АА0000АА):✍')
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
                             '🚌Страховка автобусів не підтримується.')
            auto_number(message)
        elif utility.get(str(message.chat.id) + 'car_changer') == '1':
            connection = sql.connect('DATABASE.sqlite')
            q = connection.cursor()
            q.execute("UPDATE user SET number_car='%s',category='%s',model_car='%s',vin_code='%s' WHERE id='%s'" % (
                message.text, category, model, vin_code, message.from_user.id))
            connection.commit()
            q.close()
            connection.close()
            bot.send_message(message.chat.id,
                             'Модель: {0}\nVIN-код: {1}\nРеєстраційний номер: {2}'.format(model, vin_code, car_nmb))
            utility.pop(str(message.chat.id) + 'car_changer')
            car_year_set(message)
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
                             'Модель: {0}\nVIN-код: {1}\nРеєстраційний номер: {2}'.format(model, vin_code, car_nmb))
            bot.send_message(message.chat.id, 'Введіть місце реєстрації авто:✍')
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
    bot.send_message(message.chat.id, 'Виберіть ваш найкращий варіант:👇')
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
                         f'👔 {utility.get(str(message.chat.id) + "tariff8")[0]}\n💼 Франшиза: {utility.get(str(message.chat.id) + "tariff8")[2]}\n\n💵 Вартість: {utility.get(str(message.chat.id) + "tariff8")[1]}',
                         reply_markup=utility.get(str(message.chat.id) + "tariff8")[4])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                         f'👔 {utility.get(str(message.chat.id) + "tariff7")[0]}\n💼 Франшиза: {utility.get(str(message.chat.id) + "tariff7")[2]}\n\n💵 Вартість: {utility.get(str(message.chat.id) + "tariff7")[1]}',
                         reply_markup=utility.get(str(message.chat.id) + "tariff7")[4])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                         f'👔 {utility.get(str(message.chat.id) + "tariff6")[0]}\n💼 Франшиза: {utility.get(str(message.chat.id) + "tariff6")[2]}\n\n💵 Вартість: {utility.get(str(message.chat.id) + "tariff6")[1]}',
                         reply_markup=utility.get(str(message.chat.id) + "tariff6")[4])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                         f'👔 {utility.get(str(message.chat.id) + "tariff5")[0]}\n💼 Франшиза: {utility.get(str(message.chat.id) + "tariff5")[2]}\n\n💵 Вартість: {utility.get(str(message.chat.id) + "tariff5")[1]}',
                         reply_markup=utility.get(str(message.chat.id) + "tariff5")[4])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                         f'👔 {utility.get(str(message.chat.id) + "tariff4")[0]}\n💼 Франшиза: {utility.get(str(message.chat.id) + "tariff4")[2]}\n\n💵 Вартість: {utility.get(str(message.chat.id) + "tariff4")[1]}',
                         reply_markup=utility.get(str(message.chat.id) + "tariff4")[4])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                         f'👔 {utility.get(str(message.chat.id) + "tariff3")[0]}\n💼 Франшиза: {utility.get(str(message.chat.id) + "tariff3")[2]}\n\n💵 Вартість: {utility.get(str(message.chat.id) + "tariff3")[1]}',
                         reply_markup=utility.get(str(message.chat.id) + "tariff3")[4])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                         f'👔 {utility.get(str(message.chat.id) + "tariff2")[0]}\n💼 Франшиза: {utility.get(str(message.chat.id) + "tariff2")[2]}\n\n💵 Вартість: {utility.get(str(message.chat.id) + "tariff2")[1]}',
                         reply_markup=utility.get(str(message.chat.id) + "tariff2")[4])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                         f'👔 {utility.get(str(message.chat.id) + "tariff1")[0]}\n💼 Франшиза: {utility.get(str(message.chat.id) + "tariff1")[2]}\n\n💵 Вартість: {utility.get(str(message.chat.id) + "tariff1")[1]}',
                         reply_markup=utility.get(str(message.chat.id) + "tariff1")[4])
    except TypeError:
        pass


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        print(call.data, type(call.data))
        print(utility.get(str(call.message.chat.id) + 'tariff1')[3],
              type(utility.get(str(call.message.chat.id) + 'tariff1')[3]))
        if int(call.data) == utility.get(str(call.message.chat.id) + 'tariff1')[3]:
            utility.update(
                {str(call.message.chat.id) + 'tariff_id': utility.get(str(call.message.chat.id) + "tariff1")[3]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_type': utility.get(str(call.message.chat.id) + "tariff1")[5]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_payment': utility.get(str(call.message.chat.id) + "tariff1")[1]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_discounted_payment':
                     utility.get(str(call.message.chat.id) + "tariff1")[6]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_name': utility.get(str(call.message.chat.id) + "tariff1")[0]})
            utility.update(
                {str(call.message.chat.id) + 'min_bonus_malus': utility.get(str(call.message.chat.id) + "tariff1")[7]})
            if utility.get(str(call.message.chat.id) + 'car_year') is None:
                bot.send_message(call.message.chat.id,
                                 'Добре!👍\nВведіть рік випуску автомобіля\n(пункт B.2 свідоцтва про реєстрацію ТЗ)✍')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Введіть своє прізвище (українською):')
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
            if utility.get(str(call.message.chat.id) + 'car_year') is None:
                bot.send_message(call.message.chat.id,
                                 'Добре!👍\nВведіть рік випуску автомобіля\n(пункт B.2 свідоцтва про реєстрацію ТЗ)✍')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Введіть своє прізвище (українською):')
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
            if utility.get(str(call.message.chat.id) + 'car_year') is None:
                bot.send_message(call.message.chat.id,
                                 'Добре!👍\nВведіть рік випуску автомобіля\n(пункт B.2 свідоцтва про реєстрацію ТЗ)✍')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Введіть своє прізвище (українською):')
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
            if utility.get(str(call.message.chat.id) + 'car_year') is None:
                bot.send_message(call.message.chat.id,
                                 'Добре!👍\nВведіть рік випуску автомобіля\n(пункт B.2 свідоцтва про реєстрацію ТЗ)✍')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Введіть своє прізвище (українською):')
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
            if utility.get(str(call.message.chat.id) + 'car_year') is None:
                bot.send_message(call.message.chat.id,
                                 'Добре!👍\nВведіть рік випуску автомобіля\n(пункт B.2 свідоцтва про реєстрацію ТЗ)✍')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Введіть своє прізвище (українською):')
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
            if utility.get(str(call.message.chat.id) + 'car_year') is None:
                bot.send_message(call.message.chat.id,
                                 'Добре!👍\nВведіть рік випуску автомобіля\n(пункт B.2 свідоцтва про реєстрацію ТЗ)✍')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Введіть своє прізвище (українською):')
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
            if utility.get(str(call.message.chat.id) + 'car_year') is None:
                bot.send_message(call.message.chat.id,
                                 'Добре!👍\nВведіть рік випуску автомобіля\n(пункт B.2 свідоцтва про реєстрацію ТЗ)✍')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Введіть своє прізвище (українською):')
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
            if utility.get(str(call.message.chat.id) + 'car_year') is None:
                bot.send_message(call.message.chat.id,
                                 'Добре!👍\nВведіть рік випуску автомобіля\n(пункт B.2 свідоцтва про реєстрацію ТЗ)✍')
                dbworker.set_state(call.message.chat.id, config.States.S_CAR_YEAR.value)
            else:
                bot.send_message(call.message.chat.id, 'Введіть своє прізвище (українською):')
                dbworker.set_state(call.message.chat.id, config.States.S_SURNAME.value)
    except IndexError:
        pass
    except TypeError:
        pass


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_CAR_YEAR.value)
def car_year_taking(message):
    log(message)
    car_year = message.text
    if len(car_year) != 4:
        bot.send_message(message.chat.id, 'Рік випуску має містити 4 цифри. Наприклад 2020. Спробуйте ще.')
        dbworker.set_state(message.chat.id, config.States.S_CAR_YEAR.value)
    else:
        connection = sql.connect('DATABASE.sqlite')
        q = connection.cursor()
        q.execute("UPDATE user SET car_year='%s' WHERE id='%s'" % (car_year, message.from_user.id))
        connection.commit()
        q.close()
        connection.close()
        # database
        bot.send_message(message.chat.id, 'Введіть ваше прізвище(українською):✍')
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
    bot.send_message(message.chat.id, "Введіть своє ім'я (українською):✍")
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
    bot.send_message(message.chat.id, 'Введіть своє по-батькові (українською):✍')
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
    bot.send_message(message.chat.id, 'Введіть дату свого народження\n\n(у форматі РРРР-ММ-ДД):✍')
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
    bot.send_message(message.chat.id, 'Введіть адресу своєї реєстрації\n\n(у форматі: місто, вулиця, дім, квартира):✍')
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
    bot.send_message(message.chat.id, 'Введіть свій ІНПП (10 цифр):✍')
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
        bot.send_message(message.chat.id, 'Введіть email, на який ви отриматє електронний поліс:✍')
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
    bot.send_message(message.chat.id,
                     'Введіть номер телефону, на який ми вишлемо СМС для підпису електронного полісу (має починатися на +380):✍')
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
    # bot.send_message(message.chat.id, 'Введіть серію паспорта (2 літери):✍')
    # dbworker.set_state(message.chat.id, config.States.S_SERIES.value)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button1 = types.KeyboardButton('Паспорт 📖')
    button2 = types.KeyboardButton('ID-карта')
    button3 = types.KeyboardButton('Посвідчення водія 🚘')
    markup.add(button1, button2, button3)
    bot.send_message(message.chat.id, 'Ваш документ:', reply_markup=markup)
    dbworker.clear_db(message.chat.id)


# ----------------------------------------------------------------------------------------------------------------------


@bot.message_handler(func=lambda message: message.text == 'Паспорт 📖')
def passport(message):
    utility.update({str(message.chat.id) + 'doc_type': 'PASSPORT'})
    bot.send_message(message.chat.id, 'Введіть серію паспорта (2 літери):✍')
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
    bot.send_message(message.chat.id, 'Введіть номер паспорта (6 цифр):✍')
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
        bot.send_message(message.chat.id, 'Введіть дату видачі паспорта (у форматі РРРР-ММ-ДД):✍')
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
    bot.send_message(message.chat.id, 'Введіть орган, що видав паспорт:✍')
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


# ----------------------------------------------------------------------------------------------------------------------


@bot.message_handler(func=lambda message: message.text == 'ID-карта')
def id_card(message):
    utility.update({str(message.chat.id) + 'doc_type': 'ID_PASSPORT'})
    bot.send_message(message.chat.id, 'Введіть запис ID карти(14 символів):✍')
    dbworker.set_state(message.chat.id, config.States.S_ID_SERIES.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ID_SERIES.value)
def series_id_taking(message):
    log(message)
    series = message.text
    if len(series) != 14:
        bot.send_message(message.chat.id, 'Запис ID-карти має містити 14 символів. Спробуйте ще')
        id_card(message)
    else:
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
        bot.send_message(message.chat.id, 'Введіть номер ID-карти(9 цифр):✍')
        dbworker.set_state(message.chat.id, config.States.S_ID_NUMBER.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ID_NUMBER.value)
def number_id_taking(message):
    log(message)
    number = message.text
    if len(number) != 9:
        bot.send_message(message.chat.id, 'Номер ID-карти має містити 9 цифр. Спробуйте ще')
        dbworker.set_state(message.chat.id, config.States.S_ID_NUMBER.value)
    else:
        connection = sql.connect('DATABASE.sqlite')
        q = connection.cursor()
        q.execute("UPDATE passport SET number='%s' WHERE id='%s'" % (number, message.from_user.id))
        connection.commit()
        q.close()
        connection.close()
        bot.send_message(message.chat.id, 'Введіть дату видачі ID-карти (у форматі РРРР-ММ-ДД):✍')
        dbworker.set_state(message.chat.id, config.States.S_ID_DATE.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ID_DATE.value)
def date_id_taking(message):
    log(message)
    date = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE passport SET date='%s' WHERE id='%s'" % (date, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    bot.send_message(message.chat.id, 'Введіть орган, що видав ID-карту(4 цифри):✍')
    dbworker.set_state(message.chat.id, config.States.S_ID_ISSUED_BY.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ID_ISSUED_BY.value)
def issued_id_taking(message):
    log(message)
    issued_by = message.text
    if len(issued_by) != 4:
        bot.send_message(message.chat.id, 'Орган видачі має містити 4 цифри. Спробуйте ще')
        dbworker.set_state(message.chat.id, config.States.S_ID_ISSUED_BY.value)
    else:
        connection = sql.connect('DATABASE.sqlite')
        q = connection.cursor()
        q.execute("UPDATE passport SET issued_by='%s' WHERE id='%s'" % (issued_by, message.from_user.id))
        connection.commit()
        q.close()
        connection.close()
        prefinal(message)


# ----------------------------------------------------------------------------------------------------------------------


@bot.message_handler(func=lambda message: message.text == 'Посвідчення водія 🚘')
def driver_license(message):
    utility.update({str(message.chat.id) + 'doc_type': 'DRIVING_LICENSE'})
    bot.send_message(message.chat.id, 'Введіть серію посвідчення(3 символи):✍')
    dbworker.set_state(message.chat.id, config.States.S_DRIVER_SERIES.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_DRIVER_SERIES.value)
def series_driver_taking(message):
    log(message)
    series = message.text
    if len(series) != 3:
        bot.send_message(message.chat.id, 'Серія посвідчення має містити 3 символи. Спробуйте ще')
        driver_license(message)
    else:
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
        bot.send_message(message.chat.id, 'Введіть номер посвідчення(6 цифр):✍')
        dbworker.set_state(message.chat.id, config.States.S_DRIVER_NUMBER.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_DRIVER_NUMBER.value)
def number_driver_taking(message):
    log(message)
    number = message.text
    if len(number) != 6:
        bot.send_message(message.chat.id, 'Номер посвідчення має містити 6 цифр. Спробуйте ще')
        dbworker.set_state(message.chat.id, config.States.S_DRIVER_NUMBER.value)
    else:
        connection = sql.connect('DATABASE.sqlite')
        q = connection.cursor()
        q.execute("UPDATE passport SET number='%s' WHERE id='%s'" % (number, message.from_user.id))
        connection.commit()
        q.close()
        connection.close()
        bot.send_message(message.chat.id, 'Введіть дату видачі посвідчення (у форматі РРРР-ММ-ДД):✍')
        dbworker.set_state(message.chat.id, config.States.S_DRIVER_DATE.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_DRIVER_DATE.value)
def date_driver_taking(message):
    log(message)
    date = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE passport SET date='%s' WHERE id='%s'" % (date, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    bot.send_message(message.chat.id, 'Введіть орган, що видав посвідчення:✍')
    dbworker.set_state(message.chat.id, config.States.S_DRIVER_ISSUED_BY.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_DRIVER_ISSUED_BY.value)
def issued_driver_taking(message):
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
    bot.send_message(message.chat.id, 'Перевірте правильність введених даних.')
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("SELECT * from user WHERE id='%s'" % message.from_user.id)
    results = q.fetchall()
    q.execute("SELECT * from passport WHERE id='%s'" % message.from_user.id)
    results1 = q.fetchall()
    connection.commit()
    q.close()
    connection.close()
    try:
        model = results[0][1]
    except IndexError:
        model = ''
    try:
        VIN = results[0][2]
    except IndexError:
        VIN = ''
    try:
        reg_number = results[0][3]
    except IndexError:
        reg_number = ''
    try:
        category = results[0][4]
    except IndexError:
        category = ''
    try:
        year_car = results[0][5]
    except IndexError:
        year_car = ''
    try:
        surname = results[0][6]
    except IndexError:
        surname = ''
    try:
        name = results[0][7]
    except IndexError:
        name = ''
    try:
        patronymic = results[0][8]
    except IndexError:
        patronymic = ''
    try:
        birth = results[0][9]
    except IndexError:
        birth = ''
    try:
        reg_addres = results[0][10]
    except IndexError:
        reg_addres = ''
    try:
        INN = results[0][11]
    except IndexError:
        INN = ''
    try:
        email = results[0][12]
    except IndexError:
        email = ''
    try:
        phone = results[0][13]
    except IndexError:
        phone = ''
    try:
        series = results1[0][1]
    except IndexError:
        series = ''
    try:
        doc_num = results1[0][2]
    except IndexError:
        doc_num = ''
    try:
        date = results1[0][3]
    except IndexError:
        date = ''
    try:
        organ = results1[0][4]
    except IndexError:
        organ = ''
    bot.send_message(message.chat.id,
                     f"Дані автомобіля🚘\n\nМодель:  {model}\nVIN-код:  {VIN}\nРеєстраційний номер:  {reg_number}\nКатегорія:  {category}\nРік випуску:  {year_car}\n\nВаша особиста інформація😉\n\nПрізвище:  {surname}\nІм'я:  {name}\nПо-батькові:  {patronymic}\nДата народждения:  {birth}\nАдреса реєстрації:  {reg_addres}\nІНПП:  {INN}\nEMAIL:  {email}\nТелефон:  {phone}\n\nДані вашого документа📖\n\nСерія/Запис документа:  {series}\nНомер документа:  {doc_num}\nДата видачі:  {date}\nОрган, що видав:  {organ}",
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

    bot.send_message(message.chat.id, 'Добре!\n📝Формую договір\n⏳Зачекайте',
                     reply_markup=types.ReplyKeyboardRemove())

    d = date_from_to(message)

    url = f'https://web.ewa.ua/ewa/api/v9/auto_model/maker_and_model?query={model}'
    response = requests.get(url, headers=headers, cookies=cookies)
    if str(utility.get(str(message.chat.id) + 'doc_type')) == 'ID_PASSPORT':
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
                        'type': str(utility.get(str(message.chat.id) + 'doc_type')),
                        'record': results1[0][1],
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
                        'type': str(utility.get(str(message.chat.id) + 'doc_type')),
                        'record': results1[0][1],
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
    else:
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
                        'type': str(utility.get(str(message.chat.id) + 'doc_type')),
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
                        'type': str(utility.get(str(message.chat.id) + 'doc_type')),
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
    print(str(utility.get(str(message.chat.id) + 'doc_type')))
    print(type(utility.get(str(message.chat.id) + 'doc_type')))
    url_for_save_contract = 'https://web.ewa.ua/ewa/api/v9/contract/save'
    json_string = json.dumps(contract_data)
    r = requests.post(url_for_save_contract, headers=headers, cookies=cookies,
                      data=json_string)  # Перевод договора в состояние ЧЕРНОВИК
    print(r)
    print(r.json())
    bad_data = 0
    try:
        id_contract = r.json()['id']
        utility.update({str(message.chat.id) + 'contract_id': id_contract})
    except KeyError:
        print('Какое-то из значений было введено неправильно')
        bot.send_message(message.chat.id, 'Якісь дані були введені некоректно. Спробуйте ще')
        bad_data = 1
    if bad_data == 1:
        prefinal(message)
    else:
        contract = utility.get(str(message.chat.id) + 'contract_id')
        url_for_req = f'https://web.ewa.ua/ewa/api/v9/contract/{contract}/state/REQUEST'
        r1 = requests.post(url_for_req, headers=headers, cookies=cookies)  # перевод договора в состояние ЗАЯВЛЕН
        print(r1)
        url_for_otp = f'https://web.ewa.ua/ewa/api/v9/contract/{contract}/otp/send?customer=true'
        r_otp = requests.get(url_for_otp, headers=headers, cookies=cookies)
        print(r_otp)
        bot.send_message(message.chat.id,
                         '📲На ваш мобільний телефон було відправлено СМС з паролем для підпису електронного полісу.\n\nВведіть пароль з повідомлення✍')
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
                     '👌Платіж пройшов успішно!\n\n📬Перевірте пошту, яку вказували при оформленні - ваш електронний поліс у форматі PDF має бути там.\n\n👏Якщо ви задоволені моєю роботою - поділіться мною, будь-ласка, з другом  - https://t.me/osago_insurance_bot.')
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
    button6 = types.KeyboardButton('Адреса реєстрації')
    button7 = types.KeyboardButton('ІНПП')
    button8 = types.KeyboardButton('EMAIL')
    button9 = types.KeyboardButton('Телефон')
    button10 = types.KeyboardButton('Серія документа')
    button11 = types.KeyboardButton('Номер документа')
    button12 = types.KeyboardButton('Дата видачі')
    button13 = types.KeyboardButton('Орган видачі')
    button14 = types.KeyboardButton('Авто')
    markup.add(button14, button1, button2, button3, button4, button5, button6, button7, button8, button9, button10,
               button11,
               button12, button13)
    bot.send_message(message.chat.id, 'Виберіть що хочете змінити:', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Авто')
def change_auto(message):
    utility.update({str(message.chat.id) + 'car_changer': '1'})
    print(utility.get(str(message.chat.id) + 'car_changer'))
    auto_number(message)


@bot.message_handler(func=lambda message: message.text == 'Рік випуску')
def car_year_set(message):
    bot.send_message(message.chat.id, 'Введіть рік випуску:✍')
    dbworker.set_state(message.chat.id, config.States.S1_CAR_YEAR.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_CAR_YEAR.value)
def car_year_taking_again(message):
    log(message)
    v = message.text
    if len(v) != 4:
        bot.send_message(message.chat.id, 'Рік випуску має містити 4 цифри. Наприклад 2020. Спробуйте ще.')
        car_year_set(message)
    else:
        connection = sql.connect('DATABASE.sqlite')
        q = connection.cursor()
        q.execute("UPDATE user SET car_year='%s' WHERE id='%s'" % (v, message.from_user.id))
        connection.commit()
        q.close()
        connection.close()
        prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Прізвище')
def surname_set(message):
    bot.send_message(message.chat.id, 'Введіть ваше прізвище(українською):✍')
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
    bot.send_message(message.chat.id, 'Введіть ваше імя(українською):✍')
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
    bot.send_message(message.chat.id, 'Введіть ваше імя по батькові(українською):✍')
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
    bot.send_message(message.chat.id, 'Введіть вашу дату нарождения(в форматі РРРР-ММ-ДД):✍')
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


@bot.message_handler(func=lambda message: message.text == 'Адреса реєстрації')
def address_set(message):
    bot.send_message(message.chat.id, 'Введіть вашу адресу прописки(в форматі "Місто,Вулиця,Дім,Квартира"):✍')
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


@bot.message_handler(func=lambda message: message.text == 'ІНПП')
def inn_set(message):
    bot.send_message(message.chat.id, 'Введіть ваш ІНПП(10 цифр):✍')
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
    bot.send_message(message.chat.id, 'Введіть ваш email(сюди буде висланий поліс):✍')
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
    bot.send_message(message.chat.id, 'Введіть ваш  моібльний номер телефону:✍')
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


@bot.message_handler(func=lambda message: message.text == 'Серія документа')
def series_set(message):
    bot.send_message(message.chat.id, 'Введіть вашу серію/запис документа:✍')
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


@bot.message_handler(func=lambda message: message.text == 'Номер документа')
def number_set(message):
    bot.send_message(message.chat.id, 'Введіть ваш номер документа:✍')
    dbworker.set_state(message.chat.id, config.States.S1_NUMBER.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_NUMBER.value)
def number_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE passport SET number='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Дата видачі')
def date_set(message):
    bot.send_message(message.chat.id, 'Введіть дату видачі документа(в форматі РРРР-ММ-ДД):✍')
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
    bot.send_message(message.chat.id, 'Введіть орган видачі документа:✍')
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


@bot.message_handler(content_types=['text'])
def text(message):
    if message.text[:10] == 'статистика' or message.text[:10] == 'Cтатистика':
        st = message.text.split(' ')
        if 'txt' in st or 'тхт' in st:
            tg_analytic.analysis(st, message.chat.id)
            with open('%s.txt' % message.chat.id, 'r', encoding='UTF-8') as file:
                bot.send_document(message.chat.id, file)
            tg_analytic.remove(message.chat.id)
        else:
            messages = tg_analytic.analysis(st, message.chat.id)
            bot.send_message(message.chat.id, messages)


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
