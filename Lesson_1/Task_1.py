"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping
будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел
должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять
их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»). При этом ip-адрес
сетевого узла должен создаваться с помощью функции ip_address().
"""

# воспользуемся пинг-командой со следуюшими параметрами:
'''
парвметры для MacOS
-t интервал

Определяет в миллисекундах время ожидания получения сообщения с эхо-ответом, 
которое соответствует сообщению с эхо-запросом. Если сообщение с эхо-ответом 
не получено в пределах заданного интервала, то выдается сообщение об ошибке 
"Request timed out". Интервал по умолчанию равен 4000 (4 секунды).

-c счетчик
Задает число отправляемых сообщений с эхо-запросом. По умолчанию - 4.
'''


from ipaddress import ip_address
from subprocess import Popen, PIPE
from tabulate import tabulate




def host_ping(hosts, timeout=50, count=4):
	results = {'Доступные узлы': [], 'Недоступные узлы': []}
	ip_list = []
	host_list = []
	for host in hosts:
	# Отделяем IP адреса в список
		try:
			ip = ip_address(host)
			ip_list.append(ip)
		except ValueError:
			host_list.append(host)

	for address in (host_list + ip_list):
		process = Popen(f"ping {address} -t {timeout} -c {count}", shell=True, stdout=PIPE)
		process.wait()
		# проверяем код завершения подпроцесса
		if process.returncode == 0:
			results['Доступные узлы'].append(f"{address}")
			print(f'{address} - Узел доступен')
		else:
			results['Недоступные узлы'].append(f"{address}")
			print(f'{address} - Узел не доступен')
	return results


if __name__ == '__main__':
	hosts = ['ya.ru', 'google.ru', '127.0.0.1', '3.3.3.3']
	results = host_ping(hosts)
	print(tabulate(results, headers='keys'))