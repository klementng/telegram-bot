import requests
import functools

from requests.exceptions import HTTPError
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO

from utils.api.objects import InlineKeyboardMarkup
from utils.templates import render_response_template
from utils.general import round_datetime
from utils.api.replies import *


class Weather:
    hook = "/weather"
    description = "Singapore Weather"

    @classmethod
    def _inline_hook_reply(cls,chat_id,*args,**kwargs) -> list[MessageReply]:
        """return inline keyboard for /cls. Return [(method,response)]"""

        labels = [
            ["24 Hours Forecast"],
            ["4 Day Outlook"],
            ["Rainmap"],
            ["Help"]
        ]

        commands = [
            [f"{cls.hook} forecast24"],
            [f"{cls.hook} forecast4d"],
            [f"{cls.hook} rainmap"],
            [f"{cls.hook} help"],
        ]

        reply = MessageReply(
            chat_id,
            text=f"[{cls.hook}] Select an Option",
            reply_markup=InlineKeyboardMarkup(labels, commands)
        )

        return [reply]

    @classmethod
    def _inline_forecast24_reply(cls,chat_id, *args,**kwargs):
        labels = [
            ["North"],
            ["West", "Central", "East"],
            ["South"]
        ]

        commands = [
            [f"{cls.hook} forecast24 north"],
            [
                f"{cls.hook} forecast24 west",
                f"{cls.hook} forecast24 central",
                f"{cls.hook} forecast24 east"
            ],
            [f"{cls.hook} forecast24 south"]
        ]

        reponse = MessageReply(
            chat_id,
            text=f"[{cls.hook}] Select an Option",
            reply_markup=InlineKeyboardMarkup(labels, commands)
        )

        return [reponse]

    @staticmethod
    def _fetch_forecast24_api():
        api_response = requests.get(
            url='https://api.data.gov.sg/v1/environment/24-hour-weather-forecast')
        api_response.raise_for_status()

        return api_response.json()['items'][0]

    @staticmethod
    def _fetch_forecast4d_api():
        api_response = requests.get(
            url='https://api.data.gov.sg/v1/environment/4-day-weather-forecast')
        api_response.raise_for_status()

        return api_response.json()['items'][0]
    
    @staticmethod
    def _fetch_rainmap_api(dt:datetime = datetime.now()):
        
        @functools.cache
        def get_static_images():
            static_images_url = [
                "http://www.cls.gov.sg/wp-content/themes/wiptheme/assets/img/base-853.png",
                "http://www.cls.gov.sg/wp-content/themes/wiptheme/images/SG-Township.png",
            ]

            images = []
            
            for url in static_images_url:
                r = requests.get(url, stream=True)
                r.raise_for_status()
                
                r.raw.decode_content = True
                images.append(Image.open(r.raw))
            
            return tuple(images)

        max_it = 10
        @functools.lru_cache(10)
        def get_rain_overlay(time:datetime) -> tuple[datetime,Image.Image]:
            nonlocal max_it

            time = round_datetime(time,5) # round to nearest 5mins

            url = f"http://www.cls.gov.sg/files/rainarea/50km/v2/dpsri_70km_{time.strftime('%Y%m%d%H%M')}0000dBR.dpsri.png"
            r = requests.get(url, stream=True)
            
            if r.status_code == 200:
                r.raw.decode_content = True
                return time,Image.open(r.raw)
            
            elif max_it > 0:
                max_it = max_it - 1
                
                return get_rain_overlay(time - timedelta(minutes=5))

            else:
                #Max iterations
                r.status_code = 404 #Force HTTP error to raise
                r.raise_for_status()
                raise HTTPError

        @functools.lru_cache(5)
        def sitch_images(rainmap_time:datetime) -> tuple[datetime,bytes]:
            nonlocal static_images
            nonlocal overlay
            
            base = static_images[0].convert("RGBA")
            town = static_images[1].resize(base.size).convert("RGBA")
            overlay = overlay.resize(base.size).convert("RGBA")
            overlay.putalpha(70)
            base.paste(overlay, (0, 0), overlay)
            base.paste(town, (0, 0), town)
            
            photo = BytesIO()
            base.save(photo, 'PNG')
            photo.seek(0)

            return rainmap_time,photo.read()
        
        static_images = get_static_images()
        rainmap_time,overlay = get_rain_overlay(dt) #Snice the api is slow

        return sitch_images(rainmap_time)

    @classmethod
    def _weather_help_reply(cls,chat_id,*args,**kwargs):
        """Help response, return [('sendMessage', response_json)]"""
        assert args[1] == "help"
                                      
        text = render_response_template("weather/help.html")
        response = MessageReply(chat_id,text,parse_mode="HTML")
        
        return [response]

    @classmethod
    def _weather_forecast24_reply(cls,chat_id, *args,**kwargs):
        assert args[1] == "forecast24"

        if len(args) == 2:
            return cls._inline_forecast24_reply(chat_id)

        elif len(args) == 3:

            region = args[2]
            if region not in ["north", "south", "east", "west", "central"]:
                return [MessageReply(chat_id,f"Invalid Arguments '{args[2]}'")]

            try:
                weather_api = cls._fetch_forecast24_api()

                text = render_response_template(
                    "weather/forecast24.html",
                    title=f"24 Hour Forecast ({region})",
                    weather_api=weather_api,
                    region=region
                )

            except HTTPError as e:
                text = "API Error, Try Again Later"
        
        else:
            text = "Too many arugmenst"

        response = MessageReply(chat_id,text,parse_mode="HTML")

        return [response]                                       

    @classmethod
    def _weather_forecast4d_reply(cls,chat_id, *args,**kwargs):
        assert args[1] == "forecast4d"

        try:
            weather_api = cls._fetch_forecast4d_api()                                        
            text = render_response_template(                                       
                "weather/forecast4d.html",
                title=f"4 Day Outlook",
                weather_api=weather_api,
            )

        except HTTPError as e:
            text = "API Error, Try Again Later"

        response = MessageReply(chat_id,text,parse_mode="HTML")
        return [response]

    @classmethod
    def _weather_rainmap_reply(cls,chat_id, *args,**kwargs):
        
        assert args[1] == "rainmap"

        time = round_datetime(datetime.now() - timedelta(minutes=5),5)

        try:
            rainmap_time,photo  = cls._fetch_rainmap_api(time)
            response = PhotoReply(
                chat_id,
                photo,
                caption=f"Updated: {str(rainmap_time)}"
            )

        except HTTPError as e:
            response = MessageReply(chat_id,"API Error Occured")

        return [response]

    @classmethod
    def get_reply(cls,*args,**kwargs):
        """
        Get replies for commands:

        Args:
            *args: parsed user inputs
            
            **chat_id: chat where the input is sent
        
        """
        assert (args[0] == cls.hook)
        
        try:
            chat_id = int(kwargs["chat_id"])
        except ValueError:
            raise ValueError("Chat id must be a int")
        except KeyError:
            raise ValueError("Missing kwargs:chat_id ")
        
        
        if len(args) == 1:
            return cls._inline_hook_reply(chat_id)

        elif len(args) >= 2:
            try:
                return getattr(Weather, '_weather_%s_reply' % args[1])(chat_id, *args,**kwargs)

            except AttributeError:
                return [MessageReply(chat_id,f"Invaild arguments: {args[1:]} ")]