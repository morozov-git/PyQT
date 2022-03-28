""" Тесты для модуля клиента. """

import unittest
# sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import RESPONSE, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE, TEST_MESSAGE
from client import ClientApp


class TeasClientApp(unittest.TestCase):

	def test_create_presence(self):
		test = ClientApp.create_presence()
		test[TIME] = 1.1  # время необходимо приравнять принудительно
		# иначе тест никогда не будет пройден
		self.assertEqual(test, {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}})

	def test_200_answer(self):
		self.assertEqual(ClientApp.process_answer({RESPONSE: 200, TEST_MESSAGE: 'TestMessage'}), '200 : OK')

	def test_no_response(self):
		self.assertRaises(ValueError, ClientApp.process_answer, {TEST_MESSAGE: 'TestMessage'})

	# (что ожидаем в ответе, в какую фунтцию отправляем запрос, данные запроса)
	# self.assertRaises(ValueError, ClientApp.process_answer, {ERROR: 'Bad Request'})

	def test_main_bad_port(self):
		self.assertEqual(ClientApp.main('test', 'client.py', '192.168.0.100', 888), 'BAD PORT')
# self.assertRaises(ValueError, ClientApp.main('test', 'client.py', '192.168.0.100', 888))


# client.py 192.168.0.100 8079
if __name__ == '__main__':
	unittest.main()
