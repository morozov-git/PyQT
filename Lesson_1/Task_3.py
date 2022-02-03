"""
Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2.
Но в данном случае результат должен быть итоговым по всем ip-адресам, представленным в табличном формате
(использовать модуль tabulate). Таблица должна состоять из двух колонок
"""


from tabulate import tabulate
from Task_2 import host_range_ping

def host_range_ping_tab():
	ip, available_list = host_range_ping()
	tabulate_available_list = tabulate(available_list, headers='keys')
	return tabulate_available_list

if __name__ == '__main__':
	print(host_range_ping_tab())

