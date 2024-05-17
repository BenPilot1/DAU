import socket
import threading
from encryption import *
import pymongo

ADDRESS = '0.0.0.0', 60000
kill_all = False
number_of_clients = 0
clients = []
threads = []
connected_users = 0
key = get_key().encode()
mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
DAU = mongo_client["DAU"]
users = DAU.accounts["users"]
# users.insert_one({'username': 'dive', 'password': 'kick', "online": "False"})
# users.insert_one({'username': 'kick', 'password': 'dive', "online": "False"})
# users.insert_one({'username': 'crewmate', 'password': 'impostor', "online": "False"})
# users.insert_one({'username': 'among', 'password': 'us', "online": "False"})
class Client:
    def __init__(self, addr: tuple[str, int], sock: socket):
        self.addr = addr
        self.sock = sock
        self.sock.settimeout(0.02)
        self.status = 'WAITING'
        self.online = False
        self.username = ''

    def set_username(self, username):
        self.username = username
def recv_by_size(client: Client) -> str:
    try:
        data_length = int(client.sock.recv(9)[:8])
        data_bytes = decrypt(client.sock.recv(data_length).decode())
        print(f'recv {data_bytes}')
        return data_bytes
    except socket.timeout:
        return 'Time Out'
    except socket.error:
        return ''
    except ValueError:
        return ''


def send_with_size(client: Client, data: str):
    data_bytes = encrypt(data).encode()
    data_length = str(len(data_bytes)).zfill(8).encode()
    while True:
        try:
            client.sock.send(data_length + b'~' + data_bytes)
            print(f'sent {data}')
            return False
        except socket.timeout:
            pass
        except socket.error:
            return True


def handle_request(client: Client, data: str) -> bool:
    global connected_users
    data_fields = data.split('~')
    if data_fields[0] == 'EXIT':
        print('Client asked for disconnection')
        return True
    elif data_fields[0] == 'BTL':
        print('Client asked to return to login')
        connected_users -= 1
        users.update_one({'username': client.username}, {'$set': {'online': "False"}})
    elif data_fields[0] == 'STATUS':
        for other_client in clients:
            if other_client != client and other_client.status == 'IN GAME':
                send_with_size(other_client, 'ENEMY~' + '~'.join(data_fields[1:]))
    elif data_fields[0] == 'SIGNUP':
        if users.find_one({'username': data_fields[1]}) is None:
            users.insert_one({'username': data_fields[1], 'password': data_fields[2], "online": "True"})
            client.online = True
            send_with_size(client, 'CORRECT')
            client.set_username(data_fields[1])
            connected_users += 1
        else:
            send_with_size(client, 'EXISTS')
    elif data_fields[0] == 'LOGIN':
        if users.find_one({'username': data_fields[1], 'password': data_fields[2], 'online': "False"}) is not None:
            send_with_size(client, 'CORRECT')
            client.online = True
            client.set_username(data_fields[1])
            users.update_one({'username': data_fields[1]}, {'$set': {'online': "True"}})
            connected_users += 1
        elif users.find_one({'username': data_fields[1], 'password': data_fields[2], 'online': "True"}) is not None:
            send_with_size(client, 'TAKEN')
        else:
            send_with_size(client, 'WRONG')
    return False


def handle_client(addr: tuple[str, int], client_sock: socket):
    global connected_users
    client = Client(addr, client_sock)
    clients.append(client)
    connected = True
    while not kill_all and connected:
        while not kill_all and connected:
            data = recv_by_size(client)
            if data == '':
                connected = False
                break
            elif data != 'Time Out':
                if handle_request(client, data):
                    connected = False
                    break

            if connected_users >= 2:
                send_with_size(client, f'START~{clients.index(client) + 1}')
                client.status = 'IN GAME'
                break

        while not kill_all and connected:
            data = recv_by_size(client)
            if data == 'Time Out':
                continue
            elif data == '':
                connected = False
                break
            else:
                if handle_request(client, data):
                    connected = False
                    break
            if connected_users < 2:
                client.status = 'WAITING'
                send_with_size(client, 'WAIT')
                break
    if client.online:
        connected_users -= 1
        users.update_one({'username': client.username}, {'$set': {'online': "False"}})
    client.sock.close()
    clients.remove(client)


def main():

    server_socket = socket.socket()
    server_socket.bind(ADDRESS)
    server_socket.listen()

    while not kill_all:
        client_sock, addr = server_socket.accept()
        client_sock.send(key)
        print(f'{addr[0]}:{addr[1]} connected')
        if len(clients) >= 2:
            print(f'{addr[0]}:{addr[1]} disconnected')
            client_sock.close()
        else:
            threads.append(threading.Thread(target=handle_client, args=(addr, client_sock)).start())

    for thread in threads:
        thread.join()

    server_socket.close()


if __name__ == '__main__':
    main()
