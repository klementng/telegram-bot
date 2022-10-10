"""
Wrappers/Callable Classes for request.post() to telegrams servers.
"""

import dataclasses
import requests

from utils.api.objects import TelegramObject, InlineKeyboardMarkup

class BasicReply:

    def __init__(self,method:str,**kwargs) -> None:
        self.method = method
        self.__dict__.update(kwargs)
    
    def __call__(self, *args, **kwargs):
        return self.post(*args,*kwargs)
    
    def post_url(self,token:str):
        return f'https://api.telegram.org/bot{token}/{self.method}'

    def response_dict(self):
        response_dict = {}

        for name, value in vars(self).items():
            if not (name.startswith('__') or isinstance(value, classmethod)):
                
                if isinstance(value,TelegramObject):
                    response_dict.update({name:value.to_json()})
                else:
                    response_dict[name] = value

        return response_dict

    def post(self,token,raise_errors=False):

        r= requests.post(
            url=self.post_url(token),
            params=self.response_dict()
        )

        if raise_errors == True:
            r.raise_for_status()

        return r.status_code

@dataclasses.dataclass
class MessageReply(BasicReply):

    chat_id: str
    text: str
    reply_markup:InlineKeyboardMarkup = None
    parse_mode:str = None

    caption_entities:list = None
    disable_notification:bool=None
    protect_content:bool = None
    reply_to_message_id:str = None
    allow_sending_without_reply:bool = None

    def post_url(self,token:str):
        return f'https://api.telegram.org/bot{token}/sendMessage'

        
@dataclasses.dataclass
class PhotoReply(BasicReply):

    chat_id: str
    photo: bytes
    caption:str = None
    reply_markup:dict = None
    parse_mode:str = None
    
    caption_entities:list = None
    disable_notification:bool=None
    protect_content:bool = None
    reply_to_message_id:str = None
    allow_sending_without_reply:bool = None

    def post_url(self,token:str):
        return f'https://api.telegram.org/bot{token}/sendPhoto'
    
    def post(self,token,raise_errors=False):
        params = self.response_dict()
        photo = params.pop('photo')

        r= requests.post(
            url=self.post_url(token),
            params=params,
            files={'photo': photo}
        )

        if raise_errors == True:
            r.raise_for_status()

        return r.status_code