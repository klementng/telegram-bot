import json
import sqlite3
import core.database as db
from typing import Iterable
from utils.api.methods import TelegramMethods, SendMessage
from utils.api.objects import InlineKeyboardMarkup
from utils.server.session import UserSession
from utils.templates import render_response_template


class Shortcuts:
    """
    Module that handles a commands received from user.

    This modules allow the user to saved favourite. Does not need be instantiated

    Class Attributes:
        hook: tigger modules activation [default: "/shortcuts"]
        description: modules description

    Instance Attributes:
        chat_id: id of telegram chat
        user_id: id of telegram user
        session: UserSession Object

    """

    hook = "/shortcuts"
    description = "Set custom messages / commands"

    def __init__(self, chat_id: int, user_id: int) -> None:

        try:
            self.chat_id = int(chat_id)
            self.user_id = int(user_id)
            self.session = UserSession(user_id, chat_id)

        except ValueError:
            raise ValueError("Invaild type for chat_id or user_id")
        except:
            raise ValueError("Missing keyword arguments")

    def __call__(self, *args):

        if len(args) == 1:
            return [
                SendMessage(
                    self.chat_id,
                    f"[{self.hook}] Select an Option",
                    reply_markup=self._inline_hook_markup()
                )]

        elif len(args) >= 2:
            try:
                return getattr(self, '_shortcuts_%s_reply' % args[1])(args)

            except AttributeError:
                return self._exception_reply(args[0:1], f"Unexpected arguement: '{args[1]}'")

    @classmethod
    def _inline_hook_markup(cls) -> InlineKeyboardMarkup:
        """Build inline keyboard markup"""

        labels = [
            ["Modify", "Show"]
        ]

        commands = [
            [f"{cls.hook} modify", f"{cls.hook} show"]
        ]

        return InlineKeyboardMarkup(labels, commands)

    def _db_get(self) -> list[dict]:
        """
        Query database for saved command list. 

        Returns:
            list of key:value pair

        Raises:
            sqlite3.Error: Database error
        """
        query = db.execute(
            "SELECT command_list FROM shortcuts WHERE user_id = ?", (self.user_id,))

        return json.loads(query[0][0]) if (query != []) else []

    def _db_add(self, name: str, command: str) -> str:
        """
        Adds a new shortcuts. 

        Returns: 
            A message

        Raises: 
            sqlite3.Error: Database error
        """

        command_list = self._db_get()
        command_list.append({name: command})

        db.execute_and_commit(
            """
            INSERT INTO shortcuts 
            VALUES(:user_id,:command_list) 
            ON CONFLICT(user_id) 
            DO UPDATE SET command_list=:command_list 
            WHERE user_id = :user_id
            """,
            {
                "user_id": self.user_id,
                "command_list": json.dumps(command_list)
            }
        )

        return f'Added!'

    def _db_delete(self, indexes: Iterable[int]) -> str:
        """
        Delete a shortcuts. 

        Returns: 
            A message

        Raises: 
            sqlite3.Error: Database error
            IndexError: Invaild Indexes
        """

        msg = ""

        command_list = self._db_get()
        if command_list == None:
            return "Failed: there is no commands to remove"

        # TODO: Check for invaild indexes
        command_list = [i for j, i in enumerate(
            command_list) if j not in indexes]

        if len(command_list) == 0:
            msg += f"Success: The list is now empty."
            sql = "DELETE from shortcuts WHERE user_id = :user_id;"

        else:
            msg += f"Succeeded!"
            sql = """
                UPDATE shortcuts SET command_list = :command_list
                WHERE user_id = :user_id;
                """

        db.execute_and_commit(sql, {
            "user_id": self.user_id,
            "command_list": json.dumps(list(command_list))
        })

        return msg

    def _db_edit(self, index: int, name: str, command: str) -> str:
        """
        Edit a saved shortcut. 

        Returns: 
            A message

        Raises: 
            sqlite3.Error: Database error
            IndexError: Invaild index
        """

        command_list = self._db_get()
        if command_list == []:
            return "There is no commands to edit"

        command_list[index] = {name: command}

        sql = """ 
            UPDATE shortcuts SET command_list = :command_list
            WHERE user_id = :user_id;
            """

        db.execute_and_commit(sql, {
            "user_id": self.user_id,
            "command_list": json.dumps(list(command_list))
        })

        return "Succeeded!"

    def _exception_reply(self, args: tuple, msg: str, additional_info=None, listen_for_additional_args=None, **kwargs_send_message) -> list[TelegramMethods]:

        commands = " ".join(args)
        text = f"[{commands}] ERROR: {msg}"

        if additional_info is not None:
            text += f"\n\nMore Infomation: {additional_info}"

        if listen_for_additional_args is not None:
            self.session.update_state(commands, listen_for_additional_args)

        return [SendMessage(self.chat_id, text, **kwargs_send_message)]

    def _simple_reply(self, args: tuple, msg: str, listen_for_additional_args=None, **kwargs_send_message) -> list[TelegramMethods]:
        commands = " ".join(args)
        text = f"[{commands}] {msg}"

        if listen_for_additional_args is not None:
            self.session.update_state(commands, listen_for_additional_args)

        return [SendMessage(self.chat_id, text, **kwargs_send_message)]

    def _shortcuts_modify_reply(self, args: tuple) -> list[TelegramMethods]:
        """Modify the shortcuts list"""

        assert (args[1] == "modify")
        argc = len(args)

        # Returns InlineKeyboard hints
        if argc == 2:
            replies = []

            replies.extend(
                # Render list of saved shortcuts
                self._shortcuts_show_reply(args, show_full=True)
            )

            msg = render_response_template(
                "shortcuts/modfiy.html", hook=self.hook
            )
            replies.append(SendMessage(self.chat_id, msg, parse_mode="HTML"))

            # Set listen for additional arg state to be true
            self.session.update_state(" ".join(args[0:2]), True)
            return replies

        # Check if enough arguments
        elif argc < 4:
            self.session.update_state(" ".join(args[0:2]), True)
            return self._exception_reply(args[0:2], f"Not enough arguments, expected > 3, got {argc}")

        action = args[2]

        try:
            if action == "add" and argc == 5:
                msg = self._db_add(args[3], args[4])  # DBError

            elif action == "delete" and argc >= 4:
                indexes = tuple(map(int, args[3:]))  # ValueError
                msg = self._db_delete(indexes)  # IndexError,DBError

            elif action == "edit" and argc == 6:
                index = int(args[3]) 
                msg = self._db_edit(index, args[4], args[5]) 

            elif action in ["add", "delete", "edit"]:

                return self._exception_reply(
                    args[0:2],
                    f'Too many/few args.',
                    additional_info=f'Expected 5 for "add", >= 4 for "delete", 6 for "edit". Got {argc}',
                    listen_for_additional_args=True
                )
            else:
                return self._exception_reply(
                    args[0:2],
                    f'Unexpected Arguments: "{action}"',
                    listen_for_additional_args=True
                )

            return self._simple_reply(args[0:2], msg, False, reply_markup=self._inline_hook_markup())

        except sqlite3.Error as e:
            return self._exception_reply(args[0:2], f"A Database Error has occured:", additional_info=str(e), listen_for_additional_args=True)

        except ValueError as e:
            return self._exception_reply(args[0:2], f"Illegal arguments type", additional_info=str(e), listen_for_additional_args=True)

        except IndexError as e:
            return self._exception_reply(args[0:2], f"Index given not in saved list", additional_info=str(e), listen_for_additional_args=True)

    def _shortcuts_show_reply(self, args, show_full=False) -> list[TelegramMethods]:
        """Query database and replies with a message with InlineMarkup"""

        assert (args[1] == "show" or args[1] == "modify")

        try:
            command_list = self._db_get()

            if command_list != []:

                labels = []
                callback_data = []

                for i, command in enumerate(command_list):
                    for name, data in command.items():

                        if show_full == True:
                            labels.append(
                                [f"{i}. " + name + f"  [{str(data)}]"])
                        else:
                            labels.append([f"{i}. " + name])

                        callback_data.append([data])

                return self._simple_reply(args, "Saved shortcuts:", reply_markup=InlineKeyboardMarkup(labels, callback_data))

            else:
                return self._simple_reply(args[0:2], "Your shortcuts list is empty")

        except sqlite3.Error as e:
            return self._exception_reply(args[0:2], "A database error occured", additional_info=str(e), listen_for_additional_args=True)

    def _shortcuts_help_reply(self, args) -> list[TelegramMethods]:
        """Render and send the help response"""

        assert (args[1] == "help")
        msg = render_response_template("shortcuts/help.html", hook=self.hook)

        return [SendMessage(self.chat_id, msg, parse_mode="HTML")]

    @classmethod
    def get_reply(cls, *args, **kwargs):
        """
        Get replies for commands.

        Instantiate an shortcuts object and call it

        Args:
            *args: parsed user inputs

            **chat_id: chat id
            **user_id: user id

        Returns:
            list of TelegramMethod objects

        Rasies:
            ValueError: Missing kwargs / Invaild type

        """

        assert (args[0] == cls.hook)

        try:
            chat_id = int(kwargs["chat_id"])
            user_id = int(kwargs["user_id"])

        except ValueError:
            raise ValueError("Invaild type for chat_id or user_id")
        except:
            raise ValueError("Missing keyword arguments")

        return Shortcuts(chat_id, user_id)(*args)


class sc:
    hook = "/sc"
    description = "Show saved shortcuts"

    @staticmethod
    def get_reply(*args,**kwargs):
        return Shortcuts.get_reply(*(Shortcuts.hook,"show",),**kwargs)
