class NotSupportedNoChatID(Exception):
    def __init__(self, message = "Not Supported",*args: object) -> None:
        super().__init__(message,*args)


class NotSupported(Exception):
    def __init__(self, message = "Not Supported",*args: object) -> None:
        super().__init__(message,*args)