class NotSupportedNoChatID(Exception):
    """Expection class in cases where chat_id is not available """
    def __init__(self, message = "Not Supported",*args: object) -> None:
        super().__init__(message,*args)


class NotSupportedErr(Exception):
    """Expection class for non implemented objects or recongized commands"""
    def __init__(self, message = "Not Supported",*args: object) -> None:
        super().__init__(message,*args)