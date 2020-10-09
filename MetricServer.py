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
        pass


class JsonStoreClass:
    def __init__(self, path):
        self._path = path

    def store(self, name, value, timestamp):
        with open(self._path, '+') as file:
            for i, line in enumerate(file):
                line = json.loads(line)
                if line['name'] == name:
                    line['payload'].append({'value': value, 'timestamp': timestamp})
                    file.seek(i)
                    return
            line = json.dumps({'name': name, 'payload': [{'value': value, 'timestamp': timestamp}]})
            file.write(line)


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