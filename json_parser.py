import json

class Handle_test:

    def __init__(self, filename):
        self.filename = filename
        self.test_container = self.parse_json()
        self.values_lst = list(self.test_container.values())

    def parse_json(self):
        with open(self.filename) as file:
            return json.loads(file.read())









