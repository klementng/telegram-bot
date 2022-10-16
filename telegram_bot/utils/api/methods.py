"""
Wrappers/Callable Classes for request.post() to telegrams servers.

More Infomation: https://core.telegram.org/bots/api/#available-methods

"""

import dataclasses
from typing import Optional, Union
import requests

from utils.api.objects import TelegramObject, InlineKeyboardMarkup


class TelegramMethods:
    """
    Base telegram methods class
    
    Attributes:
    methods: name of telegram methods 
    """

    def __init__(self, method: str, **kwargs) -> None:
        self.method = method
        self.__dict__.update(kwargs)

    def __call__(self, *args, **kwargs):
        return self.post(*args, *kwargs)

    def post_url(self, token: str):
        return f'https://api.telegram.org/bot{token}/{self.method}'

    def response_dict(self):
        response_dict = {}

        for name, value in vars(self).items():
            if not (name.startswith('__') or isinstance(value, classmethod)):
                
                if name == 'method':
                    continue

                if isinstance(value, TelegramObject):
                    response_dict.update({name: value.to_json()})
                else:
                    response_dict[name] = value

        return response_dict

    def post(self, token, raise_errors=False):

        r = requests.post(
            url=self.post_url(token),
            params=self.response_dict()
        )

        if raise_errors == True:
            r.raise_for_status()

        return r.status_code


@dataclasses.dataclass
class SendMessage(TelegramMethods):
    chat_id: Union[int, str]
    text: str

    _: dataclasses.KW_ONLY
    reply_markup: Optional[InlineKeyboardMarkup] = None
    parse_mode: Optional[str] = None

    caption_entities: Optional[list] = None
    disable_notification: Optional[bool] = None
    protect_content: Optional[bool] = None
    reply_to_message_id: Optional[str] = None
    allow_sending_without_reply: Optional[bool] = None

    def post_url(self, token: str):
        return f'https://api.telegram.org/bot{token}/sendMessage'


@dataclasses.dataclass
class SendPhoto(TelegramMethods):

    chat_id: Union[str,int]
    photo: bytes
    caption: Optional[str] = None
    reply_markup: Optional[dict] = None
    parse_mode: Optional[str] = None

    caption_entities: Optional[list] = None
    disable_notification: Optional[bool] = None
    protect_content: Optional[bool] = None
    reply_to_message_id: Optional[str] = None
    allow_sending_without_reply: Optional[bool] = None

    def post_url(self, token: str):
        return f'https://api.telegram.org/bot{token}/sendPhoto'

    def post(self, token, raise_errors=False):
        params = self.response_dict()
        photo = params.pop('photo')

        r = requests.post(
            url=self.post_url(token),
            params=params,
            files={'photo': photo}
        )

        if raise_errors == True:
            r.raise_for_status()

        return r.status_code
