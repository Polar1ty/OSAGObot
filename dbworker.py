from vedis import Vedis
import config


# Пытаемся узнать из базы «состояние» пользователя
def get_current_state(user_id):
    with Vedis(config.db_file) as db:
        try:
            return db[user_id].decode() # Если используете Vedis версии ниже, чем 0.7.1, то .decode() НЕ НУЖЕН
        except KeyError:  # Если такого ключа почему-то не оказалось
            return config.States.S_START.value  # значение по умолчанию - начало диалога

# Сохраняем текущее «состояние» пользователя в нашу базу
def set_state(user_id, value):
    with Vedis(config.db_file) as db:
        try:
            db[user_id] = value
            return True
        except:
            # тут желательно как-то обработать ситуацию
            return False

# def save_data(user_id, key, value):
#     with Vedis(config.db_file) as db:
#         try:
#             db[user_id][key] = value
#             return True
#         except:
#             return print('Жепа')
#
# def get_state(user_id, key):
#     with Vedis(config.db_file) as db:
#         try:
#             return db[user_id].decode()
#         except:
#             return False
#
#
# # Пока что не работает, нужно довести до ума
def clear_db(user_id):
    with Vedis(config.db_file) as db:
        try:
            db.delete(user_id)
        except KeyError:
            print('Текущее состояние пустое')