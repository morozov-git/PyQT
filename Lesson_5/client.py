"""Программа-клиент"""

import sys
import json
import socket
import time
import argparse
import logging
from errors import ReqFieldMissingError
from common.variables import *
from common.utils import get_message, send_message, arg_parser
from loging_decos import Log
from errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
import threading
from descrptors import Port, IP_Address
from metaclasses import ClientMaker
from server_db import ServerStorage
from client_database import ClientDatabase

# Инициализация клиентского логера
CLIENT_LOGGER = logging.getLogger('client')

# Объект блокировки сокета и работы с базой данных
sock_lock = threading.Lock()
database_lock = threading.Lock()


# # парсер перенесен в модуль common.utils
# def arg_parser():
#     """
#     Создаём парсер аргументов коммандной строки
#     и читаем параметры, возвращаем 3 параметра
#     """
#     parser = argparse.ArgumentParser()
#     parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
#     parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
#     # parser.add_argument('-m', '--mode', default='listen', nargs='?')
#     parser.add_argument('-u', '--user', default='Guest', nargs='?')
#     namespace = parser.parse_args(sys.argv[2:])
#     server_address = namespace.addr
#     server_port = namespace.port
#     # client_mode = namespace.mode
#     client_name = namespace.user
#
#     # # проверим подходящий номер порта
#     # if not 1023 < server_port < 65536:
#     #     CLIENT_LOGGER.critical(f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
#     #                            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
#     #     sys.exit(1)
#     # # Проверим допустим ли выбранный режим работы клиента
#     # if client_mode not in ('listen', 'send'):
#     #     CLIENT_LOGGER.critical(f'Указан недопустимый режим работы {client_mode}, '
#     #                            f'допустимые режимы: listen , send')
#     #     sys.exit(1)
#     return server_address, server_port, client_name  # client_mode,


@Log()
class ClientApp(metaclass=ClientMaker):
	server_port = Port()
	server_address = IP_Address()

	def __init__(self, server_address, server_port, client_name):
		""" Параментры подключения """
		self.client_name = client_name
		self.server_address = server_address
		self.server_port = server_port

	# super().__init__()
	# print(self)

	# @classmethod
	def create_exit_message(self, account_name):
		"""Функция создаёт словарь с сообщением о выходе"""
		return {
			ACTION: EXIT,
			TIME: time.time(),
			ACCOUNT_NAME: account_name
		}

	# @classmethod
	# def message_from_server(cls, sock, username):
	def message_from_server(self, sock, username):
		"""Функция - обработчик сообщений других пользователей, поступающих с сервера"""
		while True:
			try:
				message = get_message(sock)
				if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
						and MESSAGE_TEXT in message and message[DESTINATION] == username:
					print(f'\nПолучено сообщение от пользователя {message[SENDER]}: {message[MESSAGE_TEXT]} \n')
					CLIENT_LOGGER.info(
						f'Получено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
				else:
					CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
			except IncorrectDataRecivedError:
				CLIENT_LOGGER.error(f'Не удалось декодировать полученное сообщение.')
			except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
				CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
				break

	# @classmethod
	def create_message(self, sock, account_name='Guest'):
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

		with database_lock:
			if not self.database.check_user(to_user):
				CLIENT_LOGGER.error(f'Попытка отправить сообщение незарегистрированому получателю: {to}')
				return

		message_dict = {
			ACTION: MESSAGE,
			TIME: time.time(),
			SENDER: account_name,
			DESTINATION: to_user,
			MESSAGE_TEXT: message
		}
		CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')

		# Сохраняем сообщения для истории
		with database_lock:
			self.database.save_message(self.account_name, to_user, message)
		# return message_dict
		try:
			send_message(sock, message_dict)
			CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
		except:
			CLIENT_LOGGER.critical('Потеряно соединение с сервером.')
			sys.exit(1)

	# @classmethod
	def user_interactive(self, sock, username):
		"""Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""
		ClientApp.print_help()
		while True:
			command = input('Введите команду: ')
			if command == 'message':
				ClientApp.create_message(sock, username)
			elif command == 'help':
				ClientApp.print_help()
			elif command == 'exit':
				# Выход. Отправляем сообщение серверу о выходе.
				with sock_lock:
					try:
						send_message(sock, ClientApp.create_exit_message(username))
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

	# @classmethod
	def print_help(self):
		"""Функция выводящяя справку по командам"""
		print('Поддерживаемые команды:')
		print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
		print('history - история сообщений')
		print('contacts - список контактов')
		print('edit - редактирование списка контактов')
		print('help - вывести подсказки по командам')
		print('exit - выход из программы')

	def print_history(self):
		"""Функция выводящяя историю сообщений"""
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
					print(
						f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от {message[3]}\n{message[2]}')

	def edit_contacts(self):
		"""Функция изменеия контактов"""
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
						ClientApp.add_contact(self.sock, self.account_name, edit)
					except ServerError:
						CLIENT_LOGGER.error('Не удалось отправить информацию на сервер.')

	def add_contact(sock, username, contact):
		"""Функция добавления пользователя в контакт лист"""
		CLIENT_LOGGER.debug(f'Создание контакта {contact}')
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

	def contacts_list_request(sock, name):
		"""Функция запрос контакт листа"""
		CLIENT_LOGGER.debug(f'Запрос контакт листа для пользователся {name}')
		req = {
			ACTION: GET_CONTACTS,
			TIME: time.time(),
			USER: name
		}
		CLIENT_LOGGER.debug(f'Сформирован запрос {req}')
		send_message(sock, req)
		ans = get_message(sock)
		CLIENT_LOGGER.debug(f'Получен ответ {ans}')
		if RESPONSE in ans and ans[RESPONSE] == 202:
			return ans[LIST_INFO]
		else:
			raise ServerError

	def user_list_request(sock, username):
		"""Функция запроса списка известных пользователей"""
		CLIENT_LOGGER.debug(f'Запрос списка известных пользователей {username}')
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

	def remove_contact(sock, username, contact):
		"""Функция удаления пользователя из контакт листа"""
		CLIENT_LOGGER.debug(f'Создание контакта {contact}')
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

	# @classmethod
	def create_presence(self, account_name='Guest'):
		'''
		Функция генерирует запрос о присутствии клиента
		:param account_name:
		:return:
		'''
		# {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
		out = {
			ACTION: PRESENCE,
			TIME: time.time(),
			USER: {ACCOUNT_NAME: account_name}
		}
		CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
		return out


	def database_load(sock, database, username):
		"""
		Функция инициализатор базы данных.
		Запускается при запуске, загружает данные в базу с сервера.
		"""
		# Загружаем список известных пользователей
		try:
			users_list = ClientApp.user_list_request(sock, username)
		except ServerError:
			CLIENT_LOGGER.error('Ошибка запроса списка известных пользователей.')
		else:
			database.add_users(users_list)

		# Загружаем список контактов
		try:
			contacts_list = ClientApp.contacts_list_request(sock, username)
		except ServerError:
			CLIENT_LOGGER.error('Ошибка запроса списка контактов.')
		else:
			for contact in contacts_list:
				database.add_contact(contact)


	# @classmethod
	def process_response_ans(self, message):
		"""
		Функция разбирает ответ сервера на сообщение о присутствии,
		возращает 200 если все ОК или генерирует исключение при ошибке
		"""
		CLIENT_LOGGER.debug(f'Разбор приветственного сообщения от сервера: {message}')
		if RESPONSE in message:
			if message[RESPONSE] == 200:
				return '200 : OK'
			elif message[RESPONSE] == 400:
				raise ServerError(f'400 : {message[ERROR]}')
		raise ReqFieldMissingError(RESPONSE)

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

	# @classmethod
	def main(self, *args, **kwargs):
		'''Загружаем параметы коммандной строки'''
		# client.py 192.168.0.100 8079
		# s_address, s_port, self.client_name = arg_parser()

		if not self.client_name:
			self.client_name = input('Введите имя пользователя: ')

		# CLIENT_LOGGER.info(f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
		#             f'порт: {server_port}, режим работы: {client_mode}')

		CLIENT_LOGGER.info(f'Запущен клиент с парамертами: адрес сервера: {server_address}, порт: {server_port}')
		# переменные для тестов
		if args:
			if args[0] == 'test':
				CLIENT_LOGGER.debug(f'Запущен тест ClientApp с параметрами: {args}')
				sys.argv = args

		# Сбор параметров подключения перенесено в отдельную функцию
		# try:
		#     server_address = sys.argv[2]
		#     server_port = int(sys.argv[3])
		#     if server_port < 1024 or server_port > 65535:
		#         raise ValueError
		# except IndexError:
		#     server_address = DEFAULT_IP_ADDRESS
		#     server_port = DEFAULT_PORT
		# except ValueError:
		#     # print('В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
		#     CLIENT_LOGGER.error(f'В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
		#     # sys.exit('BAD PORT')
		#     # raise SystemExit('BAD PORT')
		#     # raise ValueError('BAD PORT')
		#     return 'BAD PORT'
		#     # sys.exit(1)
		#
		# CLIENT_LOGGER.info(f'Запущен клиент с парамертами: (адрес сервера: {server_address}, порт: {server_port})')

		# Инициализация сокета и обмен приветствиями
		try:
			transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			# Таймаут 1 секунда, необходим для освобождения сокета.
			transport.settimeout(1)
			transport.connect((server_address, server_port))
			message_to_server = ClientApp.create_presence(self.client_name)
			send_message(transport, message_to_server)
			answer = ClientApp.process_answer(get_message(transport))
			CLIENT_LOGGER.info(f'Принят ответ от сервера {answer}')
			print(answer)  # Печатаем ответ от сервера в косоль для наглядности
		# except (ValueError, json.JSONDecodeError):
		#     print('Не удалось декодировать сообщение сервера.')
		except json.JSONDecodeError:
			CLIENT_LOGGER.error('Не удалось декодировать полученную Json строку.')
			sys.exit(1)
		except ServerError as error:
			CLIENT_LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
			sys.exit(1)
		except ReqFieldMissingError as missing_error:
			CLIENT_LOGGER.error(f'В ответе сервера отсутствует необходимое поле '
								f'{missing_error.missing_field}')
			sys.exit(1)
		except ConnectionRefusedError:
			CLIENT_LOGGER.critical(f'Не удалось подключиться к серверу {server_address}:{server_port}, '
								   f'сервер отверг запрос на подключение.')
			sys.exit(1)
		else:

			# Инициализация БД
			database = ClientDatabase(client_name)
			ClientApp.database_load(transport, database, client_name)

			# Если соединение с сервером установлено корректно,
			# запускаем клиенский процесс приёма сообщний
			receiver = threading.Thread(target=ClientApp.message_from_server, args=(transport, self.client_name))
			receiver.daemon = True
			receiver.start()

			# затем запускаем отправку сообщений и взаимодействие с пользователем.
			user_interface = threading.Thread(target=ClientApp.user_interactive, args=(transport, self.client_name))
			user_interface.daemon = True
			user_interface.start()
			CLIENT_LOGGER.debug('Запущены процессы')



			# Watchdog основной цикл, если один из потоков завершён,
			# то значит или потеряно соединение или пользователь
			# ввёл exit. Поскольку все события обработываются в потоках,
			# достаточно просто завершить цикл.
			while True:
				time.sleep(1)
				if receiver.is_alive() and user_interface.is_alive():
					continue
				break

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


if __name__ == '__main__':
	server_address, server_port, client_name = arg_parser()
	ClientApp = ClientApp(server_address, server_port, client_name)
	ClientApp.main()

# client.py -a 192.168.0.106 -p 8888 -u TestSender1
# client.py -a 192.168.0.49 -p 8888 -u TestSender1
# client.py -a 192.168.0.66 -p 8888 -u TestSender1
# client.py 192.168.0.49 8888 -m send -u TestSender1
