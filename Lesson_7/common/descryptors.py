import logging
logger = logging.getLogger('server')
from ipaddress import ip_address

# Дескриптор для описания порта:
class Port:
    """ Класс дескриптор для проверки корректного номера порта """
    def __set__(self, instance, value):
        # instance - <__main__.Server object at 0x000000D582740C50>
        # value - 7777
        if not 1023 < value < 65536:
            logger.critical(
                f'Попытка запуска сервера с указанием неподходящего порта {value}. Допустимы адреса с 1024 до 65535.')
            exit(1)
        # Если порт прошел проверку, добавляем его в список атрибутов экземпляра
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        # owner - <class '__main__.Server'>
        # name - listen_port
        self.name = name

class IP_Address:
    """ Класс дескриптор для проверки корректного IP адреса """
    def __set__(self, instance, value):
        # instance - <__main__.Server object at 0x000000D582740C50>
        # value - 192.168.0.49
        try:
            ip_address(value)
            # Если адрес прошел проверку, добавляем его в список атрибутов экземпляра
            instance.__dict__[self.name] = value
            # right_ip = value
        except ValueError:
            logger.critical(f"Введен некорректный IP-адрес: {value}")
            exit(1)

    def __set_name__(self, owner, name):
        # owner - <class '__main__.Server'>
        # name - listen_address
        self.name = name