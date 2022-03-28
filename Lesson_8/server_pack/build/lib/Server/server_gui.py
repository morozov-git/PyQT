""" PyQT интерфейс. Главное окно сервера. """

import os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, QDialog, QComboBox, \
	QPushButton, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem  # , Qt
from PyQt5.QtCore import QTimer, Qt
import hashlib
import binascii


# # GUI - Создание таблицы QModel, для отображения в окне программы.
# def gui_create_model(database):
#     list_users = database.active_users_list() #список активных юзеров
#     list_ = QStandardItemModel() #Это начинка то что я вставля в главную форму(можно сказать нашу разметку) QTableView
#     list_.setHorizontalHeaderLabels(['Имя Клиента', 'IP Адрес', 'Порт', 'Время подключения'])
#     for row in list_users:
#         user, ip, port, time = row
#         user = QStandardItem(user) # создаем элемент
#         user.setEditable(False) # редактирование
#         ip = QStandardItem(ip)
#         ip.setEditable(False)
#         port = QStandardItem(str(port))
#         port.setEditable(False)
#         # Уберём милисекунды из строки времени, т.к. такая точность не требуется.
#         time = QStandardItem(str(time.replace(microsecond=0)))
#         time.setEditable(False)
#         list_.appendRow([user, ip, port, time])#добавляем строку
#     return list_
#
# # GUI - Функция реализующая заполнение таблицы историей сообщений.
# def create_stat_model(database):
#     # Список записей из базы
#     hist_list = database.message_history()
#
#     # Объект модели данных:
#     list = QStandardItemModel()
#     list.setHorizontalHeaderLabels(
#         ['Имя Клиента', 'Последний раз входил', 'Сообщений отправлено', 'Сообщений получено'])
#     for row in hist_list:
#         user, last_seen, sent, recvd = row
#         user = QStandardItem(user)
#         user.setEditable(False)
#         last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
#         last_seen.setEditable(False)
#         sent = QStandardItem(str(sent))
#         sent.setEditable(False)
#         recvd = QStandardItem(str(recvd))
#         recvd.setEditable(False)
#         list.appendRow([user, last_seen, sent, recvd])#добавляем
#     return list#возвращаем


class MainWindow(QMainWindow):
	""" Класс - основное окно сервера. """

	def __init__(self, database, server, config):
		# Конструктор предка
		super().__init__()

		# База данных сервера
		self.database = database

		self.server_thread = server
		self.config = config

		# Ярлык выхода
		self.exitAction = QAction('Выход', self)
		self.exitAction.setShortcut('Ctrl+Q')
		self.exitAction.triggered.connect(qApp.quit)

		# Кнопка обновить список клиентов
		self.refresh_button = QAction('Обновить список', self)

		# Кнопка настроек сервера
		self.config_btn = QAction('Настройки сервера', self)

		# Кнопка регистрации пользователя
		self.register_btn = QAction('Регистрация пользователя', self)

		# Кнопка удаления пользователя
		self.remove_btn = QAction('Удаление пользователя', self)

		# Кнопка вывести историю сообщений
		self.show_history_button = QAction('История клиентов', self)

		# Статусбар
		self.statusBar()
		self.statusBar().showMessage('Server Working')

		# Тулбар
		self.toolbar = self.addToolBar('MainBar')
		self.toolbar.addAction(self.exitAction)
		self.toolbar.addAction(self.refresh_button)
		self.toolbar.addAction(self.show_history_button)
		self.toolbar.addAction(self.config_btn)
		self.toolbar.addAction(self.register_btn)
		self.toolbar.addAction(self.remove_btn)

		# Настройки геометрии основного окна
		# Поскольку работать с динамическими размерами мы не умеем, и мало
		# времени на изучение, размер окна фиксирован.
		self.setFixedSize(800, 600)
		self.setWindowTitle('Messaging Server alpha release')

		# Надпись о том, что ниже список подключённых клиентов
		self.label = QLabel('Список подключённых клиентов:', self)
		self.label.setFixedSize(240, 15)
		self.label.move(10, 25)

		# Окно со списком подключённых клиентов.
		self.active_clients_table = QTableView(self)
		self.active_clients_table.move(10, 45)
		self.active_clients_table.setFixedSize(780, 400)

		# Таймер, обновляющий список клиентов 1 раз в секунду
		self.timer = QTimer()
		self.timer.timeout.connect(self.create_users_model)
		self.timer.start(1000)

		# Связываем кнопки с процедурами
		self.refresh_button.triggered.connect(self.create_users_model)
		self.show_history_button.triggered.connect(self.show_statistics)
		self.config_btn.triggered.connect(self.server_config)
		self.register_btn.triggered.connect(self.reg_user)
		self.remove_btn.triggered.connect(self.rem_user)

		# Последним параметром отображаем окно.
		self.show()

	def create_users_model(self):
		""" Метод заполняющий таблицу активных пользователей. """

		list_users = self.database.active_users_list()
		list = QStandardItemModel()
		list.setHorizontalHeaderLabels(
			['Имя Клиента', 'IP Адрес', 'Порт', 'Время подключения'])
		for row in list_users:
			user, ip, port, time = row
			user = QStandardItem(user)
			user.setEditable(False)
			ip = QStandardItem(ip)
			ip.setEditable(False)
			port = QStandardItem(str(port))
			port.setEditable(False)
			# Уберём милисекунды из строки времени, т.к. такая точность не
			# требуется.
			time = QStandardItem(str(time.replace(microsecond=0)))
			time.setEditable(False)
			list.appendRow([user, ip, port, time])
		self.active_clients_table.setModel(list)
		self.active_clients_table.resizeColumnsToContents()
		self.active_clients_table.resizeRowsToContents()

	def show_statistics(self):
		""" Метод создающий окно со статистикой клиентов. """

		global stat_window
		stat_window = StatWindow(self.database)
		stat_window.show()

	def server_config(self):
		""" Метод создающий окно с настройками сервера. """

		global config_window
		# Создаём окно и заносим в него текущие параметры
		config_window = ConfigWindow(self.config)

	def reg_user(self):
		""" Метод создающий окно регистрации пользователя. """

		global reg_window
		reg_window = RegisterUser(self.database, self.server_thread)
		reg_window.show()

	def rem_user(self):
		""" Метод создающий окно удаления пользователя. """

		global rem_window
		rem_window = DelUserDialog(self.database, self.server_thread)
		rem_window.show()


class DelUserDialog(QDialog):
	""" Класс - диалог выбора контакта для удаления. """

	def __init__(self, database, server):
		super().__init__()
		self.database = database
		self.server = server

		self.setFixedSize(350, 120)
		self.setWindowTitle('Удаление пользователя')
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.setModal(True)

		self.selector_label = QLabel('Выберите пользователя для удаления:', self)
		self.selector_label.setFixedSize(200, 20)
		self.selector_label.move(10, 0)

		self.selector = QComboBox(self)
		self.selector.setFixedSize(200, 20)
		self.selector.move(10, 30)

		self.btn_ok = QPushButton('Удалить', self)
		self.btn_ok.setFixedSize(100, 30)
		self.btn_ok.move(230, 20)
		self.btn_ok.clicked.connect(self.remove_user)

		self.btn_cancel = QPushButton('Отмена', self)
		self.btn_cancel.setFixedSize(100, 30)
		self.btn_cancel.move(230, 60)
		self.btn_cancel.clicked.connect(self.close)

		self.all_users_fill()

	def all_users_fill(self):
		""" Метод заполняющий список пользователей. """

		self.selector.addItems([item[0]
								for item in self.database.users_list()])

	def remove_user(self):
		""" Метод - обработчик удаления пользователя. """

		self.database.remove_user(self.selector.currentText())
		if self.selector.currentText() in self.server.names:
			sock = self.server.names[self.selector.currentText()]
			del self.server.names[self.selector.currentText()]
			self.server.remove_client(sock)
		# Рассылаем клиентам сообщение о необходимости обновить справочники
		self.server.service_update_lists()
		self.close()


class StatWindow(QDialog):
	"""	Класс - окно со статистикой пользователей. """

	def __init__(self, database):
		super().__init__()

		self.database = database
		self.initUI()

	def initUI(self):
		# Настройки окна:
		self.setWindowTitle('Статистика клиентов')
		self.setFixedSize(600, 700)
		self.setAttribute(Qt.WA_DeleteOnClose)

		# Кнапка закрытия окна
		self.close_button = QPushButton('Закрыть', self)
		self.close_button.move(250, 650)
		self.close_button.clicked.connect(self.close)

		# Лист с собственно статистикой
		self.stat_table = QTableView(self)
		self.stat_table.move(10, 10)
		self.stat_table.setFixedSize(580, 620)

		self.create_stat_model()

	def create_stat_model(self):
		""" Метод реализующий заполнение таблицы статистикой сообщений. """

		# Список записей из базы
		stat_list = self.database.message_history()

		# Объект модели данных:
		list = QStandardItemModel()
		list.setHorizontalHeaderLabels(
			['Имя Клиента', 'Последний раз входил', 'Сообщений отправлено', 'Сообщений получено'])
		for row in stat_list:
			user, last_seen, sent, recvd = row
			user = QStandardItem(user)
			user.setEditable(False)
			last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
			last_seen.setEditable(False)
			sent = QStandardItem(str(sent))
			sent.setEditable(False)
			recvd = QStandardItem(str(recvd))
			recvd.setEditable(False)
			list.appendRow([user, last_seen, sent, recvd])
		self.stat_table.setModel(list)
		self.stat_table.resizeColumnsToContents()
		self.stat_table.resizeRowsToContents()


class ConfigWindow(QDialog):
	""" Класс окно настроек. """

	def __init__(self, config):
		super().__init__()
		self.config = config
		self.initUI()

	def initUI(self):
		""" Настройки окна. """

		self.setFixedSize(365, 260)
		self.setWindowTitle('Настройки сервера')
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.setModal(True)

		# Надпись о файле базы данных:
		self.db_path_label = QLabel('Путь до файла базы данных: ', self)
		self.db_path_label.move(10, 10)
		self.db_path_label.setFixedSize(240, 15)

		# Строка с путём базы
		self.db_path = QLineEdit(self)
		self.db_path.setFixedSize(250, 20)
		self.db_path.move(10, 30)
		self.db_path.setReadOnly(True)

		# Кнопка выбора пути.
		self.db_path_select = QPushButton('Обзор...', self)
		self.db_path_select.move(275, 28)

		# Метка с именем поля файла базы данных
		self.db_file_label = QLabel('Имя файла базы данных: ', self)
		self.db_file_label.move(10, 68)
		self.db_file_label.setFixedSize(180, 15)

		# Поле для ввода имени файла
		self.db_file = QLineEdit(self)
		self.db_file.move(200, 66)
		self.db_file.setFixedSize(150, 20)

		# Метка с номером порта
		self.port_label = QLabel('Номер порта для соединений:', self)
		self.port_label.move(10, 108)
		self.port_label.setFixedSize(180, 15)

		# Поле для ввода номера порта
		self.port = QLineEdit(self)
		self.port.move(200, 108)
		self.port.setFixedSize(150, 20)

		# Метка с адресом для соединений
		self.ip_label = QLabel('С какого IP принимаем соединения:', self)
		self.ip_label.move(10, 148)
		self.ip_label.setFixedSize(180, 15)

		# Метка с напоминанием о пустом поле.
		self.ip_label_note = QLabel(' оставьте это поле пустым, чтобы\n принимать соединения с любых адресов.', self)
		self.ip_label_note.move(10, 168)
		self.ip_label_note.setFixedSize(500, 30)

		# Поле для ввода ip
		self.ip = QLineEdit(self)
		self.ip.move(200, 148)
		self.ip.setFixedSize(150, 20)

		# Кнопка сохранения настроек
		self.save_btn = QPushButton('Сохранить', self)
		self.save_btn.move(190, 220)

		# Кнапка закрытия окна
		self.close_button = QPushButton('Закрыть', self)
		self.close_button.move(275, 220)
		self.close_button.clicked.connect(self.close)

		self.db_path_select.clicked.connect(self.open_file_dialog)

		self.show()

		self.db_path.insert(self.config['SETTINGS']['Database_path'])
		self.db_file.insert(self.config['SETTINGS']['Database_file'])
		self.port.insert(self.config['SETTINGS']['Default_port'])
		self.ip.insert(self.config['SETTINGS']['Listen_Address'])
		self.save_btn.clicked.connect(self.save_server_config)

	def open_file_dialog(self):
		""" Метод обработчик открытия окна выбора папки. """

		global dialog
		dialog = QFileDialog(self)
		path = dialog.getExistingDirectory()
		path = path.replace('/', '\\')
		self.db_path.clear()
		self.db_path.insert(path)

	def save_server_config(self):
		"""	Метод сохранения настроек.
		Проверяет правильность введённых данных и если всё правильно сохраняет ini файл. """

		global config_window
		message = QMessageBox()
		self.config['SETTINGS']['Database_path'] = self.db_path.text()
		self.config['SETTINGS']['Database_file'] = self.db_file.text()
		try:
			port = int(self.port.text())
		except ValueError:
			message.warning(self, 'Ошибка', 'Порт должен быть числом')
		else:
			self.config['SETTINGS']['Listen_Address'] = self.ip.text()
			if 1023 < port < 65536:
				self.config['SETTINGS']['Default_port'] = str(port)
				dir_path = os.getcwd()
				dir_path = os.path.join(dir_path, '../..')
				with open(f"{dir_path}/{'server.ini'}", 'w') as conf:
					self.config.write(conf)
					message.information(
						self, 'OK', 'Настройки успешно сохранены!')
			else:
				message.warning(
					self, 'Ошибка', 'Порт должен быть от 1024 до 65536')


class RegisterUser(QDialog):
	""" Класс диалог регистрации пользователя на сервере. """

	def __init__(self, database, server):
		super().__init__()

		self.database = database
		self.server = server

		self.setWindowTitle('Регистрация')
		self.setFixedSize(175, 183)
		self.setModal(True)
		self.setAttribute(Qt.WA_DeleteOnClose)

		self.label_username = QLabel('Введите имя пользователя:', self)
		self.label_username.move(10, 10)
		self.label_username.setFixedSize(150, 15)

		self.client_name = QLineEdit(self)
		self.client_name.setFixedSize(154, 20)
		self.client_name.move(10, 30)

		self.label_password = QLabel('Введите пароль:', self)
		self.label_password.move(10, 55)
		self.label_password.setFixedSize(150, 15)

		self.client_password = QLineEdit(self)
		self.client_password.setFixedSize(154, 20)
		self.client_password.move(10, 75)
		self.client_password.setEchoMode(QLineEdit.Password)
		self.label_conf = QLabel('Введите подтверждение:', self)
		self.label_conf.move(10, 100)
		self.label_conf.setFixedSize(150, 15)

		self.client_conf = QLineEdit(self)
		self.client_conf.setFixedSize(154, 20)
		self.client_conf.move(10, 120)
		self.client_conf.setEchoMode(QLineEdit.Password)

		self.btn_ok = QPushButton('Сохранить', self)
		self.btn_ok.move(10, 150)
		self.btn_ok.clicked.connect(self.save_data)

		self.btn_cancel = QPushButton('Выход', self)
		self.btn_cancel.move(90, 150)
		self.btn_cancel.clicked.connect(self.close)

		self.messages = QMessageBox()

		self.show()

	def save_data(self):
		""" Метод проверки правильности ввода и сохранения в базу нового пользователя. """

		if not self.client_name.text():
			self.messages.critical(
				self, 'Ошибка', 'Не указано имя пользователя.')
			return
		elif self.client_password.text() != self.client_conf.text():
			self.messages.critical(
				self, 'Ошибка', 'Введённые пароли не совпадают.')
			return
		elif self.database.check_user(self.client_name.text()):
			self.messages.critical(
				self, 'Ошибка', 'Пользователь уже существует.')
			return
		else:
			# Генерируем хэш пароля, в качестве соли будем использовать логин в
			# нижнем регистре.
			password_bytes = self.client_password.text().encode('utf-8')
			salt = self.client_name.text().lower().encode('utf-8')
			passwd_hash = hashlib.pbkdf2_hmac(
				'sha512', password_bytes, salt, 10000)
			self.database.add_user(
				self.client_name.text(),
				binascii.hexlify(passwd_hash))
			self.messages.information(
				self, 'Успех', 'Пользователь успешно зарегистрирован.')
			# Рассылаем клиентам сообщение о необходимости обновить справичники
			self.server.service_update_lists()
			self.close()


class HistoryWindow(QDialog):
	""" Класс окна с историей пользователей. """

	# QWidget в QDialog - нет развертывания и скрытия только 2 кнопки
	# крыть и ?
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		# Настройки окна:
		self.setWindowTitle('Статистика клиентов')
		self.setFixedSize(600, 700)
		self.setAttribute(Qt.WA_DeleteOnClose)

		# Кнапка закрытия окна
		self.close_button = QPushButton('Закрыть', self)
		self.close_button.move(250, 650)
		self.close_button.clicked.connect(self.close)

		# Лист с собственно историей
		self.history_table = QTableView(self)
		self.history_table.move(10, 10)
		self.history_table.setFixedSize(580, 620)

		self.show()
