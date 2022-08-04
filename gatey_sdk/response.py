
class Response:
    _raw_json = {}
    def __init__(self, response):
        self.response = response
        self._raw_json = response.json()
    
    def raw_json(self):
        return self._raw_json
