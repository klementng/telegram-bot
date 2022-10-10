"""
This module contains dataclasses for object returned/used by the telegram bot api.

Objects can be be found in "Available types" section in: https://core.telegram.org/bots/api
"""

import numpy as np
import dataclasses
from utils.exceptions import *
from dataclasses import field, dataclass
from dataclasses_json import dataclass_json, config
import utils.api.replies as replies


@dataclass_json
@dataclass
class TelegramObject:
    """Base dataclass of telegram objects"""

    #def to_json 
    #    ....  -- defined in @dataclass_json
    #

    #def to_dict(self):
    #   ....  -- defined in @dataclass_json

    #def from_json
    #    ....  -- defined in @dataclass_json

    #def from_dict(self):
    #   ....  -- defined in @dataclass_json


@dataclass
class Location(TelegramObject):
    _: dataclasses.KW_ONLY
    
    # Guaranteed from api
    longitude: float
    latitude: float

    # Optional
    horizontal_accuracy: float = None
    
    # Optional: Live location only
    live_period: int = None
    heading: float = None
    proximity_alert_radius: float = None


@dataclass
class Chat(TelegramObject):
    _: dataclasses.KW_ONLY

    # Guaranteed from api
    id: str
    type: str

    # Optional
    title: str = None
    username: str = None
    first_name: str = None
    last_name: str = None
    photo: str = None
    bio: str = None
    description: str = None
    permissions: str = None

    # others
    has_private_forwards: str = None
    has_restricted_voice_and_video_messages: bool = None
    join_to_send_messages: bool = None
    join_by_request: bool = None
    invite_link: str = None
    pinned_message: str = None
    slow_mode_delay: int = None
    message_auto_delete_time: int = None
    has_protected_content: bool = None
    sticker_set_name: bool = None
    linked_chat_id: int = None
    location: Location = None

    def __post__init__(self):
        pass


@dataclass
class User(TelegramObject):
    _: dataclasses.KW_ONLY
    # Guaranteed from api
    id: str
    is_bot: bool
    first_name: str

    # useful
    last_name: str = None
    username: str = None

    # others
    language_code: str = None
    is_premium: bool = None
    added_to_attachment_menu: bool = None
    can_join_groups: bool = None
    can_read_all_group_messages: bool = None
    supports_inline_queries: bool = None


@dataclass(init=False)
class Message(TelegramObject):
    # Guaranteed from api
    message_id: int = field()
    chat: Chat = field()
    from_: User = field(metadata=config(field_name="from"))
    message_id: int = field()
    date: str = field()

    # Others (Not included)
    # initizted as instance variable (not included when using to_json())

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

        for key in kwargs:  # handling reserved keyword
            self.__setattr__(key, kwargs[key])

        self.chat = Chat(**kwargs["chat"])
        self.from_ = User(**kwargs["from"])

    def get_content(self):

        if "text" in self.kwargs:
            return self.kwargs['text']

        elif "location" in self.kwargs:
            return Location(**self.kwargs["location"])

        else:
            return None

    def get_chat_id(self):
        return self.chat.id

    def get_chat(self):
        return self.chat

    def get_user(self):
        return self.from_


@dataclass(init=False)
class CallbackQuery(TelegramObject):
    _: dataclasses.KW_ONLY
    id: int
    from_: User = field(metadata=config(field_name="from"))

    # Optional
    data: str = None
    message: Message = None

    inline_message_id = None
    chat_instance = None
    game_short_name = None

    def __init__(self, **kwargs):
        # Dealing with researved keywords 'from' # no checks for excess kwargs
        for key in kwargs:
            self.__setattr__(key, kwargs[key])

        self.from_ = User(
            **kwargs["from"]) if kwargs.get("from") != None else None
        
        self.message = Message(
            **self.message) if self.message != None else None

    def get_user(self) -> User:
        return self.from_

    def get_chat_id(self) -> str:

        if self.message != None:
            return self.message.chat.id
        else:
            return self.from_.id

    def answer(self, token, *args, **kwargs):
        return replies.BasicReply("answerCallbackQuery", callback_query_id=self.id, *args, **kwargs)(token)


@dataclass(init=False)
class InlineKeyboardMarkup(TelegramObject):
    inline_keyboard: dict = field(init=False)

    def __init__(self, labels, callback_data) -> None:
        self.inline_keyboard = InlineKeyboardMarkup._build(
            labels, callback_data)

    @staticmethod
    def _build(labels, data) -> str:
        data = np.array(data)
        labels = np.array(labels)

        if data.shape != labels.shape:
            raise ValueError("label and data shape are not equal")
        elif len(data.shape) == 1 and type(data[0]) == list:
            #TODO: FIND a better solutions 
            pass
        elif len(data.shape) != 2:
            raise ValueError("label and data shape must be 2D")

        inine_keyboard = []

        for i in range(len(labels)):
            tmp = []

            for j in range(len(labels[i])):
                tmp.append(
                    {"text": str(labels[i][j]), "callback_data": str(data[i][j])})

            inine_keyboard.append(tmp)

        return inine_keyboard