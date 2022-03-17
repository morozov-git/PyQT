# """Программа-клиент"""
#
# import sys
# import json
# import socket
# import time
# import argparse
# import logging
# from errors import ReqFieldMissingError
# from common.variables import *
# from loging_decos import Log
# from errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
# import threading
# from descrptors import Port, IP_Address
# from metaclasses import ClientMaker
# from server_db import ServerStorage
# from client_db import ClientDatabase
#
# # Инициализация клиентского логера
# CLIENT_LOGGER = logging.getLogger('client')
#
# # Объект блокировки сокета и работы с базой данных
# sock_lock = threading.Lock()
# database_lock = threading.Lock()
#
#
# @Log()
# class ClientApp(metaclass=ClientMaker):
#
#     server_port = Port()
#     server_address = IP_Address()
#
#
#     def __init__(self, server_address, server_port, client_name):
#         """ Параментры подключения """
#         self.client_name = client_name
#         self.server_address = server_address
#         self.server_port = server_port
#
#         # super().__init__()
#         # print(self)
#
#
#
#     # @classmethod
#     def create_exit_message(self, account_name):
#         """Функция создаёт словарь с сообщением о выходе"""
#         return {
#             ACTION: EXIT,
#             TIME: time.time(),
#             ACCOUNT_NAME: account_name
#         }
#
#     # @classmethod
#     # def message_from_server(cls, sock, username):
#     def message_from_server(self, sock, username):
#         """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
#         while True:
#             try:
#                 message = get_message(sock)
#                 if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
#                         and MESSAGE_TEXT in message and message[DESTINATION] == username:
#                     print(f'\nПолучено сообщение от пользователя {message[SENDER]}: {message[MESSAGE_TEXT]} \n')
#                     CLIENT_LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
#                 else:
#                     CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
#             except IncorrectDataRecivedError:
#                 CLIENT_LOGGER.error(f'Не удалось декодировать полученное сообщение.')
#             except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
#                 CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
#                 sys.exit(1)
#                 break
#
#     # @classmethod
#     def create_message(self, sock, account_name='Guest'):
#         """
#         Функция запрашивает текст сообщения и возвращает его.
#         Так же завершает работу при вводе подобной комманды
#         """
#         to_user = input('Введите получателя сообщения: ')
#         message = input('Введите сообщение для отправки: ')
#         # if message == 'exit':
#         #     sock.close()
#         #     CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
#         #     print('Спасибо за использование нашего сервиса!')
#         #     sys.exit(0)
#         message_dict = {
#             ACTION: MESSAGE,
#             TIME: time.time(),
#             SENDER: account_name,
#             DESTINATION: to_user,
#             MESSAGE_TEXT: message
#         }
#         CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
#         # return message_dict
#         try:
#             send_message(sock, message_dict)
#             CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
#         except:
#             CLIENT_LOGGER.critical('Потеряно соединение с сервером.')
#             self.user_interface.daemon = True
#             sys.exit(1)
#
#     # @classmethod
#     def user_interactive(self):
#         """Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""
#         ClientApp.print_help()
#         while True:
#             command = input('Введите команду: ')
#             # Если отправка сообщения - соответствующий метод
#             if command == 'message':
#                 self.create_message()
#
#             # Вывод помощи
#             elif command == 'help':
#                 self.print_help()
#
#             # Выход. Отправляем сообщение серверу о выходе.
#             elif command == 'exit':
#                 with sock_lock:
#                     try:
#                         send_message(self.transport, self.create_exit_message())
#                     except:
#                         pass
#                     print('Завершение соединения.')
#                     CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
#                 # Задержка неоходима, чтобы успело уйти сообщение о выходе
#                 time.sleep(0.5)
#                 break
#
#             # Список контактов
#             elif command == 'contacts':
#                 with database_lock:
#                     contacts_list = self.database.get_contacts()
#                 for contact in contacts_list:
#                     print(contact)
#
#             # Редактирование контактов
#             elif command == 'edit':
#                 self.edit_contacts()
#
#             # история сообщений.
#             elif command == 'history':
#                 self.print_history()
#
#             else:
#                 print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')
#
#     # @classmethod
#     def print_help(self):
#         """Функция выводящяя справку по командам"""
#         print('Поддерживаемые команды:')
#         print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
#         print('history - история сообщений')
#         print('contacts - список контактов')
#         print('edit - редактирование списка контактов')
#         print('help - вывести подсказки по командам')
#         print('exit - выход из программы')
#
#     # @classmethod
#     def create_presence(self, account_name='Guest'):
#         '''
#         Функция генерирует запрос о присутствии клиента
#         :param account_name:
#         :return:
#         '''
#         # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
#         out = {ACTION: PRESENCE,
#                TIME: time.time(),
#                USER: {ACCOUNT_NAME: account_name}
#             }
#         CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
#         return out
#
#     # @classmethod
#     def process_response_ans(self, message):
#         """
#         Функция разбирает ответ сервера на сообщение о присутствии,
#         возращает 200 если все ОК или генерирует исключение при ошибке
#         """
#         CLIENT_LOGGER.debug(f'Разбор приветственного сообщения от сервера: {message}')
#         if RESPONSE in message:
#             if message[RESPONSE] == 200:
#                 return '200 : OK'
#             elif message[RESPONSE] == 400:
#                 raise ServerError(f'400 : {message[ERROR]}')
#         raise ReqFieldMissingError(RESPONSE)
#
#     # @classmethod
#     def process_answer(self, message):
#         '''
#         Функция разбирает ответ сервера
#         :param message:
#         :return:
#         '''
#         CLIENT_LOGGER.debug(f'Разбор сообщения от сервера: {message}')
#         if RESPONSE in message:
#             if message[RESPONSE] == 200:
#                 return '200 : OK'
#             return f'400 : {message[ERROR]}'
#         raise ReqFieldMissingError(RESPONSE)
#
#
#     def contacts_list_request(self, transport, name):
#         """Функция запрос контакт листа"""
#         CLIENT_LOGGER.debug(f'Запрос контакт листа для пользователся {name}')
#         req = {
#             ACTION: GET_CONTACTS,
#             TIME: time.time(),
#             USER: name
#         }
#         CLIENT_LOGGER.debug(f'Сформирован запрос {req}')
#         send_message(transport, req)
#         ans = get_message(transport)
#         CLIENT_LOGGER.debug(f'Получен ответ {ans}')
#         if RESPONSE in ans and ans[RESPONSE] == 202:
#             return ans[LIST_INFO]
#         else:
#             raise ServerError
#
#
#     def add_contact(self, transport, username, contact):
#         """Функция добавления пользователя в контакт лист"""
#         CLIENT_LOGGER.debug(f'Создание контакта {contact}')
#         req = {
#             ACTION: ADD_CONTACT,
#             TIME: time.time(),
#             USER: username,
#             ACCOUNT_NAME: contact
#         }
#         send_message(transport, req)
#         ans = get_message(transport)
#         if RESPONSE in ans and ans[RESPONSE] == 200:
#             pass
#         else:
#             raise ServerError('Ошибка создания контакта')
#         print('Удачное создание контакта.')
#
#
#     def database_load(self, transport, database, username):
#         """Функция инициализатор базы данных. Запускается при запуске, загружает данные в базу с сервера."""
#         # Загружаем список известных пользователей
#         try:
#             users_list = self.user_list_request(transport, username)
#         except ServerError:
#             CLIENT_LOGGER.error('Ошибка запроса списка известных пользователей.')
#         else:
#             database.add_users(users_list)
#
#         # Загружаем список контактов
#         try:
#             contacts_list = self.contacts_list_request(transport, username)
#         except ServerError:
#             CLIENT_LOGGER.error('Ошибка запроса списка контактов.')
#         else:
#             for contact in contacts_list:
#                 database.add_contact(contact)
#
#
#     def user_list_request(self, transport, username):
#         """Функция запроса списка известных пользователей"""
#         CLIENT_LOGGER.debug(f'Запрос списка известных пользователей {username}')
#         req = {
#             ACTION: USERS_REQUEST,
#             TIME: time.time(),
#             ACCOUNT_NAME: username
#         }
#         send_message(transport, req)
#         ans = get_message(transport)
#         if RESPONSE in ans and ans[RESPONSE] == 202:
#             return ans[LIST_INFO]
#         else:
#             raise ServerError
#
#
#     def remove_contact(self, transport, username, contact):
#         """Функция удаления пользователя из контакт листа"""
#         CLIENT_LOGGER.debug(f'Создание контакта {contact}')
#         req = {
#             ACTION: REMOVE_CONTACT,
#             TIME: time.time(),
#             USER: username,
#             ACCOUNT_NAME: contact
#         }
#         send_message(transport, req)
#         ans = get_message(transport)
#         if RESPONSE in ans and ans[RESPONSE] == 200:
#             pass
#         else:
#             raise ServerError('Ошибка удаления клиента')
#         print('Удачное удаление')
#
#
#     def edit_contacts(self):
#         """Функция изменеия контактов"""
#         ans = input('Для удаления введите del, для добавления add: ')
#         if ans == 'del':
#             edit = input('Введите имя удаляемного контакта: ')
#             with database_lock:
#                 if self.database.check_contact(edit):
#                     self.database.del_contact(edit)
#                 else:
#                     CLIENT_LOGGER.error('Попытка удаления несуществующего контакта.')
#         elif ans == 'add':
#             # Проверка на возможность такого контакта
#             edit = input('Введите имя создаваемого контакта: ')
#             if self.database.check_user(edit):
#                 with database_lock:
#                     self.database.add_contact(edit)
#                 with sock_lock:
#                     try:
#                         self.add_contact(self.sock, self.account_name, edit)
#                     except ServerError:
#                         CLIENT_LOGGER.error('Не удалось отправить информацию на сервер.')
#
#
#     def print_history(self):
#         """Функция выводящяя историю сообщений"""
#         ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
#         with database_lock:
#             if ask == 'in':
#                 history_list = self.database.get_history(to_who=self.account_name)
#                 for message in history_list:
#                     print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
#             elif ask == 'out':
#                 history_list = self.database.get_history(from_who=self.account_name)
#                 for message in history_list:
#                     print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
#             else:
#                 history_list = self.database.get_history()
#                 for message in history_list:
#                     print(f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от {message[3]}\n{message[2]}')
#
#     # @classmethod
#     def main(self, *args, **kwargs):
#         '''Загружаем параметы коммандной строки'''
#         # client.py 192.168.0.100 8079
#         # s_address, s_port, self.client_name = arg_parser()
#
#         if not self.client_name:
#             self.client_name = input('Введите имя пользователя: ')
#
#         CLIENT_LOGGER.info(f'Запущен клиент с парамертами: адрес сервера: {server_address}, порт: {server_port}')
#         # переменные для тестов
#         if args:
#             if args[0] == 'test':
#                 CLIENT_LOGGER.debug(f'Запущен тест ClientApp с параметрами: {args}')
#                 sys.argv = args
#
#         # Инициализация сокета и обмен приветствиями
#         try:
#             transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             transport.settimeout(1)
#             transport.connect((server_address, server_port))
#             message_to_server = ClientApp.create_presence(self.client_name)
#             send_message(transport, message_to_server)
#             answer = ClientApp.process_answer(get_message(transport))
#             CLIENT_LOGGER.info(f'Принят ответ от сервера {answer}')
#             print(answer)  # Печатаем ответ от сервера в косоль для наглядности
#         # except (ValueError, json.JSONDecodeError):
#         #     print('Не удалось декодировать сообщение сервера.')
#         except json.JSONDecodeError:
#             CLIENT_LOGGER.error('Не удалось декодировать полученную Json строку.')
#             sys.exit(1)
#         except ServerError as error:
#             CLIENT_LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
#             sys.exit(1)
#         except ReqFieldMissingError as missing_error:
#             CLIENT_LOGGER.error(f'В ответе сервера отсутствует необходимое поле '
#                                 f'{missing_error.missing_field}')
#             sys.exit(1)
#         except ConnectionRefusedError:
#             CLIENT_LOGGER.critical(f'Не удалось подключиться к серверу {server_address}:{server_port}, '
#                                    f'сервер отверг запрос на подключение.')
#             sys.exit(1)
#         else:
#
#             # # Инициализация БД
#             # self.database = ClientDatabase(self.client_name)
#             # self.database_load(transport, self.database, self.client_name)
#
#             # Если соединение с сервером установлено корректно,
#             # запускаем клиенский процесс приёма сообщний
#             self.receiver = threading.Thread(target=ClientApp.message_from_server, args=(transport, self.client_name))
#             self.receiver.daemon = True
#             self.receiver.start()
#
#             # затем запускаем отправку сообщений и взаимодействие с пользователем.
#             self.user_interface = threading.Thread(target=ClientApp.user_interactive) # , args=(transport, self.client_name)
#             self.user_interface.daemon = True
#             self.user_interface.start()
#             CLIENT_LOGGER.debug('Запущены процессы')
#
#             # Watchdog основной цикл, если один из потоков завершён,
#             # то значит или потеряно соединение или пользователь
#             # ввёл exit. Поскольку все события обработываются в потоках,
#             # достаточно просто завершить цикл.
#             while True:
#                 time.sleep(1)
#                 if self.user_interface.is_alive(): #self.receiver.is_alive() and
#                     continue
#                 # sys.exit(0)
#                 break
#             time.sleep(1)
#             print('Client stopped')
#             sys.exit(0)
#
#             # # Если соединение с сервером установлено корректно,
#             # # начинаем обмен с ним, согласно требуемому режиму.
#             # # основной цикл прогрммы:
#             # if client_mode == 'send':
#             #     print('Режим работы - отправка сообщений.')
#             # else:
#             #     print('Режим работы - приём сообщений.')
#             # while True:
#             #     # режим работы - отправка сообщений
#             #     if client_mode == 'send':
#             #         try:
#             #             send_message(transport, ClientApp.create_message(transport, client_name))
#             #         except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
#             #             CLIENT_LOGGER.error(f'Соединение с сервером {server_address} было потеряно.')
#             #             sys.exit(1)
#             #
#             #     # Режим работы приём:
#             #     if client_mode == 'listen':
#             #         try:
#             #             ClientApp.message_from_server(get_message(transport))
#             #         except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
#             #             CLIENT_LOGGER.error(f'Соединение с сервером {server_address} было потеряно.')
#             #             sys.exit(1)
#
#
#
#
# if __name__ == '__main__':
#     server_address, server_port, client_name = arg_parser()
#     ClientApp = ClientApp(server_address, server_port, client_name)
#     ClientApp.main()
#     # time.sleep(1)
#     # sys.exit(0)
#
# # client.py -a 192.168.0.93 -p 8888 -u TestSender1
# # client.py -a 192.168.0.49 -p 8888 -u TestSender1
# # client.py -a 192.168.0.66 -p 8888 -u TestSender1
# # client.py 192.168.0.49 8888 -m send -u TestSender1


import socket
import time
import threading
from common.variables import *
from common.utils import *
from errors import IncorrectDataRecivedError, ReqFieldMissingError, ServerError
from decos import log
from metaclasses import ClientMaker
from client_database_111111 import ClientDatabase

# Инициализация клиентского логера
logger = logging.getLogger('client')

# Объект блокировки сокета и работы с базой данных
sock_lock = threading.Lock()
database_lock = threading.Lock()


# Класс формировки и отправки сообщений на сервер и взаимодействия с пользователем.
class ClientSender(threading.Thread, metaclass=ClientMaker):
    """ """
    def __init__(self, account_name, sock, database):
        """ """
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    # Функция создаёт словарь с сообщением о выходе.
    def create_exit_message(self):
        """ """
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    # Функция запрашивает кому отправить сообщение и само сообщение, и отправляет полученные данные на сервер.
    def create_message(self):
        """ """
        to = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')

        # Проверим, что получатель существует
        with database_lock:
            if not self.database.check_user(to):
                logger.error(f'Попытка отправить сообщение незарегистрированому получателю: {to}')
                return

        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')

        # Сохраняем сообщения для истории
        with database_lock:
            self.database.save_message(self.account_name , to , message)

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                logger.info(f'Отправлено сообщение для пользователя {to}')
            except OSError as err:
                if err.errno:
                    logger.critical('Потеряно соединение с сервером.')
                    exit(1)
                else:
                    logger.error('Не удалось передать сообщение. Таймаут соединения')

    # Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения
    def run(self):
        """ """
        self.print_help()
        while True:
            command = input('Введите команду: ')
            # Если отправка сообщения - соответствующий метод
            if command == 'message':
                self.create_message()

            # Вывод помощи
            elif command == 'help':
                self.print_help()

            # Выход. Отправляем сообщение серверу о выходе.
            elif command == 'exit':
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_message())
                    except:
                        pass
                    print('Завершение соединения.')
                    logger.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break

            # Список контактов
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            # Редактирование контактов
            elif command == 'edit':
                self.edit_contacts()

            # история сообщений.
            elif command == 'history':
                self.print_history()

            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    # Функция выводящяя справку по использованию.
    def print_help(self):
        """ """
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    # Функция выводящяя историю сообщений
    def print_history(self):
        """ """
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от {message[3]}\n{message[2]}')

    # Функция изменеия контактов
    def edit_contacts(self):
        """ """
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock , self.account_name, edit)
                    except ServerError:
                        logger.error('Не удалось отправить информацию на сервер.')







# Класс-приёмник сообщений с сервера. Принимает сообщения, выводит в консоль , сохраняет в базу.
class ClientReader(threading.Thread, metaclass=ClientMaker):
    """ """
    def __init__(self, account_name, sock, database):
        """ """
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    # Основной цикл приёмника сообщений, принимает сообщения, выводит в консоль. Завершается при потере соединения.
    def run(self):
        """ """
        while True:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # если не сделать тут задержку, то второй поток может достаточно долго ждать освобождения сокета.
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)

                # Принято некорректное сообщение
                except IncorrectDataRecivedError:
                    logger.error(f'Не удалось декодировать полученное сообщение.')
                # Вышел таймаут соединения если errno = None, иначе обрыв соединения.
                except OSError as err:
                    if err.errno:
                        logger.critical(f'Потеряно соединение с сервером.')
                        break
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    logger.critical(f'Потеряно соединение с сервером.')
                    break
                # Если пакет корретно получен выводим в консоль и записываем в базу.
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                            and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name:
                        print(f'\nПолучено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                        # Захватываем работу с базой данных и сохраняем в неё сообщение
                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER], self.account_name, message[MESSAGE_TEXT])
                            except:
                                logger.error('Ошибка взаимодействия с базой данных')

                        logger.info(f'Получено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                    else:
                        logger.error(f'Получено некорректное сообщение с сервера: {message}')


# Функция генерирует запрос о присутствии клиента
@log
def create_presence(account_name):
    """ """
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    logger.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
    return out


# Функция разбирает ответ сервера на сообщение о присутствии, возращает 200 если все ОК или генерирует исключение при\
# ошибке.
@log
def process_response_ans(message):
    """ """
    logger.debug(f'Разбор приветственного сообщения от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


# # Парсер аргументов коммандной строки
# @log
# def arg_parser():
#     """ """
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-a', default=DEFAULT_IP_ADDRESS, nargs='?')
#     parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
#     parser.add_argument('-u', '--name', default=None, nargs='?')
#     namespace = parser.parse_args(sys.argv[1:])
#     server_address = namespace.addr
#     server_port = namespace.port
#     client_name = namespace.name
#
#     # проверим подходящий номер порта
#     if not 1023 < server_port < 65536:
#         logger.critical(
#             f'Попытка запуска клиента с неподходящим номером порта: {server_port}. Допустимы адреса с 1024 до 65535. Клиент завершается.')
#         exit(1)
#
#     return server_address, server_port, client_name


# Функция запрос контакт листа
def contacts_list_request(sock, name):
    """ """
    logger.debug(f'Запрос контакт листа для пользователся {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    logger.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    ans = get_message(sock)
    logger.debug(f'Получен ответ {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


# Функция добавления пользователя в контакт лист
def add_contact(sock, username, contact):
    """ """
    logger.debug(f'Создание контакта {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Удачное создание контакта.')


# Функция запроса списка известных пользователей
def user_list_request(sock, username):
    """ """
    logger.debug(f'Запрос списка известных пользователей {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


# Функция удаления пользователя из контакт листа
def remove_contact(sock, username, contact):
    """ """
    logger.debug(f'Создание контакта {contact}')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print('Удачное удаление')


# Функция инициализатор базы данных. Запускается при запуске, загружает данные в базу с сервера.
def database_load(sock, database, username):
    """ """
    # Загружаем список известных пользователей
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        logger.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    # Загружаем список контактов
    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        logger.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main():
    """ """
    # Сообщаем о запуске
    print('Консольный месседжер. Клиентский модуль.')

    # Загружаем параметы коммандной строки
    server_address, server_port, client_name = arg_parser()

    # Если имя пользователя не было задано, необходимо запросить пользователя.
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')

    logger.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address} , порт: {server_port}, имя пользователя: {client_name}')

    # Инициализация сокета и сообщение серверу о нашем появлении
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Таймаут 1 секунда, необходим для освобождения сокета.
        transport.settimeout(1)

        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_response_ans(get_message(transport))
        logger.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        logger.error('Не удалось декодировать полученную Json строку.')
        exit(1)
    except ServerError as error:
        logger.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        exit(1)
    except ReqFieldMissingError as missing_error:
        logger.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        logger.critical(
            f'Не удалось подключиться к серверу {server_address}:{server_port}, конечный компьютер отверг запрос на подключение.')
        exit(1)
    else:

        # Инициализация БД
        database = ClientDatabase(client_name)
        database_load(transport, database, client_name)

        # Если соединение с сервером установлено корректно, запускаем поток взаимодействия с пользователем
        module_sender = ClientSender(client_name, transport, database)
        module_sender.daemon = True
        module_sender.start()
        logger.debug('Запущены процессы')

        # затем запускаем поток - приёмник сообщений.
        module_receiver = ClientReader(client_name, transport, database)
        module_receiver.daemon = True
        module_receiver.start()

        # Watchdog основной цикл, если один из потоков завершён, то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках, достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if module_receiver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
