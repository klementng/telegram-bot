import shlex
import socketserver
import ssl
import json
import requests
from http.server import SimpleHTTPRequestHandler
from utils.api.methods import SendMessage
from utils.api.objects import *
from utils.exceptions import NotSupported
from utils.server.users import UserCommandState
import utils.templates

CONFIG = {}
MODULES = {}

def run_command_from_modules(*args, **kwargs):
    """
    Get replies from modules and send it

    Args:
        *args: Commands arguments to pass to modules
            -> *args =  ["/weather","forecast24"]

        **kwargs: Keyword arguments required for modules
            -> **kwargs = {"chat_id":...,"user_id":...} 

    Returns:
        None

    Raises:
        NotSupported: The hook (args[0]) does not match any modules 
        requests.HTTPError: An error occured posting to telegram servers

        See also: Respective errors raised by modules:
            -> NotSupported: Invaild Arguments

    """

    module = MODULES.get(args[0])
    if module == None:
        raise NotSupported

    for action in module.get_reply(*args, **kwargs):
        action(CONFIG["BOT_TOKEN"], raise_errors=True)

    return


def parse_incoming_res(res_type: str, response: str):
    """
    Parse supported objects 

    Args:
        res_type: Name of object received
            -> see https://core.telegram.org/bots/api/#update

        response: dict/json of object

    Returns:
        None

    Raises:
        ValueError: Failed Decode of json/dict
    """

    user_id, chat_id, data = None, None, None

    if "callback_query" == res_type:
        cbq = CallbackQuery.decode(response)
        cbq.answer(CONFIG["BOT_TOKEN"])

        chat_id = cbq.get_chat_id()
        user_id = cbq.get_user_id()
        data = cbq.data

    elif "message" == res_type:
        msg = Message.decode(response)
        user_id = msg.get_user_id()
        chat_id = msg.get_chat_id()
        data = msg.get_content()

    return user_id, chat_id, data


def handle_text_data(user_id, chat_id, text):
    """
    Parse text for commands  

    Args:
        user_id: user id of sender
        chat_id: chat id of sender
        text: commands to parse

    Returns:
        None

    Raises:
        NotSupported: Unregonized commands
        ValueError: Invaild Parsing

        From run_command_from_modules():
            NotSupported: The hook (args[0]) does not match any modules 
            requests.HTTPError: An error occured posting to telegram servers

            See also: Respective errors raised by modules:
                -> NotSupported: Invaild Arguments

    """

    text = text.lower().strip()

    args = shlex.split(text)
    usr_state = UserCommandState(user_id, chat_id)

    # Handle Commands
    if text.startswith("/"):
        usr_state.update_state(text, False)
        run_command_from_modules(*args, chat_id=chat_id, user_id=user_id)

    # Look if server is listening for additional args
    elif usr_state.is_awaiting_user_reply() == True:

        last_command = usr_state.get_last_command()
        text = last_command + " " + text

        args = shlex.split(text)
        run_command_from_modules(*args, chat_id=chat_id, user_id=user_id)

    else:
        if text in ['hello', 'hi']:
            SendMessage(chat_id, "Beep Boop").post(CONFIG["BOT_TOKEN"])

        else:
            raise NotSupported


class RequestHandler(SimpleHTTPRequestHandler):

    def do_POST(self):

        try:
            received = json.loads(
                self.rfile.read(
                    int(self.headers['Content-Length'])))
            update_id = received.pop("update_id")
            obj_type = list(received.keys())[0]

            received = received[obj_type]

            self.send_response(200)
            self.end_headers()

        except Exception as e:
            self.send_response(400, str(e))
            self.end_headers()
            return

        user_id, chat_id, data = None,None,None
        try:
            user_id, chat_id, data = parse_incoming_res(obj_type, received)

            if chat_id == None:
                raise NotSupportedNoChatID

            if type(data) == str:
                handle_text_data(user_id, chat_id, data)

            elif type(data) == Location:
                raise NotSupported("location data is not supported")
            else:
                raise NotSupported

        except NotSupported as e:
            SendMessage(chat_id, str(e))(CONFIG["BOT_TOKEN"])  # type: ignore

        except NotSupportedNoChatID as e:
            return  # no response is sent to user

        except Exception as e:
            SendMessage(chat_id, "Unexpected error has occured: %s" %  # type: ignore
                         e)(CONFIG["BOT_TOKEN"])

    def do_GET(self):
        self.send_response(200)
        self.end_headers()


def setup(config_path, modules):
    """
    Connect to database using a config file

    Args:
        config_path: path to a JSON config file 
    
    Returns:
        None

    Raises:
        IOError: Config file cannot be read
        json.JSONDecodeError: Invaild JSON
        KeyError: The keys: ["server"] does not exist
        request.HTTPError: API error when setting up certs
    """
    
    
    global CONFIG
    global MODULES

    with open(config_path) as f:
        CONFIG = json.load(f)["server"]

    MODULES = {m.hook: m for m in modules}

    with open(CONFIG["CERT_PATH"]) as cert:
        url = f'https://api.telegram.org/bot{CONFIG["BOT_TOKEN"]}/setWebhook?url={CONFIG["HOSTNAME"]}:{CONFIG["PORT"]}'
        requests.post(url, files={'certificate': cert}).raise_for_status()

    url = f'https://api.telegram.org/bot{CONFIG["BOT_TOKEN"]}/setMyCommands'

    commands_list = [{"command": m.hook.replace(
        "/", ""), "description": m.description} for m in modules]
    requests.post(url, params={"commands": json.dumps(commands_list)}).raise_for_status()


def run():
    """Starts the server"""

    handler = RequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer((CONFIG["HOST"], CONFIG["PORT"]), handler)

    server.socket = ssl.wrap_socket(
        server.socket,
        ca_certs=CONFIG["CA_CERT_PATH"],
        certfile=CONFIG["CERT_PATH"],
        keyfile=CONFIG["KEY_PATH"],
        server_side=True
    )

    # TODO Add threading
    server.serve_forever()
