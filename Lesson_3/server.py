"""Программа-сервер"""

import socket
import sys
import json
import argparse
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, \
    MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, ACCOUNT_NAME, SENDER, MESSAGE, MESSAGE_TEXT, \
    RESPONSE_400, DESTINATION, RESPONSE_200, EXIT
from common.utils import get_message, send_message, arg_parser
import logging
import time
import logs.config_server_log
from loging_decos import Log
import select
from descrptors import Port, IP_Address
from metaclasses import ServerMaker
from server_db import ServerStorage
import threading

# Инициализация серверного логера
SERVER_LOGGER = logging.getLogger('server')






@Log()
class ServerApp(metaclass=ServerMaker):

    # Инициализация базы данных
    database = ServerStorage()

    listen_port = Port()
    listen_address = IP_Address()

    def __init__(self, listen_address, listen_port):
        """ Параментры подключения """
        self.listen_address = listen_address
        self.listen_port = listen_port

    # список клиентов , очередь сообщений
    clients = []
    messages = []

    # Словарь, содержащий имена пользователей и соответствующие им сокеты.
    names = dict()


    # @classmethod
    def process_client_message(self, message, messages_list, client, clients, names):
        '''
        Обработчик сообщений от клиентов, принимает словарь -
        сообщение от клинта, проверяет корректность,
        возвращает словарь-ответ для клиента

        :param message:
        :return:
        '''
        SERVER_LOGGER.debug(f'Разбор сообщения от клиента : {message}')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
                and USER in message:

            # and message[USER][ACCOUNT_NAME] == 'Guest'
            # send_message(client, {RESPONSE: 200})
            # return

            if message[USER][ACCOUNT_NAME] not in names.keys():
                names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Имя пользователя уже занято.'
                send_message(client, response)
                clients.remove(client)
                client.close()
            return

        # Если это сообщение, то добавляем его в очередь сообщений. Ответ не требуется.
        elif ACTION in message and message[ACTION] == MESSAGE and \
                DESTINATION in message and TIME in message and SENDER in message and \
                MESSAGE_TEXT in message:
            messages_list.append(message)
            return
        # Если клиент выходит
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            clients.remove(names[message[ACCOUNT_NAME]])
            names[message[ACCOUNT_NAME]].close()
            del names[message[ACCOUNT_NAME]]
            return

        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return

    # @classmethod
    def process_message(self, message, names, listen_socks):
        """
        Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение,
        список зарегистрированых пользователей и слушающие сокеты. Ничего не возвращает.
        :param message:
        :param names:
        :param listen_socks:
        :return:
        """
        if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
            send_message(names[message[DESTINATION]], message)
            SERVER_LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                        f'от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            SERVER_LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')

    def print_help(self):
        '''Справка по командам интерфейса'''
        print('Поддерживаемые комманды:')
        print('users - список известных пользователей')
        print('connected - список подключенных пользователей')
        print('history - история входов пользователя')
        print('exit - завершение работы сервера.')
        print('help - вывод справки по поддерживаемым командам')

    def server_iterface(self):
        '''Консольный интерфейс сервера (работа с БД)'''
        # Печатаем справку:
        self.print_help()

        # Основной цикл сервера:
        while True:
            command = input('Введите комманду: ')
            if command == 'help':
                self.print_help()
            elif command == 'exit':
                break
            elif command == 'users':
                for user in sorted(self.database.users_list()):
                    print(f'Пользователь {user[0]}, последний вход: {user[1]}')
            elif command == 'connected':
                active_users_now = sorted(self.database.active_users_list())
                # print(active_users_now)
                if active_users_now:
                    for user in active_users_now:
                        print(
                            f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, время установки соединения: {user[3]}')
                else:
                    print('Отсутствуют активные пользователи.')
            elif command == 'history':
                name = input(
                    'Введите имя пользователя для просмотра истории. Для вывода всей истории, просто нажмите Enter: ')
                for user in sorted(self.database.login_history(name)):
                    print(f'Пользователь: {user[0]} время входа: {user[1]}. Вход с: {user[2]}:{user[3]}')
            else:
                print('Команда не распознана.')

    def main_server_process(self):
        '''Главный процесс сервера по приему/отправке сообщений и управления активными пользователями'''
        # Основной цикл программы сервера


        while True:
            try:
                client, client_address = self.transport.accept()
            except OSError:
                pass
            else:
                SERVER_LOGGER.info(f'Установлено соедение с Клиентом: {client_address}')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []

            # Проверяем на наличие ждущих клиентов
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass
            # принимаем сообщения и если там есть сообщения,
            # кладём в словарь, если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        ServerApp.process_client_message(get_message(client_with_message), self.messages,
                                                         client_with_message, self.clients, self.names)
                    except:
                        SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')

                        # Получаем порт отключившегося клиента
                        client_port =  client_with_message.getpeername()[1]
                        # Получаем из базы пользователя по порту клиента
                        disabled_client = self.database.session.query(ServerStorage.ActiveUsers).filter_by(port=client_port).first()
                        # print(client_port, disabled_client, 'user.id:', disabled_client.user)

                        # Удаляем отключившегося пользователя из базы из таблицы ActiveUsers
                        self.database.session.query(ServerStorage.ActiveUsers).filter_by(port=client_port).delete()
                        self.database.session.commit()
                        disabled_client_name = self.database.session.query(ServerStorage.AllUsers).filter_by(id=disabled_client.user).first()
                        print(f'Клиент {disabled_client_name.name} (User.ID={disabled_client.user}) отключился от сервера.')

                        # Удаляем из списка клиентов
                        self.clients.remove(client_with_message)


            # Если есть сообщения, обрабатываем каждое. Добавили обработку получателя сообщения.
            for i in self.messages:
                try:
                    ServerApp.process_message(i, self.names, send_data_lst)
                except Exception:
                    SERVER_LOGGER.info(f'Связь с клиентом с именем {i[DESTINATION]} была потеряна')
                    self.clients.remove(self.names[i[DESTINATION]])
                    del self.names[i[DESTINATION]]
            self.messages.clear()

    def server_socket(self):
        '''Функция запуска сокета для сервера'''
        # Готовим сокет
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((listen_address, listen_port))
        transport.settimeout(0.5)
        self.transport = transport

        # Слушаем порт
        transport.listen(MAX_CONNECTIONS)

    # @classmethod
    def main(self, *args, **kwargs):
        ''' Функция запуска сервера '''
        # self.listen_port = listen_port
        # self.listen_address = listen_address


        # переменные для тестов
        if args:
            if args[0] == 'test':
                SERVER_LOGGER.debug(f'Запущен тест ServerApp с параметрами: {args}')
                sys.argv = args

        SERVER_LOGGER.info(f'Запущен сервер, порт для подключений: {listen_port}, '
                    f'адрес с которого принимаются подключения: {listen_address}. '
                    f'Если адрес не указан, принимаются соединения с любых адресов.')


        server_start_message = f'Сервер запущен. Адрес: {listen_address} Порт: {listen_port}'
        SERVER_LOGGER.debug(server_start_message)
        print(server_start_message)

        # Запуск сокета для сервера
        self.server_socket()

        # Запуск главного серверного процесса
        module_main_server = threading.Thread(target=self.main_server_process)
        module_main_server.daemon = True
        module_main_server.start()


        # # Запуск интерфейса сервера
        # module_server_iterface = threading.Thread(target=self.server_iterface)
        # module_server_iterface.daemon = True
        # module_server_iterface.start()

        # Watchdog основной цикл, если один из потоков завершён, то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках, достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if module_main_server.is_alive(): #module_server_iterface.is_alive() and
                continue
            break


        # # Основной цикл программы сервера
        # while True:
        #     try:
        #         client, client_address = transport.accept()
        #     except OSError:
        #         pass
        #     else:
        #         SERVER_LOGGER.info(f'Установлено соедение с Клиентом: {client_address}')
        #         self.clients.append(client)
        #
        #     recv_data_lst = []
        #     send_data_lst = []
        #     err_lst = []
        #
        #     # Проверяем на наличие ждущих клиентов
        #     try:
        #         if self.clients:
        #             recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
        #     except OSError:
        #         pass
        #     # принимаем сообщения и если там есть сообщения,
        #     # кладём в словарь, если ошибка, исключаем клиента.
        #     if recv_data_lst:
        #         for client_with_message in recv_data_lst:
        #             try:
        #                 ServerApp.process_client_message(get_message(client_with_message), self.messages, client_with_message, self.clients, self.names)
        #             except:
        #                 SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
        #                 self.clients.remove(client_with_message)
        #
        #     # Если есть сообщения, обрабатываем каждое. Добавили обработку получателя сообщения.
        #     for i in self.messages:
        #         try:
        #             ServerApp.process_message(i, self.names, send_data_lst)
        #         except Exception:
        #             SERVER_LOGGER.info(f'Связь с клиентом с именем {i[DESTINATION]} была потеряна')
        #             self.clients.remove(self.names[i[DESTINATION]])
        #             del self.names[i[DESTINATION]]
        #     self.messages.clear()



            # # Если есть сообщения для отправки и ожидающие клиенты, отправляем им сообщение.
            # if messages and send_data_lst:
            #     message = {ACTION: MESSAGE,
            #                SENDER: messages[0][0],
            #                TIME: time.time(),
            #                MESSAGE_TEXT: messages[0][1]}
            #     del messages[0]
            #     for waiting_client in send_data_lst:
            #         try:
            #             send_message(waiting_client, message)
            #         except:
            #             SERVER_LOGGER.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
            #             clients.remove(waiting_client)

            # try:
            #     message_from_client = get_message(client)
            #     # print(message_from_client)
            #     SERVER_LOGGER.info(f'Сообщение от клиента: {message_from_client}')
            #     # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
            #     response = ServerApp.process_client_message(message_from_client)
            #     SERVER_LOGGER.debug(f'Отправка сообщения: {response} клиенту: {message_from_client["user"]["account_name"]}.')
            #     send_message(client, response)
            #     client.close()
            #     SERVER_LOGGER.debug(f'Клиент остановлен.')
            # except (ValueError, json.JSONDecodeError):
            #     # print('Принято некорретное сообщение от клиента.')
            #     SERVER_LOGGER.error(f'Принято некорретное сообщение от клиента.')
            #     client.close()
            #     SERVER_LOGGER.debug(f'Клиент остановлен.')


if __name__ == '__main__':
    listen_address, listen_port = arg_parser()
    ServerApp = ServerApp(listen_address, listen_port)
    ServerApp.main()

# server_with_db.py -p 8888 -a 192.168.0.49
# server_with_db.py -p 8888 -a 192.168.0.66
# server_with_db.py -p 8888 -a 192.168.0.101