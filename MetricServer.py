import asyncio
import json
import os
import uuid
import tempfile


def run_server(host, port):
    loop = asyncio.get_event_loop()
    coroutine = loop.create_server(
        ClientServerProtocol,
        host, port
    )

    server = loop.run_until_complete(coroutine)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


class ServerError(Exception):
    """Server Exception Class"""
    pass


class ClientServerProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None
        self._store = None

    def connection_made(self, transport):
        port = transport.get_extra_info('socket').getsockname()[1]
        self._store = JsonStoreClass(str(port) + '.json')
        self.transport = transport

    def data_received(self, data):
        resp = self.process_data(data.decode())
        self.transport.write(resp.encode())

    def process_data(self, data):
        try:
            command, payload = data.split(maxsplit=1)
        except ValueError:
            return 'error\nwrong command\n\n'
        if command == 'put':

            if len(payload.split()) > 3:
                return 'error\nwrong command\n\n'

            key, value, timestamp = payload.split()
            try:
                key, value, timestamp = str(key), float(value), int(timestamp)
            except ValueError:
                return 'error\nwrong command\n\n'

            response = self.put(key, value, timestamp)
        elif command == 'get':

            if len(payload.split()) > 1:
                return 'error\nwrong command\n\n'

            key = payload.strip()
            response = self.get(key)
        else:
            response = 'error\nwrong command\n\n'
        return response

    def put(self, name, value, timestamp):
        try:
            self._store.store(name, value, timestamp)
            return 'ok\n\n'
        except json.JSONDecodeError:
            return 'error\nstore error\n\n'

    def get(self, name):
        try:
            store = self._store.get()
        except json.JSONDecodeError:
            return 'error\nstore error\n\n'

        if name == '*':
            names = [line['name'] for line in store['data']]
        else:
            names = [name]

        print(names)
        response = 'ok\n'
        for key in names:
            dict_index = next((i for i, item in enumerate(store['data']) if item["name"] == key), None)
            if dict_index is not None:
                for value in store['data'][dict_index]['payload']:
                    response += f'{key} {value["value"]} {value["timestamp"]}\n'
        response += '\n'
        return response


class JsonStoreClass:
    def __init__(self, path):
        self._path = path

        if not os.path.exists(self._path):
            with open(self._path, 'w') as file:
                json.dump({'data': []}, file)

    def store(self, name, value, timestamp):
        with open(self._path, 'r') as file:
            data = json.load(file)

            dict_index = next((i for i, item in enumerate(data['data']) if item["name"] == name), None)
            if dict_index is not None:
                value_index = next(
                    (i for i, item in enumerate(data['data'][dict_index]['payload']) if item["timestamp"] == timestamp),
                    None)
                if value_index is not None:
                    data['data'][dict_index]['payload'][value_index]['value'] = value
                else:
                    data['data'][dict_index]['payload'].append({'value': value, 'timestamp': timestamp})
            else:
                data['data'].append({'name': name, 'payload': [{'value': value, 'timestamp': timestamp}]})

        with open(self._path, 'w') as file:
            json.dump(data, file)

    def get(self):
        with open(self._path, 'r') as file:
            data = json.load(file)
        return data


if __name__ == '__main__':
    run_server('127.0.0.1', 8181)

