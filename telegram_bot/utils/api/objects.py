"""
This module contains dataclasses for object returned/used by the telegram bot api.

Objects can be be found in "Available types" section in: https://core.telegram.org/bots/api
"""

import numpy as np
from typing import Optional

from utils.exceptions import *
from dataclasses import InitVar, field, dataclass, KW_ONLY
from dataclasses_json import Undefined, CatchAll, DataClassJsonMixin
from dataclasses_json import dataclass_json, config
import utils.api.methods as methods


@dataclass
class TelegramObject(DataClassJsonMixin):
    """Base dataclass of telegram objects"""

    @classmethod
    def decode(cls, obj):
        if type(obj) == str:
            return cls.from_json(obj)

        elif type(obj) == dict:
            return cls.from_dict(obj)

        else:
            raise ValueError(
                f"{cls.__name__}.decode() only accepts dict/str(json) type")

    # def to_json
    #    ....  -- defined in @dataclass_json
    #

    # def to_dict:
    #   ....  -- defined in @dataclass_json

    # def from_json
    #    ....  -- defined in @dataclass_json

    # def from_dict:
    #   ....  -- defined in @dataclass_json


@dataclass_json
@dataclass
class Location(TelegramObject):
    _: KW_ONLY

    # Guaranteed from api
    longitude: float
    latitude: float

    # Optional
    horizontal_accuracy: Optional[float] = None

    # Optional: Live location only
    live_period: Optional[int] = None
    heading: Optional[float] = None
    proximity_alert_radius: Optional[float] = None


@dataclass_json
@dataclass
class Chat(TelegramObject):
    _: KW_ONLY

    # Guaranteed from api
    id: str
    type: str

    # Optional
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    photo: Optional[str] = None
    bio: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[str] = None

    # others
    has_private_forwards: Optional[str] = None
    has_restricted_voice_and_video_messages: Optional[bool] = None
    join_to_send_messages: Optional[bool] = None
    join_by_request: Optional[bool] = None
    invite_link: Optional[str] = None
    pinned_message: Optional[str] = None
    slow_mode_delay: Optional[int] = None
    message_auto_delete_time: Optional[int] = None
    has_protected_content: Optional[bool] = None
    sticker_set_name: Optional[bool] = None
    linked_chat_id: Optional[int] = None
    location: Optional[Location] = None


@dataclass_json
@dataclass
class User(TelegramObject):
    _: KW_ONLY
    # Guaranteed from api
    id: int
    is_bot: bool
    first_name: str

    # Optional
    last_name: Optional[str] = None
    username: Optional[str] = None

    # others
    language_code: Optional[str] = None
    is_premium: Optional[bool] = None
    added_to_attachment_menu: Optional[bool] = None
    can_join_groups: Optional[bool] = None
    can_read_all_group_messages: Optional[bool] = None
    supports_inline_queries: Optional[bool] = None


@dataclass_json(undefined=Undefined.INCLUDE)
@dataclass
class Message(TelegramObject):
    _: KW_ONLY

    # Guaranteed from api
    message_id: int
    chat: Chat
    from_: User = field(metadata=config(field_name="from"))
    message_id: int
    date: str
    # Others (Not included)
    others: CatchAll

    def get_content(self):

        if isinstance(self.others, dict):

            if "text" in self.others:
                return self.others['text']

            elif "location" in self.others:
                return Location.from_dict(self.others["location"])

        return None

    def get_chat_id(self):
        return self.chat.id

    def get_user_id(self):
        return self.from_.id

    def get_chat(self):
        return self.chat

    def get_user(self):
        return self.from_


@dataclass_json
@dataclass
class CallbackQuery(TelegramObject):
    _: KW_ONLY
    id: str
    from_: User = field(metadata=config(field_name="from"))

    # Optional
    data: Optional[str] = None
    message: Optional[Message] = None

    inline_message_id: Optional[str] = None
    chat_instance: Optional[str] = None
    game_short_name: Optional[str] = None

    def get_user(self) -> User:
        return self.from_

    def get_user_id(self):
        return self.from_.id

    def get_chat_id(self):

        if self.message != None:
            return self.message.chat.id
        else:
            return self.from_.id

    def answer(self, token, *args, **kwargs):
        return methods.TelegramMethods("answerCallbackQuery", callback_query_id=self.id, *args, **kwargs)(token)


@dataclass(init=False)
class InlineKeyboardMarkup(TelegramObject):
    _: KW_ONLY
    inline_keyboard: list = field(init=False, default_factory=list)

    def __init__(self, labels, callback_data) -> None:
        self.inline_keyboard = InlineKeyboardMarkup._build(
            labels, callback_data)

    @staticmethod
    def _build(labels:list[list[str]], data:list[list[str]]) -> list:
        
        try:
            inline_keyboard = []
            
            for i in range(len(labels)):
                tmp = []

                for j in range(len(labels[i])):
                    tmp.append(
                        {"text": str(labels[i][j]), "callback_data": str(data[i][j])})

                inline_keyboard.append(tmp)
            
            return inline_keyboard
        
        except Exception as e:
            raise TypeError(f"Invaild parameters types. Ensure that 1) list is 2D, 2) labels and data have the same shape. " + str(e))


