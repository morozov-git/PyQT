""" SQL Alchemy. настройка базы данных для клиентов. """

from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime


class ClientDatabase:
	""" Класс - база данных клиента. """

	class KnownUsers:
		""" Класс - отображение таблицы известных пользователей. """

		def __init__(self, user):
			self.id = None
			self.username = user

	class MessageHistory:
		""" Класс - отображение таблицы истории сообщений. """

		def __init__(self, from_user, to_user, message):
			self.id = None
			self.from_user = from_user
			self.to_user = to_user
			self.message = message
			self.date = datetime.datetime.now()

	class Contacts:
		""" Класс - отображение списка контактов. """

		def __init__(self, contact):
			self.id = None
			self.name = contact

	# Конструктор класса:
	def __init__(self, client_name):
		# Создаём движок базы данных, поскольку разрешено несколько клиентов одновременно, каждый должен иметь свою БД
		# Поскольку клиент мультипоточный необходимо отключить проверки на подключения с разных потоков,
		# иначе sqlite3.ProgrammingError
		self.database_engine = create_engine(
			f'sqlite:///Client/client_{client_name}.db3',
			echo=False, pool_recycle=7200,
			connect_args={'check_same_thread': False}
		)

		# Создаём объект MetaData
		self.metadata = MetaData()

		# Создаём таблицу известных пользователей
		users = Table(
			'known_users',
			self.metadata,
			Column('id', Integer, primary_key=True),
			Column('username', String)
		)

		# Создаём таблицу истории сообщений
		history = Table(
			'message_history',
			self.metadata,
			Column('id', Integer, primary_key=True),
			Column('from_user', String),
			Column('to_user', String),
			Column('message', Text),
			Column('date', DateTime)
		)

		# Создаём таблицу контактов
		contacts = Table(
			'contacts',
			self.metadata,
			Column('id', Integer, primary_key=True),
			Column('name', String, unique=True)
		)

		# Создаём таблицы
		self.metadata.create_all(self.database_engine)

		# Создаём отображения
		mapper(self.KnownUsers, users)
		mapper(self.MessageHistory, history)
		mapper(self.Contacts, contacts)

		# Создаём сессию
		session = sessionmaker(bind=self.database_engine)
		self.session = session()

		# Необходимо очистить таблицу контактов, т.к. при запуске они подгружаются с сервера.
		self.session.query(self.Contacts).delete()
		self.session.commit()

	# Функция добавления контактов
	def add_contact(self, contact):
		if not self.session.query(self.Contacts).filter_by(name=contact).count():
			contact_row = self.Contacts(contact)
			self.session.add(contact_row)
			self.session.commit()

	# Функция удаления контакта
	def del_contact(self, contact):
		self.session.query(self.Contacts).filter_by(name=contact).delete()

	# Функция добавления известных пользователей.
	# Пользователи получаются только с сервера, поэтому таблица очищается.
	def add_users(self, users_list):
		self.session.query(self.KnownUsers).delete()
		for user in users_list:
			user_row = self.KnownUsers(user)
			self.session.add(user_row)
		self.session.commit()

	def contacts_clear(self):
		""" Функция очищающая таблицу со списком контактов. """

		self.session.query(self.Contacts).delete()

	def save_message(self, from_user, to_user, message):
		""" Функция сохраняющяя сообщения. """

		message_row = self.MessageHistory(from_user, to_user, message)
		self.session.add(message_row)
		self.session.commit()

	def get_contacts(self):
		""" Функция возвращающяя контакты. """

		return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

	def get_users(self):
		""" Функция возвращающяя список известных пользователей. """

		return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

	def check_user(self, user):
		""" Функция проверяющяя наличие пользователя в известных. """

		if self.session.query(self.KnownUsers).filter_by(username=user).count():
			return True
		else:
			return False

	def check_contact(self, contact):
		""" Функция проверяющяя наличие пользователя контактах. """

		if self.session.query(self.Contacts).filter_by(name=contact).count():
			return True
		else:
			return False

	def get_history(self, from_who=None, to_who=None):
		""" Функция возвращающая историю переписки. """

		query = self.session.query(self.MessageHistory)
		if from_who:
			query = query.filter_by(from_user=from_who)
		if to_who:
			query = query.filter_by(to_user=to_who)
		return [
			(history_row.from_user, history_row.to_user, history_row.message, history_row.date)
			for history_row in query.all()
		]


# отладка
if __name__ == '__main__':
	test_db = ClientDatabase('test1')
	for i in ['test3', 'test4', 'test5']:
		test_db.add_contact(i)
	test_db.add_contact('test4')
	test_db.add_users(['test1', 'test2', 'test3', 'test4', 'test5'])
	test_db.save_message('test1', 'test2', f'Привет! я тестовое сообщение от {datetime.datetime.now()}!')
	test_db.save_message('test2', 'test1', f'Привет! я другое тестовое сообщение от {datetime.datetime.now()}!')
	print(test_db.get_contacts())
	print(test_db.get_users())
	print(test_db.check_user('test1'))
	print(test_db.check_user('test10'))
	print(test_db.get_history('test2'))
	print(test_db.get_history(to_who='test2'))
	print(test_db.get_history('test3'))
	test_db.del_contact('test4')
	print(test_db.get_contacts())
