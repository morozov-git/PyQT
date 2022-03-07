"""Утилиты"""

import json
import sys

from variables import *
import argparse
from common.variables import *


def get_message(client):
    '''
    Утилита приёма и декодирования сообщения
    принимает байты выдаёт словарь, если приняточто-то другое отдаёт ошибку значения
    :param client:
    :return:
    '''

    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


def send_message(sock, message):
    '''
    Утилита кодирования и отправки сообщения
    принимает словарь и отправляет его
    :param sock:
    :param message:
    :return:+
    '''

    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)


# server_with_db.py arg_parser()
# def arg_parser():
#     '''
#     Парсер аргументов коммандной строки
#     Загрузка параметров командной строки, если нет параметров, то задаём значения по умоланию.
#     Сначала обрабатываем порт:
#     server_with_db.py -p 8079 -a 192.168.0.86
#     :return:
#     '''
#
#     # try:
#     #     if '-p' in sys.argv:
#     #         self.listen_port = int(sys.argv[sys.argv.index('-p') + 1])
#     #     else:
#     #         self.listen_port = DEFAULT_PORT
#     #     if self.listen_port < 1024 or self.listen_port > 65535:
#     #         raise ValueError
#     # except IndexError:
#     #     # print('После параметра -\'p\' необходимо указать номер порта.')
#     #     SERVER_LOGGER.error(f'После параметра -\'p\' необходимо указать номер порта.')
#     #     # sys.exit(1)
#     #     # для тестов
#     #     return 'PORT NOT SET'
#     #
#     # except ValueError:
#     #     # print('В качастве порта может быть указано только число в диапазоне от 1024 до 65535.')
#     #     SERVER_LOGGER.error(f'В качастве порта может быть указано только число в диапазоне от 1024 до 65535.')
#     #     # sys.exit(1)
#     #     # для тестов
#     #     return 'BAD PORT'
#     #
#     # # Затем загружаем какой адрес слушать
#     #
#     # try:
#     #     if '-a' in sys.argv:
#     #         self.listen_address = sys.argv[sys.argv.index('-a') + 1]
#     #     else:
#     #         self.listen_address = ''
#     #
#     # except IndexError:
#     #     # print('После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')
#     #     SERVER_LOGGER.error(f'После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')
#     #     sys.exit(1)
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
#     parser.add_argument('-a', default='', nargs='?')
#     namespace = parser.parse_args(sys.argv[2:])
#     listen_address = namespace.a
#     listen_port = namespace.p
#
#     # Проверки вводимых данных перенесены в дескрипторы
#
#     # # проверка получения корретного номера порта для работы сервера.
#     # if not 1023 < listen_port < 65536:
#     #     SERVER_LOGGER.critical(f'Попытка запуска сервера с указанием неподходящего порта '
#     #                            f'{listen_port}. Допустимы адреса с 1024 до 65535.')
#     #     sys.exit(1)
#
#     return listen_address, listen_port


def arg_parser():
    """
    Создаём парсер аргументов коммандной строки
    и читаем параметры, возвращаем 3 параметра
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--ip_address', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('-p', '--port', default=DEFAULT_PORT, type=int, nargs='?')
    # parser.add_argument('-m', '--mode', default='listen', nargs='?')
    parser.add_argument('-u', '--user', default='Guest', nargs='?')
    parser.add_argument('-pw', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[2:])
    server_address = namespace.ip_address
    server_port = namespace.port
    # client_mode = namespace.mode
    client_name = namespace.user
    client_password = namespace.password
    module_name = argparse.ArgumentParser().prog
    if 'server' in module_name:
        return server_address, server_port
    else:
    # # проверим подходящий номер порта
    # if not 1023 < server_port < 65536:
    #     CLIENT_LOGGER.critical(f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
    #                            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
    #     sys.exit(1)
    # # Проверим допустим ли выбранный режим работы клиента
    # if client_mode not in ('listen', 'send'):
    #     CLIENT_LOGGER.critical(f'Указан недопустимый режим работы {client_mode}, '
    #                            f'допустимые режимы: listen , send')
    #     sys.exit(1)
        return server_address, server_port, client_name, client_password  # client_mode,