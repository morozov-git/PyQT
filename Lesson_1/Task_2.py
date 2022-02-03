"""
2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
Меняться должен только последний октет каждого адреса.
По результатам проверки должно выводиться соответствующее сообщение.
"""

from ipaddress import ip_address

from tabulate import tabulate

from Task_1 import host_ping


def host_range_ping():
    while True:
        start_ip = input('Введите первоначальный адрес: ')
        try:
            right_ip = ip_address(start_ip)
            last_oct = int(str(right_ip).split('.')[3])
            break
        except ValueError:
            print("Введен некорректный IP-адрес")
    while True:
        # запрос на количество проверяемых адресов
        n = input('Сколько IP-адресов нужно проверить?: ')
        try:
            amount_ip = int(n)
            # так-как по условию можно менять только последний октет
            if (last_oct + amount_ip) > 256:
                raise Exception
            else:
                break
        except ValueError:
            print('Необходимо ввести целое положительное число: ')
        except Exception:
            print(f'Максимально допустимое количество адресов для проверки: {256-last_oct}')
    # формируем список ip адресов
    ip_list = []
    for i in range(amount_ip):
        ip_list.append(right_ip + i)

    ip_results = host_ping(ip_list)

    return ip_list, ip_results



if __name__ == '__main__':
    ip_list, ip_results = host_range_ping()
    print(f'\nСписок адресов для проверки:\n {ip_list}\n')
    print(tabulate(ip_results, headers='keys'))