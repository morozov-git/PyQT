"""Программа-клиент"""
import os
import sys
import json
import time

from PyQt5.QtWidgets import QApplication, QMessageBox
from Crypto.PublicKey import RSA
from common.variables import *
from common.utils import get_message, send_message, arg_parser
from loging_decos import Log
from common.errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
import threading
from descrptors import Port, IP_Address
from metaclasses import ClientMaker
from Client.client_db import ClientDatabase
from Client.main_window import ClientMainWindow
from Client.start_dialog import UserNameDialog
from Client.client_transport import ClientTransport

# Инициализация клиентского логера
CLIENT_LOGGER = logging.getLogger('client')

# Объект блокировки сокета и работы с базой данных
sock_lock = threading.Lock()
database_lock = threading.Lock()


@Log()
class ClientApp(metaclass=ClientMaker):

    server_port = Port()
    server_address = IP_Address()

    def __init__(self, server_address, server_port, client_name, client_password):
        """ Параментры подключения """
        self.client_name = client_name
        self.server_address = server_address
        self.server_port = server_port
        self.client_password = client_password
        # super().__init__()
        # print(self)


    # @classmethod
    def create_exit_message(self):
        """Функция создаёт словарь с сообщением о выходе"""
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name
        }

    # @classmethod
    # def message_from_server(cls, sock, username):
    def message_from_server(self, transport, client_name):
        """Функция - обработчик сообщений других пользователей, поступающих с сервера"""

        while True:
            time.sleep(1)
            with sock_lock:

                try:
                    message = get_message(transport)
                    # if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                    #         and MESSAGE_TEXT in message and message[DESTINATION] == username:
                    #     print(f'\nПолучено сообщение от пользователя {message[SENDER]}: {message[MESSAGE_TEXT]} \n')
                    #     CLIENT_LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                    # else:
                    #     CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
                # Принято некорректное сообщение
                except IncorrectDataRecivedError:
                    CLIENT_LOGGER.error(f'Не удалось декодировать полученное сообщение.')
                # Вышел таймаут соединения если error = None, иначе обрыв соединения.
                except OSError as err:
                    if err.errno:
                        CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                        break
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                    sys.exit(1)
                    break
                # Если пакет корретно получен выводим в консоль и записываем в базу.
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                            and MESSAGE_TEXT in message and message[DESTINATION] == self.client_name:
                        print(f'\nПолучено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                        # Захватываем работу с базой данных и сохраняем в неё сообщение
                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER], self.client_name, message[MESSAGE_TEXT])
                            except:
                                CLIENT_LOGGER.error('Ошибка взаимодействия с базой данных')

                        CLIENT_LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                    else:
                        CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')

    # @classmethod
    def create_message(self, client_name='Guest'):
        """
        Функция запрашивает текст сообщения и возвращает его.
        Так же завершает работу при вводе подобной комманды
        """
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        # if message == 'exit':
        #     sock.close()
        #     CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
        #     print('Спасибо за использование нашего сервиса!')
        #     sys.exit(0)


        # Проверим, что получатель существует
        with database_lock:
            if not self.database.check_user(to_user):
                CLIENT_LOGGER.error(f'Попытка отправить сообщение незарегистрированому получателю: {to_user}')
                return

        message_dict = {
            ACTION: MESSAGE,
            TIME: time.time(),
            SENDER: self.client_name,
            DESTINATION: to_user,
            MESSAGE_TEXT: message
        }
        CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        # return message_dict

        # Сохраняем сообщения для истории
        with database_lock:
            self.database.save_message(self.client_name, to_user, message)

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with sock_lock:
            try:
                send_message(self.transport, message_dict)
                CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
            except:
                CLIENT_LOGGER.critical('Потеряно соединение с сервером.')
                self.user_interface.daemon = True
                sys.exit(1)

    # @classmethod
    def user_interactive(self):
        """Функция для консольного интерфейса
        взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""
        ClientApp.print_help()
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
                        send_message(self.transport, self.create_exit_message())
                    except:
                        pass
                    print('Завершение соединения.')
                    CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
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

    def edit_contacts(self):
        """Функция для консольного интерфейса для изменеия контактов"""
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    CLIENT_LOGGER.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        self.add_contact(edit)
                    except ServerError:
                        CLIENT_LOGGER.error('Не удалось отправить информацию на сервер.')

    def print_history(self):
        """Функция для консольного интерфейса выводящяя историю сообщений"""
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

    # @classmethod
    def print_help(self):
        """Функция для консольного интерфейса выводящяя справку по командам"""
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    """перенесена в модуль client_transport"""
    # # @classmethod
    # def create_presence(self, client_name='Guest'):
    #     '''
    #     Функция генерирует запрос о присутствии клиента
    #     :param client_name:
    #     :return:
    #     '''
    #     # {'action': 'presence', 'time': 1573760672.167031, 'user': {'client_name': 'Guest'}}
    #     out = {ACTION: PRESENCE,
    #            TIME: time.time(),
    #            USER: {ACCOUNT_NAME: client_name}
    #         }
    #     CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {client_name}')
    #     return out

    """перенесена в модуль client_transport"""
    # # @classmethod
    # def process_response_ans(self, message):
    #     """
    #     Функция разбирает ответ сервера на сообщение о присутствии,
    #     возращает 200 если все ОК или генерирует исключение при ошибке
    #     """
    #     CLIENT_LOGGER.debug(f'Разбор приветственного сообщения от сервера: {message}')
    #     if RESPONSE in message:
    #         if message[RESPONSE] == 200:
    #             return '200 : OK'
    #         elif message[RESPONSE] == 400:
    #             raise ServerError(f'400 : {message[ERROR]}')
    #     raise ReqFieldMissingError(RESPONSE)

    # @classmethod
    def process_answer(self, message):
        '''
        Функция разбирает ответ сервера
        :param message:
        :return:
        '''
        CLIENT_LOGGER.debug(f'Разбор сообщения от сервера: {message}')
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200 : OK'
            return f'400 : {message[ERROR]}'
        raise ReqFieldMissingError(RESPONSE)

    """перенесена в модуль client_transport"""
    # def contacts_list_request(self):
    #     """Функция запрос контакт листа"""
    #     CLIENT_LOGGER.debug(f'Запрос контакт листа для пользователся {self.client_name}')
    #     req = {
    #         ACTION: GET_CONTACTS,
    #         TIME: time.time(),
    #         USER: client_name
    #     }
    #     CLIENT_LOGGER.debug(f'Сформирован запрос {req}')
    #     send_message(self.transport, req)
    #     ans = get_message(self.transport)
    #     CLIENT_LOGGER.debug(f'Получен ответ {ans}')
    #     if RESPONSE in ans and ans[RESPONSE] == 202:
    #         return ans[LIST_INFO]
    #     else:
    #         raise ServerError

    """перенесена в модуль client_transport"""
    # def add_contact(self, contact):
    #     """Функция добавления пользователя в контакт лист"""
    #     CLIENT_LOGGER.debug(f'Создание контакта {contact}')
    #     req = {
    #         ACTION: ADD_CONTACT,
    #         TIME: time.time(),
    #         USER: self.client_name,
    #         ACCOUNT_NAME: contact
    #     }
    #     send_message(self.transport, req)
    #     ans = get_message(self.transport)
    #     if RESPONSE in ans and ans[RESPONSE] == 200:
    #         pass
    #     else:
    #         raise ServerError('Ошибка создания контакта')
    #     print('Удачное создание контакта.')

    def database_load(self):
        """Функция инициализатор базы данных. Запускается при запуске, загружает данные в базу с сервера."""
        # Загружаем список известных пользователей
        try:
            users_list = self.user_list_request()
        except ServerError:
            CLIENT_LOGGER.error('Ошибка запроса списка известных пользователей.')
        else:
            self.database.add_users(users_list)

        # Загружаем список контактов
        try:
            contacts_list = self.contacts_list_request()
        except ServerError:
            CLIENT_LOGGER.error('Ошибка запроса списка контактов.')
        else:
            for contact in contacts_list:
                self.database.add_contact(contact)

    # def user_list_request(self):
    #     """Функция запроса списка известных пользователей"""
    #     CLIENT_LOGGER.debug(f'Запрос списка известных пользователей {self.client_name}')
    #     req = {
    #         ACTION: USERS_REQUEST,
    #         TIME: time.time(),
    #         ACCOUNT_NAME: self.client_name
    #     }
    #     send_message(self.transport, req)
    #     ans = get_message(self.transport)
    #     if RESPONSE in ans and ans[RESPONSE] == 202:
    #         return ans[LIST_INFO]
    #     else:
    #         raise ServerError

    """перенесена в модуль client_transport"""
    # def user_list_update(self):
    #     """Функция обновления таблицы известных пользователей."""
    #     CLIENT_LOGGER.debug(f'Запрос списка известных пользователей {self.client_name}')
    #     req = {
    #         ACTION: USERS_REQUEST,
    #         TIME: time.time(),
    #         ACCOUNT_NAME: self.client_name
    #     }
    #     with sock_lock:
    #         send_message(self.transport, req)
    #         ans = get_message(self.transport)
    #     if RESPONSE in ans and ans[RESPONSE] == 202:
    #         self.database.add_users(ans[LIST_INFO])
    #     else:
    #         CLIENT_LOGGER.error('Не удалось обновить список известных пользователей.')

    """перенесена в модуль client_transport"""
    # def remove_contact(self, username, contact):
    #     """Функция удаления пользователя из контакт листа"""
    #     CLIENT_LOGGER.debug(f'Создание контакта {contact}')
    #     req = {
    #         ACTION: REMOVE_CONTACT,
    #         TIME: time.time(),
    #         USER: username,
    #         ACCOUNT_NAME: contact
    #     }
    #     send_message(self.transport, req)
    #     ans = get_message(self.transport)
    #     if RESPONSE in ans and ans[RESPONSE] == 200:
    #         pass
    #     else:
    #         raise ServerError('Ошибка удаления клиента')
    #     print('Удачное удаление')



    # @classmethod
    def main(self, *args, **kwargs):
        """Основная функция клиента"""
        '''Загружаем параметы коммандной строки'''

        ''' # client.py 192.168.0.100 8079
        # s_address, s_port, self.client_name = arg_parser()

        # if not self.client_name:
        #     self.client_name = input('Введите имя пользователя: ')'''

        # Создаём клиентокое приложение
        client_app = QApplication(sys.argv)

        # Если имя пользователя не было указано в командной строке то запросим его
        start_dialog = UserNameDialog()
        if not self.client_name or not self.client_password:
            client_app.exec_()
            # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и
            # удаляем объект, инааче выходим
            if start_dialog.ok_pressed:
                self.client_name = start_dialog.client_name.text()
                self.client_password = start_dialog.client_password.text()
                CLIENT_LOGGER.debug(f'Using USERNAME = {self.client_name}, PASSWORD = {self.client_password}.')
            else:
                exit(0)


        CLIENT_LOGGER.info(f'Запущен клиент с парамертами: адрес сервера: {self.server_address}, '
                           f'порт: {self.server_port}, пользователь {self.client_name}')

        # переменные для тестов
        if args:
            if args[0] == 'test':
                CLIENT_LOGGER.debug(f'Запущен тест ClientApp с параметрами: {args}')
                sys.argv = args


        """Инициализация сокета и обмен приветствиями"""
        """перенесена в модуль client_transport"""
        """        # try:
        #     self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #
        #
        #
        #     # Таймаут 1 секунда, необходим для освобождения сокета.
        #     self.transport.settimeout(1)
        #     self.transport.connect((server_address, server_port))
        #     message_to_server = ClientApp.create_presence(self.client_name)
        #     send_message(self.transport, message_to_server)
        #     answer = ClientApp.process_answer(get_message(self.transport))
        #     CLIENT_LOGGER.info(f'Принят ответ от сервера {answer}')
        #     print(answer)  # Печатаем ответ от сервера в косоль для наглядности
        # # except (ValueError, json.JSONDecodeError):
        # #     print('Не удалось декодировать сообщение сервера.')
        # except json.JSONDecodeError:
        #     CLIENT_LOGGER.error('Не удалось декодировать полученную Json строку.')
        #     sys.exit(1)
        # except ServerError as error:
        #     CLIENT_LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        #     sys.exit(1)
        # except ReqFieldMissingError as missing_error:
        #     CLIENT_LOGGER.error(f'В ответе сервера отсутствует необходимое поле '
        #                         f'{missing_error.missing_field}')
        #     sys.exit(1)
        # except ConnectionRefusedError:
        #     CLIENT_LOGGER.critical(f'Не удалось подключиться к серверу {server_address}:{server_port}, '
        #                            f'сервер отверг запрос на подключение.')
        #     sys.exit(1)
        # else:
        #
        #     # # Инициализация БД
        #     self.database = ClientDatabase(self.client_name)
        #     # self.database_load()
        #
        #
        #     # # затем запускаем отправку сообщений и взаимодействие с пользователем.
        #     # self.user_interface = threading.Thread(target=ClientApp.user_interactive) # , args=(transport, self.client_name)
        #     # self.user_interface.daemon = True
        #     # self.user_interface.start()
        #     # CLIENT_LOGGER.debug('Запущены процессы')
        #
        #     # Если соединение с сервером установлено корректно,
        #     # запускаем клиенский процесс приёма сообщний
        #     self.receiver = threading.Thread(target=ClientApp.message_from_server, args=(self.transport, self.client_name))
        #     self.receiver.daemon = True
        #     self.receiver.start()
        #
        #
        #
        #     # Создаём GUI
        #     client_main_window = ClientMainWindow(self.database, self.transport)
        #     client_main_window.make_connection(self.transport)
        #     client_main_window.setWindowTitle(f'Чат Программа alpha release - {self.client_name}')
        #     client_app.exec_()
        #
        #     # Раз графическая оболочка закрылась, закрываем транспорт
        #     self.transport.transport_shutdown()
        #     self.transport.join()
        #
        #
        #
        #     # Watchdog основной цикл, если один из потоков завершён,
        #     # то значит или потеряно соединение или пользователь
        #     # ввёл exit. Поскольку все события обработываются в потоках,
        #     # достаточно просто завершить цикл.
        #     while True:
        #         time.sleep(1)
        #         if self.user_interface.is_alive(): #self.receiver.is_alive() and
        #             continue
        #         # sys.exit(0)
        #         break
        #     time.sleep(1)
        #     print('Client stopped')
        #     sys.exit(0)
        #
"""
            # # Если соединение с сервером установлено корректно,
            # # начинаем обмен с ним, согласно требуемому режиму.
            # # основной цикл прогрммы:
            # if client_mode == 'send':
            #     print('Режим работы - отправка сообщений.')
            # else:
            #     print('Режим работы - приём сообщений.')
            # while True:
            #     # режим работы - отправка сообщений
            #     if client_mode == 'send':
            #         try:
            #             send_message(transport, ClientApp.create_message(transport, client_name))
            #         except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
            #             CLIENT_LOGGER.error(f'Соединение с сервером {server_address} было потеряно.')
            #             sys.exit(1)
            #
            #     # Режим работы приём:
            #     if client_mode == 'listen':
            #         try:
            #             ClientApp.message_from_server(get_message(transport))
            #         except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
            #             CLIENT_LOGGER.error(f'Соединение с сервером {server_address} было потеряно.')
            #             sys.exit(1)

        # Создаём объект базы данных

        # Загружаем ключи с файла, если же файла нет, то генерируем новую пару.
        dir_path = os.path.dirname(os.path.realpath(__file__))
        key_file = os.path.join(dir_path, f'{self.client_name}.key')
        if not os.path.exists(key_file):
            keys = RSA.generate(2048, os.urandom)
            with open(key_file, 'wb') as key:
                key.write(keys.export_key())
        else:
            with open(key_file, 'rb') as key:
                keys = RSA.import_key(key.read())

        # !!!keys.publickey().export_key()
        CLIENT_LOGGER.debug("Keys sucsessfully loaded.")

        # Создаём объект базы данных
        database = ClientDatabase(self.client_name)

        # Инициализация сокета и обмен приветствиями
        # Создаём объект - транспорт и запускаем транспортный поток
        try:
            transport = ClientTransport(server_port, server_address, database, self.client_name, self.client_password, keys)
            CLIENT_LOGGER.debug("Transport ready.")
        except ServerError as error:
            message = QMessageBox()
            message.critical(start_dialog, 'Ошибка сервера', error.text)
            exit(1)
        transport.setDaemon(True)
        transport.start()

        # Удалим объект диалога за ненадобностью
        del start_dialog

        # Создаём GUI
        main_window = ClientMainWindow(database, transport, keys)
        main_window.make_connection(transport)
        main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
        client_app.exec_()

        # Раз графическая оболочка закрылась, закрываем транспорт
        transport.transport_shutdown()
        transport.join()



if __name__ == '__main__':
    server_address, server_port, client_name, client_password = arg_parser()
    ClientApp = ClientApp(server_address, server_port, client_name, client_password)
    ClientApp.main()
    # time.sleep(1)
    # sys.exit(0)

# client.py -a 192.168.0.50 -p 8888 -u TestSender1 -pass TestSender1
# client.py -a 192.168.0.49 -p 8888 -u TestSender1
# client.py -a 192.168.0.66 -p 8888 -u TestSender1
# client.py 192.168.0.49 8888 -m send -u TestSender1
