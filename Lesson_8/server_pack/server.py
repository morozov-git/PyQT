"""Программа-сервер"""

import configparser
import os
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from server_pack.common.utils import arg_parser
import logging

# from server_pack.Server.core import MessageProcessor
from server_pack.common.descryptors import Port, IpAddress
# from common.loging_decos import Log, login_required
# from common.metaclasses import ServerMaker
import threading
from server_pack.Server.server_gui import MainWindow, ConfigWindow  # , gui_create_model, create_stat_model
from server_pack.common.loging_decos import Log
from server_pack.Server.core import MessageProcessor
from server_pack.Server.server_db import ServerStorage
from server_pack.common.variables import *

# Инициализация серверного логера
SERVER_LOGGER = logging.getLogger('server')

# Флаг что был подключён новый пользователь, нужен чтобы не мучать BD
# постоянными запросами на обновление
new_connection = False
conflag_lock = threading.Lock()


@Log()
class ServerApp():  # class ServerApp(metaclass=ServerMaker):
	""" Класс программы сервера. """

	listen_port = Port()
	listen_address = IpAddress()

	def __init__(self, listen_address, listen_port, gui_flag):
		""" Параментры подключения. """

		self.listen_address = listen_address
		self.listen_port = listen_port
		self.command = ''
		self.gui_flag = gui_flag

		# список клиентов , очередь сообщений
		self.clients = []
		self.messages = []

	# Словарь, содержащий имена пользователей и соответствующие им сокеты.
	names = dict()

	def print_help(self):
		""" Консольный интерфейс сервера. (Справка по командам интерфейса.) """

		print('Поддерживаемые комманды:')
		print('users - список известных пользователей')
		print('connected - список подключенных пользователей')
		print('history - история входов пользователя')
		print('exit - завершение работы сервера.')
		print('help - вывод справки по поддерживаемым командам')

	def server_iterface(self):
		""" Консольный интерфейс сервера (работа с БД). """

		# Печатаем справку:
		self.print_help()

		# Основной цикл сервера:
		while True:
			self.command = input('Введите комманду: ')
			if self.command == 'help':
				self.print_help()
			elif self.command == 'exit':
				# sys.exit(0)
				break
			elif self.command == 'users':
				for user in sorted(self.database.users_list()):
					print(f'Пользователь {user[0]}, последний вход: {user[1]}')
			elif self.command == 'connected':
				active_users_now = sorted(self.database.active_users_list())
				# print(active_users_now)
				if active_users_now:
					for user in active_users_now:
						print(
							f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, время установки соединения: {user[3]}')
				else:
					print('Отсутствуют активные пользователи.')
			elif self.command == 'history':
				name = input(
					'Введите имя пользователя для просмотра истории. Для вывода всей истории, просто нажмите Enter: ')
				for user in sorted(self.database.login_history(name)):
					print(f'Пользователь: {user[0]} время входа: {user[1]}. Вход с: {user[2]}:{user[3]}')
			else:
				print('Команда не распознана.')

	def list_update(self):  # Перенесена в модуль core
		""" Функция обновляющяя список подключённых пользователей,
		проверяет флаг подключения, и если надо обновляет список. """

	# global new_connection
	# if new_connection:
	# 	self.main_window.active_clients_table.setModel(
	# 		gui_create_model(self.database))
	# 	self.main_window.active_clients_table.resizeColumnsToContents()
	# 	self.main_window.active_clients_table.resizeRowsToContents()
	# 	with conflag_lock:
	# 		new_connection = False

	def show_statistics(self):  # Перенесена в модуль core
		"""Функция создающяя окно со статистикой клиентов. """

	# global stat_window
	# stat_window = HistoryWindow()
	# stat_window.history_table.setModel(create_stat_model(self.database))
	# stat_window.history_table.resizeColumnsToContents()
	# stat_window.history_table.resizeRowsToContents()

	# stat_window.show()

	@Log()
	def config_load(self):
		""" Парсер конфигурационного ini файла. """

		config = configparser.ConfigParser()
		dir_path = os.getcwd()
		config.read(f"{dir_path}/{'server.ini'}")
		# Если конфиг файл загружен правильно, запускаемся, иначе конфиг по умолчанию.
		if 'SETTINGS' in config:
			return config
		else:
			config.add_section('SETTINGS')
			config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
			config.set('SETTINGS', 'Listen_Address', '')
			config.set('SETTINGS', 'Database_path', '')
			config.set('SETTINGS', 'Database_file', 'server_database.db3')
			return config

	def server_config(self):
		""" Функция создающяя окно с настройками сервера. """

		global config_window
		# Создаём окно и заносим в него текущие параметры
		config_window = ConfigWindow()
		config_window.db_path.insert(self.config['SETTINGS']['Database_path'])
		config_window.db_file.insert(self.config['SETTINGS']['Database_file'])
		config_window.port.insert(self.config['SETTINGS']['Default_port'])
		config_window.ip.insert(self.config['SETTINGS']['Listen_Address'])
		config_window.save_btn.clicked.connect(self.save_server_config)

	def save_server_config(self):
		""" Функция сохранения настроек. """

		global config_window
		message = QMessageBox()
		self.config['SETTINGS']['Database_path'] = config_window.db_path.text()
		self.config['SETTINGS']['Database_file'] = config_window.db_file.text()
		try:
			port = int(config_window.port.text())
		except ValueError:
			message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
		else:
			self.config['SETTINGS']['Listen_Address'] = config_window.ip.text()
			if 1023 < port < 65536:
				self.config['SETTINGS']['Default_port'] = str(port)
				print(port)
				with open('../server.ini', 'w') as conf:
					self.config.write(conf)
					message.information(
						config_window, 'OK', 'Настройки успешно сохранены!')
			else:
				message.warning(
					config_window,
					'Ошибка',
					'Порт должен быть от 1024 до 65536')

	# @classmethod
	def main(self, *args, **kwargs):
		""" Функция запуска сервера. """

		# Загрузка файла конфигурации сервера
		self.config = ServerApp.config_load()

		# переменные для тестов
		if args:
			if args[0] == 'test':
				SERVER_LOGGER.debug(f'Запущен тест ServerApp с параметрами: {args}')
				sys.argv = args

		SERVER_LOGGER.info(f'Запущен сервер, порт для подключений: {listen_port}, '
						   f'адрес с которого принимаются подключения: {listen_address}. '
						   f'Если адрес не указан, принимаются соединения с любых адресов.')

		server_start_message = f'Server launched. IP: {listen_address} Port: {listen_port}'
		SERVER_LOGGER.debug(server_start_message)
		print(server_start_message)

		# Инициализация базы данных
		database = ServerStorage(
			os.path.join(
				self.config['SETTINGS']['Database_path'],
				self.config['SETTINGS']['Database_file']))
		# self.database = ServerStorage()

		# # Запуск сокета для сервера
		# self.server_socket()

		# # Запуск главного серверного процесса
		# module_main_server = threading.Thread(target=self.main_server_process)
		# module_main_server.daemon = True
		# module_main_server.start()

		# Создание экземпляра класса - сервера и его запуск:
		server = MessageProcessor(self.listen_address, self.listen_port, database)
		server.daemon = True
		server.start()

		# Если  указан параметр без GUI то запускаем простенький обработчик
		# консольного ввода
		if gui_flag:
			while True:
				command = input('Введите exit для завершения работы сервера.')
				if command == 'exit':
					# Если выход, то завршаем основной цикл сервера.
					server.running = False
					server.join()
					break
		# Если не указан запуск без GUI, то запускаем GUI:
		else:
			# Создаём графическое окуружение для сервера:
			server_app = QApplication(sys.argv)
			server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
			main_window = MainWindow(database, server, self.config)

			# Запускаем GUI
			server_app.exec_()

			# По закрытию окон останавливаем обработчик сообщений
			server.running = False

# # Запуск консольного интерфейса сервера
# module_server_iterface = threading.Thread(target=self.server_iterface, daemon=True)
# module_server_iterface.daemon = True
# module_server_iterface.start()

# # Создаём графическое окуружение для сервера:
# server_app = QApplication(sys.argv)
# self.main_window = MainWindow()
# # ЗАПУСК РАБОТАЕТ ПАРАЛЕЛЬНО СЕРВЕРУ
# # ГЛАВНОМ ПОТОКЕ ЗАПУСКАЕМ НАШ GUI - ГРАФИЧЕСКИЙ ИНТЕРФЕС ПОЛЬЗОВАТЕЛЯ

# # Инициализируем параметры в Главное окно
# self.main_window.statusBar().showMessage('Server Working')  # подвал
# self.main_window.active_clients_table.setModel(
# 	gui_create_model(self.database))  # заполняем таблицу основного окна делаем разметку и заполянем ее
# self.main_window.active_clients_table.resizeColumnsToContents()
# self.main_window.active_clients_table.resizeRowsToContents()
#
# # Таймер, обновляющий список клиентов 1 раз в секунду
# timer = QTimer()
# timer.timeout.connect(self.list_update)
# timer.start(1000)

# # Связываем кнопки с процедурами
# self.main_window.refresh_button.triggered.connect(self.list_update)
# self.main_window.show_history_button.triggered.connect(self.show_statistics)
# self.main_window.config_btn.triggered.connect(self.server_config)
#
# # Запускаем GUI в отдельном потоке
# module_server_gui = threading.Thread(target=server_app.exec_(), daemon=True)
# module_server_gui.daemon = True
# module_server_gui.start()
# server_app.exec_()

# # основной цикл, если один из потоков завершён, то значит или потеряно соединение или пользователь
# # ввёл exit. Поскольку все события обработываются в потоках, достаточно просто завершить цикл.
# while True:
# 	time.sleep(1)
# 	if module_main_server.is_alive() and module_server_gui.is_alive():  # module_server_iterface.is_alive() and
# 		# if not module_server_iterface.is_alive():
# 		# 	self.command = 'exit'
# 		# 	time.sleep(1)
# 		# 	print('Server stopped')
# 		# 	sys.exit(0)
# 		continue
# 	self.command = 'exit'
# 	break
# time.sleep(1)
# print('Server stopped')
# sys.exit(0)


if __name__ == '__main__':
	listen_address, listen_port, gui_flag = arg_parser()
	ServerApp = ServerApp(listen_address, listen_port, gui_flag)
	ServerApp.main()

# server.py -a 192.168.0.71 -p 8888
# server.py -p 8888 -a 192.168.0.74
# server.py -p 8888 -a 192.168.0.66
# server.py -p 8888 -a 192.168.0.101
