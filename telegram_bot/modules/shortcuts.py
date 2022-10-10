import json
import sqlite3
import numpy as np
import core.database as database
from utils.api.replies import MessageReply
from utils.api.objects import InlineKeyboardMarkup
from utils.server.users import UserCommandState
from utils.templates import render_response_template


class Shortcuts:
    hook = "/shortcuts"
    description = "set custom shortcuts / message to send to bot"
    @staticmethod
    def _inline_hook_markup():
        """return inline keyboard for /weather. Return [(method,response)]"""

        labels = [
            ["Modify", "Show"]
        ]

        commands = [
            [f"{Shortcuts.hook} modify",
                f"{Shortcuts.hook} show"]
        ]

        return InlineKeyboardMarkup(labels, commands)

    @staticmethod
    def _db_get(user_id):
        query = database.execute(
            "SELECT command_list FROM shortcuts WHERE user_id = ?", (user_id,))

        return json.loads(query[0][0]) if (query != []) else None

    @staticmethod
    def _db_add(user_id, name, command):
        try:
            command_list = Shortcuts._db_get(user_id)
            command_list = command_list if command_list != None else []
            command_list.append({name: command})

            database.execute_and_commit(
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

        except sqlite3.Error as e:
            return "Failed (Database Error): " + e

        return f'Added!'

    @staticmethod
    def _db_delete(user_id, indexes):
        msg = ""

        try:
            command_list = Shortcuts._db_get(user_id)
            if command_list == None:
                return "Failed: there is no commands to remove"

            command_list = np.array(command_list, dtype=dict)
            indexes = np.array(indexes, dtype=np.int32)
            command_list = np.delete(command_list, indexes)

            if len(command_list) == 0:
                msg += f"Success: The list is now empty."
                sql = "DELETE from shortcuts WHERE user_id = :user_id;"

            else:
                msg += f"Succeeded!"
                sql = """
                    UPDATE shortcuts SET command_list = :command_list
                    WHERE user_id = :user_id;
                    """

            database.execute_and_commit(sql, {
                "user_id": user_id,
                "command_list": json.dumps(list(command_list))
            })

            return msg

        except IndexError as e:
            return "Failed (Index Error) (check your arguments!!)\n\n" + str(e)
        except ValueError as e:
            return "Failed (Index Error) (check your arguments!!)\n\n" + str(e)
        except sqlite3.Error as e:
            return "Failed (Database Error)\n\n" + str(e)

    @staticmethod
    def _db_edit(user_id, index,name,command):
        try:
            command_list = Shortcuts._db_get(user_id)
            if command_list == None:
                return "Failed: there is no commands to remove"

            command_list[int(index)] = {name:command}

            sql = """ 
                UPDATE shortcuts SET command_list = :command_list
                WHERE user_id = :user_id;
                """

            database.execute_and_commit(sql, {
                "user_id": user_id,
                "command_list": json.dumps(list(command_list))
            })

            return "Succeeded!"

        except IndexError as e:
            return "Failed (Index Error) (check your arguments!!)\n\n" + str(e)
        except ValueError as e:
            return "Failed (Index Error) (check your arguments!!)\n\n" + str(e)
        except sqlite3.Error as e:
            return "Failed (Database Error)\n\n" + str(e)

    @staticmethod
    def _shortcuts_modify_reply(user_id, chat_id, *args):
        assert (args[1] == "modify")
        user_state = UserCommandState(user_id,chat_id)

        if len(args) == 2:          
            replies = []
            msg = render_response_template("shortcuts/modfiy.html",hook=Shortcuts.hook)
            replies.extend(Shortcuts._shortcuts_show_reply(user_id, chat_id,show_full=True))
            replies.append(MessageReply(chat_id, msg, parse_mode="HTML"))

            #set listen for additional arg state to be true
            user_state.update_state(" ".join(args[0:2]),True)
            return replies
        
        elif len(args) < 4:
            user_state.update_state(" ".join(args[0:2]),True)
            return [MessageReply(chat_id, f"[{Shortcuts.hook} modify] Error: Not enough arguments")]

        msg = f"[{Shortcuts.hook} modify] "

        action = args[2]
        if action == "add" and len(args) == 5:
            name = args[3]
            command = args[4]
            msg += Shortcuts._db_add(user_id, name, command)
            
        elif action == "delete":
            indexes = args[3:]
            msg += Shortcuts._db_delete(user_id, indexes)
        
        elif action == "edit" and len(args) == 6:
            index = args[3]
            name = args[4]
            command = args[5]
            msg += Shortcuts._db_edit(user_id, index,name,command)

        else:
            msg += f"too many/less/invaild arguments, try again"
            user_state.update_state(" ".join(args[0:2]),True)
            return [MessageReply(chat_id, msg)]

        user_state.update_state(" ".join(args[0:2]),False)
        return [MessageReply(chat_id, msg, reply_markup=Shortcuts._inline_hook_markup())]

    @staticmethod
    def _shortcuts_show_reply(user_id, chat_id, *args,show_full=False):
        command_list = Shortcuts._db_get(user_id)

        if command_list != None:

            labels = []
            callback_data = []

            for i, command in enumerate(command_list):
                for name, data in command.items():
                    
                    if show_full == True:
                        labels.append([f"{i}. " + name + f"  [{str(data)}]"])
                    else:
                        labels.append([f"{i}. " + name])
                    
                    callback_data.append([data])

            return [
                MessageReply(
                chat_id,
                f"[{Shortcuts.hook}] Saved Commands:",
                reply_markup=InlineKeyboardMarkup(labels, callback_data))
            ]

        else:
            return [MessageReply(chat_id, f"[{Shortcuts.hook} show] Your shortcut list is empty")]

    def _shortcuts_help_reply(user_id, chat_id, *args):
        assert (args[1] == "help")
        msg = render_response_template("shortcuts/help.html",hook=Shortcuts.hook)

        return [MessageReply(chat_id, msg, parse_mode="HTML")]

    @staticmethod
    def get_reply(*args, chat_id=None, user_id=None):
        assert (args[0] == Shortcuts.hook)

        if len(args) == 1:
            return [
                MessageReply(
                    chat_id,
                    f"[{Shortcuts.hook}] Select an Option",
                    reply_markup=Shortcuts._inline_hook_markup()
                )]

        elif len(args) >= 2:
            try:
                return getattr(Shortcuts, '_shortcuts_%s_reply' % args[1])(user_id, chat_id, *args)

            except AttributeError:
                return [MessageReply(chat_id, f"[{Shortcuts.hook}] Invaild arguments")]
