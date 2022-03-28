""" Общие утилиты. """

import json
import sys

from common.variables import *
import argparse


def get_message(client):
    """ Утилита приёма и декодирования сообщения принимает байты выдаёт словарь,
    если приняточто-то другое отдаёт ошибку значения. """

    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


def send_message(sock, message):
    """ Утилита кодирования и отправки сообщения
    принимает словарь и отправляет его. """

    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)


def arg_parser():
    """ Создаём парсер аргументов коммандной строки и читаем параметры, возвращаем 3 параметра. """

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--ip_address', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('-p', '--port', default=DEFAULT_PORT, type=int, nargs='?')
    # parser.add_argument('-m', '--mode', default='listen', nargs='?')
    parser.add_argument('-u', '--user', default=None, nargs='?')
    parser.add_argument('--no_gui', action='store_true')
    parser.add_argument('-pass', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[2:])
    server_address = namespace.ip_address
    server_port = namespace.port
    # client_mode = namespace.mode
    client_name = namespace.user
    module_name = argparse.ArgumentParser().prog
    gui_flag = namespace.no_gui
    client_password = namespace.password
    if 'server' in module_name:
        return server_address, server_port, gui_flag
    else:
        return server_address, server_port, client_name, client_password  # client_mode,
