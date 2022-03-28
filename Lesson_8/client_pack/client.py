""" Программа-клиент. """
import os
import sys
import json
import time

from PyQt5.QtWidgets import QApplication, QMessageBox
from Crypto.PublicKey import RSA
from client_pack.common.utils import get_message, send_message, arg_parser
from client_pack.common.loging_decos import Log
from client_pack.common.errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
import threading
from client_pack.common.descryptors import Port, IpAddress
from client_pack.common.metaclasses import ClientMaker
from client_pack.Client.client_db import ClientDatabase
from client_pack.Client.main_window import ClientMainWindow
from client_pack.Client.start_dialog import UserNameDialog
from client_pack.Client.client_transport import ClientTransport
from client_pack.common.variables import *


# Инициализация клиентского логера
CLIENT_LOGGER = logging.getLogger('client')

# Объект блокировки сокета и работы с базой данных
sock_lock = threading.Lock()
database_lock = threading.Lock()


@Log()
class ClientApp():  #  metaclass=ClientMaker
	"""Класс программы клиента. """

	server_port = Port()
	server_address = IpAddress()

	def __init__(self, server_address, server_port, client_name, client_password):
		"""Параментры подключения. """

		self.client_name = client_name
		self.server_address = server_address
		self.server_port = server_port
		self.client_password = client_password

	def create_exit_message(self):
		""" Функция для консольного интерфейса
		Функция создаёт словарь с сообщением о выходе. """

		return {
			ACTION: EXIT,
			TIME: time.time(),
			ACCOUNT_NAME: self.client_name
		}

	def message_from_server(self, transport):  # , client_name = 'Guest'
		""" Функция для консольного интерфейса.
		Обработчик сообщений других пользователей, поступающих с сервера. """

		while True:
			time.sleep(1)
			with sock_lock:

				try:
					message = get_message(transport)
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

						CLIENT_LOGGER.info(
							f'Получено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
					else:
						CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')

	def create_message(self):  # , client_name = 'Guest'
		""" Функция для консольного интерфейса. Запрашивает текст сообщения и возвращает его.
		Так же завершает работу при вводе подобной комманды. """

		to_user = input('Введите получателя сообщения: ')
		message = input('Введите сообщение для отправки: ')

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

	def user_interactive(self):
		""" Функция для консольного интерфейса. Взаимодействия с пользователем,
		запрашивает команды, отправляет сообщения. """

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
		""" Функция для консольного интерфейса для изменеия контактов. """

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
		""" Функция для консольного интерфейса выводящяя историю сообщений. """

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

	def print_help(self):
		""" Функция для консольного интерфейса выводящяя справку по командам. """

		print('Поддерживаемые команды:')
		print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
		print('history - история сообщений')
		print('contacts - список контактов')
		print('edit - редактирование списка контактов')
		print('help - вывести подсказки по командам')
		print('exit - выход из программы')

	def process_answer(self, message):
		"""
		Функция разбирает ответ сервера
		:param message:
		:return:.
		"""

		CLIENT_LOGGER.debug(f'Разбор сообщения от сервера: {message}')
		if RESPONSE in message:
			if message[RESPONSE] == 200:
				return '200 : OK'
			return f'400 : {message[ERROR]}'
		raise ReqFieldMissingError(RESPONSE)

	def database_load(self):
		""" Функция инициализатор базы данных. Запускается при запуске, загружает данные в базу с сервера. """

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

	def main(self, *args, **kwargs):
		""" Основная функция клиента. """

		# Загружаем параметы коммандной строки

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
				sys.exit(0)

		CLIENT_LOGGER.info(f'Запущен клиент с парамертами: адрес сервера: {self.server_address}, '
						   f'порт: {self.server_port}, пользователь {self.client_name}')

		# переменные для тестов
		if args:
			if args[0] == 'test':
				CLIENT_LOGGER.debug(f'Запущен тест ClientApp с параметрами: {args}')
				sys.argv = args

		# Загружаем ключи с файла, если же файла нет, то генерируем новую пару.
		dir_path = os.getcwd()
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
			sys.exit(1)
		transport.setDaemon(True)
		transport.start()

		# Удалим объект диалога за ненадобностью
		del start_dialog

		# Создаём GUI
		main_window = ClientMainWindow(database, transport, keys)
		main_window.make_connection(transport)
		main_window.setWindowTitle(f'Messenger - {client_name}')
		client_app.exec_()

		# Раз графическая оболочка закрылась, закрываем транспорт
		transport.transport_shutdown()
		transport.join()


if __name__ == '__main__':
	server_address, server_port, client_name, client_password = arg_parser()
	ClientApp = ClientApp(server_address, server_port, client_name, client_password)
	ClientApp.main()

# client.py -a 192.168.0.71 -p 8888 -u TestSender2 -pass TestSender2
# client.py -a 192.168.0.49 -p 8888 -u TestSender1
# client.py -a 192.168.0.66 -p 8888 -u TestSender1
# client.py 192.168.0.49 8888 -m send -u TestSender1
