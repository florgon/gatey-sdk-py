class GateyApiError(Exception):
    def __init__(
        self, message: str, error_code: int, error_message: str, error_status: int
    ):
        super().__init__(message)
        self.error_code = error_code
        self.error_message = error_message
        self.error_status = error_status
