import asyncio
import json
import os


class ServerError(Exception):
    """Server Exception Class"""
    pass


class ClientServerProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None
        self._store = JsonStoreClass('store.json')

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        resp = self.process_data(data.decode())
        self.transport.write(resp.encode())

    def process_data(self, data):
        command, payload = data.split(maxsplit=1)

        if command == 'put':
            key, value, timestamp = payload.split()
            response = self.put(key, value, timestamp)
        elif command == 'get':
            response = self.get(payload)
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
            response = self._store.get(name)
            return response
        except json.JSONDecodeError:
            return 'error\nstore error\n\n'


class JsonStoreClass:
    def __init__(self, path):
        self._path = path

    def store(self, name, value, timestamp):
        with open(self._path, 'r') as file:
            data = json.load(file)
            try:
                print(next(item for item in data['data'] if item["name"] == name))
            except (StopIteration, AttributeError):
                data['data'].append({'name': name, 'payload': [{'value': value, 'timestamp': timestamp}]})
        with open(self._path, 'w') as file:
            json.dump(data, file)

    def get(self, name):
        with



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    coroutine = loop.create_server(
        ClientServerProtocol,
        '127.0.0.1', 8181
    )

    server = loop.run_until_complete(coroutine)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()