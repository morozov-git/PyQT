"""Декораторы"""

import sys
import logging
import logs.config_server_log
import logs.config_client_log
import traceback
import inspect

# метод определения модуля, источника запуска.
# Метод find () возвращает индекс первого вхождения искомой подстроки,
# если он найден в данной строке.
# Если его не найдено, - возвращает -1.
# os.path.split(sys.argv[0])[1]
if sys.argv[1].find('client') == -1:
    # если не клиент то сервер!
    LOGGER = logging.getLogger('server')
else:
    # ну, раз не сервер, то клиент
    LOGGER = logging.getLogger('client')








# Реализация в виде класса
class Log:
    """Класс-декоратор"""
    def __call__(self, func_to_log):
        def log_saver(*args, **kwargs):
            """Обертка"""
            ret = func_to_log(*args, **kwargs)
            # ret = __call__(self)
            # ret = self
            LOGGER.debug(f'Запущено приложение {func_to_log.__name__},'
                         f'c параметрами {traceback.sys.argv}'
                         f' функции {traceback.format_stack()[0].strip().split()[-1]}.')
                        # f'Вызов из функции {inspect.stack()[1][3]}'
            return ret
        return log_saver