class BusinessError(Exception):
    """携带稳定业务错误码的可预期失败。"""

    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message

