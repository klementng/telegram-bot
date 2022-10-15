from core import database as db


class UserSession:

    def __init__(self, user_id, chat_id) -> None:
        self.user_id = user_id
        self.chat_id = chat_id
        self.require_follow_up = None
        self.last_command = None

    def _run_query(self):
        query = db.execute("SELECT last_command,require_follow_up FROM usercommandstate WHERE user_id = :user_id AND chat_id = :chat_id", {
                           "user_id": self.user_id, "chat_id": self.chat_id})

        if query != []:
            self.last_command, self.require_follow_up = query[0]
        else:
            self.require_follow_up = False
            self.last_command = ""

    def is_addl_args_required(self):
        if self.require_follow_up == None:
            self._run_query()

        return self.require_follow_up

    def get_last_executed_command(self):
        if self.require_follow_up == None:
            self._run_query()

        if self.last_command != None:
            return self.last_command
        else:
            return ""

    def update_state(self, command, require_follow_up):
        db.execute_and_commit(
            """
            INSERT INTO usercommandstate 
            VALUES(:user_id,:chat_id,:last_command,:require_follow_up) 
            ON CONFLICT(user_id,chat_id) 
            DO UPDATE SET 
            last_command=:last_command,
            require_follow_up=:require_follow_up 
            WHERE 
            user_id = :user_id and chat_id = :chat_id
            """,
            {
                "user_id": self.user_id,
                "chat_id": self.chat_id,
                "last_command": str(command).strip(),
                "require_follow_up": require_follow_up
            }
        )
