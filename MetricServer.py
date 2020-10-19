import asyncio
import json


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
            store = self._store.get(name)
        except json.JSONDecodeError:
            return 'error\nstore error\n\n'

        response = 'ok\n'
        dict_index = next((i for i, item in enumerate(store['data']) if item["name"] == name))
        if dict_index is not None:
            for value in store['data'][dict_index]['payload']:
                response += f'{name} {value["value"]} {value["timestamp"]}\n'
        response += '\n'
        print(response.encode())
        return response


class JsonStoreClass:
    def __init__(self, path):
        self._path = path

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

    def get(self, name):
        with open(self._path, 'r') as file:
            data = json.load(file)
        return data


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
