import sys
import os
import unittest
# sys.path.append(os.path.join(os.getcwd(), '..'))
from Lesson_5.common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from Lesson_5.server import ServerApp


class TestServerApp(unittest.TestCase):
	error_response = {RESPONSE: 400, ERROR: 'Bad Request'}
	right_response = {RESPONSE: 200}
	TEST_TIME = 'test_time'
	TEST_USER = 'test_user'

	def test_no_action(self):
		self.assertEqual(ServerApp.process_client_message(
			{TIME: self.TEST_TIME, USER: {ACCOUNT_NAME: 'Guest'}}), self.error_response)


	def test_no_time(self):
		self.assertEqual(ServerApp.process_client_message(
			{ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest'}}), self.error_response)

	def test_no_user(self):
		self.assertEqual(ServerApp.process_client_message(
			{ACTION: PRESENCE, TIME: self.TEST_TIME}), self.error_response)

	def test_unknown_user(self):
		self.assertEqual(ServerApp.process_client_message(
			{ACTION: PRESENCE,
			 TIME: self.TEST_TIME,
			 USER: {ACCOUNT_NAME: self.TEST_USER}}), self.error_response)

	def test_right_response(self):
		self.assertEqual(ServerApp.process_client_message(
			{ACTION: PRESENCE,
			 TIME: self.TEST_TIME, USER: {ACCOUNT_NAME: 'Guest'}}), self.right_response)

	def test_main_bad_port(self):
		self.assertEqual(ServerApp.main('test', 'server.py', '-p', 888, '-a', '192.168.0.86'), 'BAD PORT')

	def test_main_not_port(self):
		self.assertEqual(ServerApp.main('test', 'server.py', '-a', '192.168.0.86', '-p'), 'PORT NOT SET')

if __name__ == '__main__':
	unittest.main()
