
class Response:
    def __init__(self, response):
        self.response = response

    def raw_json(self):
        return self.response.json()
