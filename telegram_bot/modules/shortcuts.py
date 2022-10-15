import json
import sqlite3
import core.database as db
from typing import Iterable
from utils.api.methods import TelegramMethods, SendMessage
from utils.api.objects import InlineKeyboardMarkup
from utils.server.users import UserState
from utils.templates import render_response_template


class Shortcuts:
    """
    Module that handles a commands received from user.

    This modules allow the user to saved favourite. Does not need be instantiated

    Class Attributes:
        hook: tigger modules activation [default: "/shortcuts"]
        description: modules description
    """

    hook = "/shortcuts"
    description = "set custom shortcuts / message to send to bot"

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

    @classmethod
    def _db_get(cls, user_id: int) -> list[dict]:
        """
        Query database for saved command list. 

        Returns:
            list of key:value pair

        Raises:
            sqlite3.Error: Database error
        """
        query = db.execute(
            "SELECT command_list FROM shortcuts WHERE user_id = ?", (user_id,))

        return json.loads(query[0][0]) if (query != []) else []

    @classmethod
    def _db_add(cls, user_id: int, name: str, command: str) -> str:
        """
        Adds a new shortcuts. 

        Returns: 
            A message

        Raises: 
            sqlite3.Error: Database error
        """

        command_list = cls._db_get(user_id)
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
                "user_id": user_id,
                "command_list": json.dumps(command_list)
            }
        )

        return f'Added!'

    @classmethod
    def _db_delete(cls, user_id: int, indexes: Iterable[int]) -> str:
        """
        Delete a shortcuts. 

        Returns: 
            A message

        Raises: 
            sqlite3.Error: Database error
            IndexError: Invaild Indexes
        """

        msg = ""

        command_list = cls._db_get(user_id)
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
            "user_id": user_id,
            "command_list": json.dumps(list(command_list))
        })

        return msg

    @classmethod
    def _db_edit(cls, user_id: int, index: int, name: str, command: str) -> str:
        """
        Edit a saved shortcut. 

        Returns: 
            A message

        Raises: 
            sqlite3.Error: Database error
            IndexError: Invaild index
        """

        command_list = cls._db_get(user_id)
        if command_list == []:
            return "There is no commands to edit"

        command_list[index] = {name: command}

        sql = """ 
            UPDATE shortcuts SET command_list = :command_list
            WHERE user_id = :user_id;
            """

        db.execute_and_commit(sql, {
            "user_id": user_id,
            "command_list": json.dumps(list(command_list))
        })

        return "Succeeded!"

    @classmethod
    def _shortcuts_modify_reply(cls, user_id: int, chat_id: int, *args) -> list[TelegramMethods]:
        """Modify the shortcuts list"""

        assert (args[1] == "modify")
        user_state = UserState(user_id, chat_id)

        # Returns InlineKeyboard hints
        if len(args) == 2:
            replies = []

            msg = render_response_template(
                "shortcuts/modfiy.html", hook=cls.hook
            )

            replies.extend(
                cls._shortcuts_show_reply(user_id, chat_id, show_full=True)
            )
            replies.append(SendMessage(chat_id, msg, parse_mode="HTML"))

            # Set listen for additional arg state to be true
            user_state.update_state(" ".join(args[0:2]), True)
            
            return replies

        # Check if enough arguments
        elif len(args) < 4:
            user_state.update_state(" ".join(args[0:2]), True)
            return [SendMessage(chat_id, f"[{cls.hook} modify] Error: Not enough arguments")]

        msg = f"[{cls.hook} modify] "
        action = args[2]

        try:
            if action == "add" and len(args) == 5:
                name = args[3]
                command = args[4]
                msg += cls._db_add(user_id, name, command)

            elif action == "delete":
                indexes = list(map(int, args[3:]))
                msg += cls._db_delete(user_id, indexes)

            elif action == "edit" and len(args) == 6:
                index = int(args[3])
                name = args[4]
                command = args[5]
                msg += cls._db_edit(user_id, index, name, command)

            else:
                raise ValueError("too many / not enough / invalid args ")
            
            user_state.update_state(" ".join(args[0:2]), False)
            return [SendMessage(chat_id, msg, reply_markup=cls._inline_hook_markup())]

        except Exception as e:
            # Allow user to retry
            user_state.update_state(" ".join(args[0:2]), True)

            if isinstance(e, (ValueError, IndexError)):
                msg += "Invaild arguments, please try again:"
            elif isinstance(e, sqlite3.Error):
                msg += "Database error occured, please try again:"
            else:
                msg += "Unexpected error has occured, please try again:"

            msg += f"\n\nMore Infomation: \n {e}"

            return [SendMessage(chat_id, msg)]

    @classmethod
    def _shortcuts_show_reply(cls, user_id, chat_id, *args, show_full=False) -> list[TelegramMethods]:
        """Query database and replies with a message with InlineMarkup"""

        try:
            command_list = cls._db_get(user_id)

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

                return [
                    SendMessage(
                        chat_id,
                        f"[{cls.hook}] Saved Commands:",
                        reply_markup=InlineKeyboardMarkup(labels, callback_data))
                ]

            else:
                return [SendMessage(chat_id, f"[{cls.hook} show] Your shortcut list is empty")]

        except sqlite3.Error:
            return [SendMessage(chat_id, f"[{cls.hook} show] An database error occured, try again")]

    @classmethod
    def _shortcuts_help_reply(cls, user_id, chat_id, *args) -> list[TelegramMethods]:
        """Render and send the help response"""

        assert (args[1] == "help")
        msg = render_response_template("shortcuts/help.html", hook=cls.hook)

        return [SendMessage(chat_id, msg, parse_mode="HTML")]

    @classmethod
    def get_reply(cls, *args, **kwargs):
        """
        Get replies for commands:

        Args:
            *args: parsed user inputs

            **chat_id: chat id
            **user_id: user id

        Returns:
            list of callable replies objects

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

        if len(args) == 1:
            return [
                SendMessage(
                    chat_id,
                    f"[{cls.hook}] Select an Option",
                    reply_markup=cls._inline_hook_markup()
                )]

        elif len(args) >= 2:
            try:
                return getattr(cls, '_shortcuts_%s_reply' % args[1])(user_id, chat_id, *args)

            except AttributeError:
                return [SendMessage(chat_id, f"[{cls.hook}] Invaild arguments")]
