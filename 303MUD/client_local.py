###
## Do not modify this file.
###

import os
import sys
import json
import time
import signal
import traceback
import threading
from abc import ABC
from enum import Enum
from pathlib import Path
from collections import defaultdict
from queue import Queue, PriorityQueue
from typing import Any, Literal, NoReturn, Union, cast, Callable

try:
    import tkinter as tk
    from tkinter import NORMAL, font, ttk
except:
    print("You must install python-tk witn your package manager.")

try:
    import requests
    from pygame import mixer; mixer.init() # must install pygame
    from PIL.ImageFont import FreeTypeFont
    from PIL import Image, ImageTk, ImageFont, ImageDraw # must install Pillow
except:
    raise Exception("You must pip3 install requests websocket-client pygame Pillow")

from .FestSoundCombiner import render as fsc_render
from .util import shorten_lines
from .resources import get_resource_path

TILE_SIZE = 32
NUM_ROWS, NUM_COLS = 15, 15

GRID_HEIGHT = 15 * TILE_SIZE
GRID_WIDTH = 15 * TILE_SIZE

class ResourceType(Enum):
    IMAGE = 'image'
    FONT = 'font'
    SOUND = 'sound'

    @property
    def extension(self) -> str:
        extensions: dict[ResourceType, str] = {
            ResourceType.IMAGE: 'png',
            ResourceType.FONT: 'ttf',
            ResourceType.SOUND: 'mp3',
        }
        return extensions[self]

class ResourceManager:
    """ A class to manage resources such as images, fonts, and sounds. """
    _cache: dict = {}

    def __init__(self):
        self.__load_cache()

    def __load_resource(self, resource_type: ResourceType, file_path: Path) -> Union[ImageTk.PhotoImage, ImageFont.FreeTypeFont, Path]:
        """ Load a resource from disk and return a usable object. """
        if resource_type == ResourceType.IMAGE:
            original_image = Image.open(file_path)
            new_size: tuple[int, int] = (original_image.width * 2, original_image.height * 2)
            resized_image = original_image.resize(new_size, Image.Resampling.NEAREST)  # Use NEAREST for pixel art
            return ImageTk.PhotoImage(resized_image)
        elif resource_type == ResourceType.FONT:
            return ImageFont.truetype(font=str(file_path), size=20)
        elif resource_type == ResourceType.SOUND:
            return file_path

    def __load_cache(self) -> None:
        """ Load all resources from the resources folder into the cache. """
        for rsrc_type in ResourceType:
            ResourceManager._cache[rsrc_type] = {}

            folder_path = Path(f'rsrc_cache/{rsrc_type.name.lower()}')
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                return
            
            resource_dir = Path("rsrc_cache") / rsrc_type.value
            print(resource_dir)
            for file_path in resource_dir.rglob("*"):
                if file_path.is_dir():
                    continue
                relative_path = file_path.relative_to(resource_dir).with_suffix("")
                #print("Loading from cache", relative_path)
                if file_path.stem.startswith('.'):
                    continue
                rsrc = self.__load_resource(rsrc_type, file_path)
                ResourceManager._cache[rsrc_type][str(relative_path)] = rsrc
                ResourceManager._cache[rsrc_type][str(file_path.relative_to(resource_dir))] = rsrc

    def _get_resource_from_source(self, resource_type: ResourceType, name: str) -> bytes:
        fname = name
        if '.' not in fname:
            fname += '.' + resource_type.extension
        data = open(get_resource_path(f'{resource_type.name.lower()}/{fname}'), 'rb').read()
        return data

    def __get_resource(self, resource_type: ResourceType, name: str) -> Any:
        """ Get a resource from the cache or load it from disk if it doesn't exist. """

        if resource_type in ResourceManager._cache and name in ResourceManager._cache[resource_type]:
            return ResourceManager._cache[resource_type][name]
        
        # get image from folder
        data = self._get_resource_from_source(resource_type, name)

        # save to disk
        fname = name
        if '.' not in fname:
            fname += '.' + resource_type.extension

        file_path = Path(f'rsrc_cache/{resource_type.name.lower()}/{fname}')
        print("Saving to cache", file_path)
        dirname = os.path.dirname(file_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(file_path, 'wb') as f:
            f.write(data)

        # load into cache
        if resource_type not in ResourceManager._cache:
            ResourceManager._cache[resource_type] = {}
        ResourceManager._cache[resource_type][name] = self.__load_resource(resource_type, file_path)

        print("New resource name:", name)
        return ResourceManager._cache[resource_type][name]

    def get_image(self, name: str) -> ImageTk.PhotoImage:
        """ Get an image resource by name. """
        return self.__get_resource(ResourceType.IMAGE, name)
    
    def get_pil_image(self, name: str) -> Image.Image:
        """Get a raw PIL image by name (no resizing or conversion to PhotoImage)."""
        # Construct full path to cached image file
        fname = name
        if '.' not in fname:
            fname += '.' + ResourceType.IMAGE.extension

        file_path = Path(f'rsrc_cache/{ResourceType.IMAGE.name.lower()}/{fname}')

        # Check if the file exists
        if not file_path.exists():
            # Attempt to retrieve and cache it
            data = self._get_resource_from_source(ResourceType.IMAGE, name)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(data)

        # Load and return the image
        return Image.open(file_path).convert("RGBA")


    def get_sound(self, name: str) -> Path:
        """ Get a sound resource by name. """
        return self.__get_resource(ResourceType.SOUND, name)
    
    def get_font(self, name: str) -> ImageFont.FreeTypeFont:
        """ Get a font resource by name. """
        return self.__get_resource(ResourceType.FONT, name)

    def render_font(self, font: ImageFont.FreeTypeFont, text: str, type_ : str = "normal", bg_color: tuple = (255, 255, 255), text_color: tuple = (0, 0, 0)) -> Image.Image:
        """
        Render multi-line text into an image with a transparent background.

        Parameters:
        - font_path: Path to the TrueType font file.
        - text: The text string to render, can include multiple lines separated by '\n'.
        - type_: Type of rendering, "normal" or "bold".

        Returns:
        - A PIL Image object with the rendered text.
        """
        
        # Split text into lines
        lines = text.split('\n') if text else ['']
        
        # Get font metrics
        ascent, descent = font.getmetrics()
        # Define line spacing (adjust as needed)
        line_spacing = 4  # pixels

        # Calculate width and height
        max_width = 0
        for line in lines:
            # Use getbbox for accurate measurement
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            if line_width > max_width:
                max_width = line_width

        # Calculate line height based on font metrics
        line_height = ascent + descent + line_spacing
        total_height = line_height * len(lines)

        # Create a transparent image
        image = Image.new(mode='RGB', size=(max_width, total_height), color=(*bg_color, 0))
        draw = ImageDraw.Draw(image)

        # Render each line
        for idx, line in enumerate(lines):
            y_position = idx * line_height
            if type_ == "normal":
                draw.text((0, y_position), line, font=font, fill=text_color)
            elif type_ == "bold":
                # Simulate bold by adding a stroke
                draw.text((0, y_position), line, font=font, fill=text_color, stroke_width=1, stroke_fill='black')
            else:
                raise ValueError("Unsupported type_ value. Use 'normal' or 'bold'.")

        return image

class AudioPlayer:
    """ A class to manage audio playback. """
    current_sound: Path = Path("")
    current_sound_playing: bool = False

    @staticmethod
    def set_sound(file_path: Path) -> None:
        """ Set the sound file to be played. """
        if file_path != AudioPlayer.current_sound:
            print("Loading", file_path)
            mixer.music.load(file_path)
            AudioPlayer.current_sound_playing = False
            AudioPlayer.current_sound = file_path
        else:
            AudioPlayer.current_sound_playing = True

    @staticmethod
    def play_sound(volume: float, repeat: bool) -> None:
        """ Play the currently set sound file. """
        print("Playing sound", AudioPlayer.current_sound, "with volume", volume, "repeat", repeat)
        mixer.music.set_volume(volume) #.5)
        if AudioPlayer.current_sound_playing and repeat:
            print("Already playing")
            return
        print("Playing")
        mixer.music.play(-1 if repeat else 0)

    @staticmethod
    def stop_sound() -> None:
        """ Stop the currently playing sound. """
        mixer.music.stop()
        AudioPlayer.current_sound_playing = False

class NetworkManager:
    """ A class to manage network communication. """

    def __init__(self, root_window: tk.Tk, server_inbox: Queue, server_outbox: Queue, resource_manager: ResourceManager) -> None:
        self._root_window: tk.Tk = root_window
        self.__server_inbox = server_inbox
        self.__server_outbox = server_outbox
        self._resource_manager = resource_manager
        self._data_dict = {}

    def download_file(self, path):
        # curl the file
        url = f"https://infinite-fortress-70189.herokuapp.com/{path}"
        print(url)
        response = requests.get(url)
        # check response code
        if response.status_code != 200:
            raise Exception(f"Could not load {path} from server. Status code: {response.status_code}")
        data = response.content
        
        # get stem of path
        stem = os.path.basename(path)
        # save to disk
        with open(stem, 'wb') as f:
            f.write(data)
        print(f"Downloaded {path} to {stem}")

    def update_data(self, data_dict: dict) -> None:
        self._data_dict = data_dict

    def send(self, data_dict, ws=None):
        data_dict.update(self._data_dict)
        self.__server_inbox.put(data_dict)

    def insert_message(self, messages: tk.Listbox, message: str) -> None:
        """ Insert a message into the message listbox. """
        lines = message.split('\n')

        short_lines = shorten_lines(lines, 75)
        for line in short_lines:
            messages.insert(tk.END, line)

        messages.yview(tk.END)

    def on_message(self, message: bytes) -> None:
        """ Handle a message from the server. """

        try:
            data = json.loads(message)
        except:
            print(f"Bad message (encoding): {message}")
            return
        
        if 'classname' not in data:
            print(f"Bad message (no class name): {message}")
            return

        print("Received message of type", data['classname'])

        if data['classname'] == 'GridMessage':
            self._grid_updates.put((data['seq_num'], 'grid', (data['grid'], data['room_name'], data['position'], data['bg_music'])))
            if 'description' in data:
                self.insert_message(self._messages, data['room_name'])
                self.insert_message(self._messages, data['description'])
        elif data['classname'] == 'EmoteMessage':
            self._grid_updates.put((data['seq_num'], 'emote', (data['emote'], data['emote_pos'])))
        elif data['classname'] in ['DialogueMessage', 'SoundMessage', 'MenuMessage']:
            self._aux_queue.put(data)
        elif data['classname'] in ['ChatMessage', 'ServerMessage']:
            if data.get('text', '') == 'disconnect':
                self._root_window.destroy()
            elif 'room_name' in data:
                self.insert_message(self._messages, f"[{data['room_name']}] {data['handle']}: {data['text']}")
            else:
                self.insert_message(self._messages, f"{data['handle']}: {data['text']}")
        elif data['classname'] == 'FileMessage':
            self.download_file(data['file_path'])
            
        # Group 29 added these
        # --------------------------------
        elif data['classname'] == 'PokemonBattleMessage':
            # Exatract data from the message
            destroy = data['destroy']
            player_data = data['player_data']
            enemy_data = data['enemy_data']

            if destroy:
                if hasattr(self, '_pokemon_battle_window') and self._pokemon_battle_window and self._pokemon_battle_window.is_open():
                    self._root_window.after(0, self._pokemon_battle_window._window.destroy)
                    self._pokemon_battle_window = None
            elif player_data and enemy_data:
                if not hasattr(self, '_pokemon_battle_window') or self._pokemon_battle_window is None or not self._pokemon_battle_window.is_open():
                    self._pokemon_battle_window = PokemonBattleWindow(
                        self._root_window,
                        self,
                        self._resource_manager,
                        player_data,
                        enemy_data
                    )
                    self._root_window.after(0, self._pokemon_battle_window.run)
                else:
                    self._pokemon_battle_window.update_battle_state(player_data, enemy_data)

        elif data['classname'] == 'OptionsMessage':
            # Exatract data from the message
            options = data['options']
            destroy = data['destroy']

            if destroy:
                if hasattr(self, '_options_window') and self._options_window and self._options_window.is_open():
                    self._options_window._window.destroy()
                    self._options_window = None
            elif hasattr(self, '_options_window') and self._options_window and self._options_window.is_open():
                self._options_window.update_options(options)
            else:
                self._options_window = OptionsWindow(self._root_window, self, self._resource_manager, options)
                self._root_window.after(0, self._options_window.run)

        elif data['classname'] == 'ChooseObjectMessage':
            # Exatract data from the message
            options = data['options']  
            window_title = data['window_title']
            sprite_size = data['sprite_size']
            width = data['width']
            height = data['height']
            gap = data['gap']
            label_height = data['label_height']
            offset_x = data['offset_x']
            offset_y = data['offset_y']
            orientation: Literal["landscape", "portrait"] = cast(Literal["landscape", "portrait"], data['orientation'])

            # Spawn the generalized choose object window
            choose_window = ChooseObjectWindow(
                self._root_window,
                self,
                self._resource_manager,
                options,
                orientation=orientation,
                sprite_size=sprite_size,
                window_title=window_title,
                width=width,
                height=height,
                gap=gap,
                label_height=label_height,
                offset_x=offset_x,
                offset_y=offset_y
            )
            self._root_window.after(0, choose_window.run)
        
        elif data['classname'] == 'DisplayStatsMessage':
            # Exatract data from the message
            stats = data['stats']
            top_image_path = data['top_image_path']
            bottom_image_path = data['bottom_image_path']
            sprite_size = data['scale']
            window_title = data['window_title']

            # Spawn display window with general stats and images
            display_window = DisplayStatsWindow(
                self._root_window,
                self,
                self._resource_manager,
                stats,
                top_image_path,
                bottom_image_path,
                sprite_size,
                window_title
            )
            self._root_window.after(0, display_window.run)

        ## Group 23 code ########################
        elif data['classname'] == 'FestMessage':
            fsc_render(data)
        #####################################

        elif data['classname'] == 'MagicalKeyMessage':
            magical_key_window = MagicalKeyWindow(
                self._root_window, 
                self,
                self._resource_manager
            )
            self._root_window.after(0, magical_key_window.run)

        # --------------------------------
        # group 69 code
        elif data['classname'] == 'CombatUIMessage':
            destroy = data.get('destroy', False)
            left_character = data.get('left_character')
            right_character = data.get('right_character')
            
            if destroy:
                if hasattr(self, '_combat_ui_window') and self._combat_ui_window:
                    self._root_window.after(0, self._combat_ui_window._window.destroy)
                    self._combat_ui_window = None
            else:
                if not hasattr(self, '_combat_ui_window') or self._combat_ui_window is None:
                    try:
                        self._combat_ui_window = CombatUIWindow(
                            self._root_window,
                            self,
                            self._resource_manager,
                            left_character,
                            right_character
                        )
                        self._root_window.after(0, self._combat_ui_window.run)
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                else:
                    self._combat_ui_window.update_characters(left_character, right_character)
        
        elif data['classname'] == 'TimerMessage':
            time_str = data.get('time_str', "03:00")
            is_match_over = data.get('is_match_over', False)
            destroy = data.get('destroy', False)
            
            if destroy:
                if hasattr(self, '_timer_window') and self._timer_window:
                    self._root_window.after(0, self._timer_window._window.destroy)
                    self._timer_window = None
            else:
                if not hasattr(self, '_timer_window') or self._timer_window is None:
                    try:
                        self._timer_window = TimerWindow(
                            self._root_window,
                            self,
                            time_str,
                            is_match_over
                        )
                        self._root_window.after(0, self._timer_window.run)
                    except Exception as e:
                        print(f"ERROR: Failed to create Timer window: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    self._timer_window.update_timer(time_str, is_match_over)
        
        elif data['classname'] == 'WinnerMessage':
            winner_name = data.get('winner_name', 'Unknown Fighter')
            winner_stats = data.get('winner_stats', {})
            destroy = data.get('destroy', False)
            
            if destroy:
                if hasattr(self, '_combat_result_window') and self._combat_result_window:
                    self._root_window.after(0, self._combat_result_window._window.destroy)
                    self._combat_result_window = None
            else:
                # Format fighter data for the window
                fighter_data = {
                    "name": winner_name,
                    "hp": winner_stats.get("hp", 0),
                    "max_hp": winner_stats.get("max_hp", 100)
                }
                
                if not hasattr(self, '_combat_result_window') or self._combat_result_window is None:
                    try:
                        self._combat_result_window = CombatResultWindow(
                            self._root_window,
                            self,
                            fighter_data,
                            "win"  # This is a winner, so use "win" type
                        )
                        self._root_window.after(0, self._combat_result_window.run)
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
            
            # Close other windows when winner is shown
            if hasattr(self, '_combat_ui_window') and self._combat_ui_window:
                self._root_window.after(0, self._combat_ui_window._window.destroy)
                self._combat_ui_window = None
                
            if hasattr(self, '_timer_window') and self._timer_window:
                self._root_window.after(0, self._timer_window._window.destroy)
                self._timer_window = None
                
        elif data['classname'] == 'CombatResultMessage':
            fighter_name = data.get('fighter_name', 'Unknown Fighter')
            fighter_stats = data.get('fighter_stats', {})
            result_type = data.get('result_type', 'win')  # Default to win if not specified
            destroy = data.get('destroy', False)
            
            if destroy:
                if hasattr(self, '_combat_result_window') and self._combat_result_window:
                    self._root_window.after(0, self._combat_result_window._window.destroy)
                    self._combat_result_window = None
            else:
                # Format fighter data for the window
                fighter_data = {
                    "name": fighter_name,
                    "hp": fighter_stats.get("hp", 0),
                    "max_hp": fighter_stats.get("max_hp", 100)
                }
                
                if not hasattr(self, '_combat_result_window') or self._combat_result_window is None:
                    try:
                        self._combat_result_window = CombatResultWindow(
                            self._root_window,
                            self,
                            fighter_data,
                            result_type  # Use specified result type (win/lose)
                        )
                        self._root_window.after(0, self._combat_result_window.run)
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
            
            # Close other windows when result is shown
            if hasattr(self, '_combat_ui_window') and self._combat_ui_window:
                self._root_window.after(0, self._combat_ui_window._window.destroy)
                self._combat_ui_window = None
                
            if hasattr(self, '_timer_window') and self._timer_window:
                self._root_window.after(0, self._timer_window._window.destroy)
                self._timer_window = None
        # --------------------------------
         # group 7 code --------------------------------------------------------------------
        # ----------------------------------------------------------------------------------

        elif data['classname'] == 'BoxingMatchMessage':
            player_name         = data.get('player_name', 'Player')
            npc_name            = data.get('npc_name',    'NPC')
            player_initial_hp   = data.get('player_initial_hp', 100)
            npc_initial_hp      = data.get('npc_initial_hp',    100)
            turn                = data.get('turn', 0)

            boxing_match_window = BoxingBattleWindow(
                root_window      = self._root_window,
                network_manager  = self,           
                npc_name         = npc_name,
                player_name      = player_name,
                npc_initial_hp   = npc_initial_hp,
                player_initial_hp= player_initial_hp
            )
            boxing_match_window.update_turn_counter(turn)
            
            self._root_window.after(0, boxing_match_window.run)
        
        elif data['classname'] == 'BattleResultMessage':
            result = data.get('result', 'LOSE')
            fighter_data = data.get('fighter_data', {})
            battle_result_window = BattleResultWindow(self._root_window, result, fighter_data)
            self._root_window.after(0, battle_result_window.run)

        elif data['classname'] == 'EnduranceGameMessage':
            time_left = data.get('time_left', 10)
            endurance_game_window = EnduranceGameWindow(self._root_window, time_left)
            self._root_window.after(0, endurance_game_window.run)
        
        elif data['classname'] == 'WeightliftingMinigameMessage':
            difficulty = data.get('difficulty', 1.0)
            player_email = data.get('player_email', '')
            self._weight_window = WeightliftingMinigameWindow(
                self._root_window,
                self,
                self._resource_manager,
                difficulty,
                player_email
            )
            self._root_window.after(0, self._weight_window.run)

        #end of group 7 code -----------------------------------------------------------------
        #-------------------------------------------------------------------------------------
        else:
            print(f"Bad message (unknown class name): {message}")
        
    def rcv_thread(self, messages: tk.Listbox, grid_updates: Queue, aux_queue: Queue) -> NoReturn:
        """ A thread to receive and parse messages from the server. """

        self._messages = messages
        self._grid_updates = grid_updates
        self._aux_queue = aux_queue

        while True:
            if self.__server_outbox.empty():
                time.sleep(0.1)
            #if len(self._aux_queue.queue) > 0:
            #    time.sleep(1)
            message = self.__server_outbox.get()
            self.on_message(message)

class Window(ABC):
    """ A class to manage a window. Sets up the window and provides a base for subclasses. """
    def __init__(self, root_window: tk.Tk, title: str, width: int, height: int, offset_x: int, offset_y: int, bg_color: str = "white") -> None:
        """ Initialize the window. """
        self._width: int = width
        self._height: int = height

        screen_width: int = root_window.winfo_screenwidth()
        screen_height: int = root_window.winfo_screenheight()

        main_x = int((screen_width/2) - (GRID_WIDTH/2))
        main_y = int((screen_height/2) - (GRID_HEIGHT/2))

        offset_x = main_x + offset_x
        offset_y = main_y + offset_y

        self._window = tk.Toplevel(root_window)
        self._window.title(title)
        self._window.geometry(f"{width}x{height}+{offset_x}+{offset_y}")
        self._window.configure(bg=bg_color)
        self._window.resizable(False, False)
    
    def update_color(self, bg_color: str) -> None:
        """ Update the background color of the window. """
        self._window.configure(bg=bg_color)

class DialogueBox(Window):
    """ A class to manage a dialogue box. """
    def __init__(self, root_window, resource_manager, text_datas: list) -> None:
        """ Initialize the dialogue box. """

        super().__init__(root_window, title="Dialogue", width=GRID_WIDTH, height=120, offset_x=0, offset_y=-150)

        self.__root_window = root_window
        self.__border_frame = tk.Frame(self._window, bg="#FF0000")
        self.__border_frame.place(relx=0.5, rely=1.0, anchor='s', x=0, y=-10)  # Positioned at the bottom center
        self.__resource_manager = resource_manager

        self.__text_queue = Queue()
        for text_data in text_datas:
            self.__text_queue.put(text_data)

        self.__current_text = ""
        self.__current_index = 0
        self.__is_typing = False
        self.__waiting_for_auto_advance = False  # Used for auto delay
        self.__waiting_for_user = False         # New flag for waiting for user input

        self.__typing_speed = 50  # milliseconds per character

        self.__text_font: FreeTypeFont = self.__resource_manager.get_font('pkmn')
        self.__current_font = None
        self.__bg_color = None
        self.__text_color = None
        self.__press_enter = None
        self.__auto_delay = 500  # default auto delay in ms

        self.__text_label = tk.Label(self._window, text="", wraplength=self._width-40, justify="left", bg='white', fg="#000000", anchor="nw")
        self.__text_label.place(x=20, y=5, width=self._width-40, height=self._height-20)

        indicator_font = font.Font(family="Consolas", size=10, slant="italic")
        self.__indicator_label = tk.Label(self._window, text="Press [return] to continue!", bg='white', fg="#000000", font=indicator_font)

        self.__indicator_x: int = self._width - 140
        self.__indicator_y: int = self._height - 20

        self._window.bind("<Return>", self.__on_return)
        # Ensure the window has focus so key events are captured.
        self._window.focus_set()

        self.__monitor_queue()

    def is_typing(self) -> bool:
        """ Check if the dialogue box is currently typing. """
        return self.__is_typing

    def start(self) -> None:
        """Start processing the text queue."""
        if not self.__is_typing and len(self.__text_queue.queue) > 0: # and not self.__waiting_for_user:
            self.__current_text, font, self.__bg_color, self.__text_color, self.__press_enter, self.__auto_delay = self.__text_queue.get()
            self.__current_font = self.__resource_manager.get_font(font)

            # change self.__border_frame to specified bg_color
            r, g, b = self.__bg_color
            hex_color = "#%02x%02x%02x" % (r, g, b)
            print("Changing border color to", hex_color)
            self.update_color(hex_color)
            self.__border_frame.config(bg=hex_color)
            self.__text_label.config(bg=hex_color)
            self.__indicator_label.config(bg=hex_color)

            # change text color
            r, g, b = self.__text_color
            hex_color = "#%02x%02x%02x" % (r, g, b)
            self.__text_label.config(fg=hex_color)
            self.__indicator_label.config(fg=hex_color)

            self.__current_index = 0
            self.__text_label.config(text="")
            self.__hide_indicator()  # Ensure indicator is hidden before typing
            self.__is_typing = True
            self.__waiting_for_user = False
            self.__partial_text = ""
            self.__type_character()

    def __type_character(self) -> None:
        """Display text one character at a time."""
        if self.__current_index < len(self.__current_text):
            # Append next character
            next_char = self.__current_text[self.__current_index]

            self.__partial_text += next_char
            image_text = self.__resource_manager.render_font(self.__current_font, self.__partial_text, bg_color=self.__bg_color, text_color=self.__text_color)

            # display image in label
            self.tk_image = ImageTk.PhotoImage(image_text)
            self.__text_label.config(image=self.tk_image) # type: ignore
            self.__current_index += 1

            # Schedule next character
            self._window.after(self.__typing_speed, self.__type_character)
        else:
            # Typing complete.
            #self.__is_typing = False
            self.__show_indicator()
            '''
            if self.__press_enter:
                self.__show_indicator()
                self.__is_typing = False
                self.__waiting_for_user = True  # Now waiting for the user to press Return.
            else:
                # Auto advance after a brief delay.
                self.__is_typing = False
                self.__waiting_for_auto_advance = True
                self._window.after(self.__auto_delay, self.__auto_start)
            '''

    def __auto_start(self) -> None:
        """Called after auto delay expires to start the next message."""
        self.__waiting_for_auto_advance = False
        self.start()

    def __show_indicator(self) -> None:
        """Show the 'Press Return to continue...' indicator."""
        self.__indicator_label.place(x=self.__indicator_x, y=self.__indicator_y)

    def __hide_indicator(self) -> None:
        """Hide the 'Press Return to continue...' indicator."""
        self.__indicator_label.place_forget()

    def __on_return(self, event) -> None:
        print("Return key pressed; queue: ", self.__text_queue.queue)
        """Handle Return key press."""
        self.__is_typing = False
        if len(self.__text_queue.queue) > 0: # or self.__text_label.cget("image")):
            if self.__text_label.cget("image"):
                # Clear current text
                self.__text_label.config(image="")
                self.__hide_indicator()
                # Start next text
                self.start()
            else:
                # If text is already cleared, just start next
                self.start()
        else:
            self._window.after(self.__auto_delay, lambda: self._window.destroy())
            #self._window.destroy()
    
    def __monitor_queue(self) -> None:
        """Continuously monitor the queue and start processing if not already."""
        if self.__current_index >= len(self.__current_text) and not self.__press_enter:
            self.__on_return(None)
        if not self.__is_typing and len(self.__text_queue.queue) > 0:
            self.start()
        # Check again after a short delay
        self._window.after(10, self.__monitor_queue)

    def run(self):
        """Start the Tkinter main loop."""
        #self.__root_window.after(0, self._window.mainloop)
        self.__root_window.wait_window(self._window)

class MessageWindow(Window):
    """ A class to manage a message window. """
    def __init__(self, root_window: tk.Tk, network_manager: NetworkManager) -> None:
        """ Initialize the message window. """

        super().__init__(root_window, title="Messages", width=GRID_WIDTH, height=150, offset_x=0, offset_y=GRID_HEIGHT+50)

        self._window.rowconfigure(0, weight=1)  # The listbox frame
        self._window.rowconfigure(1, weight=0)  # The entry frame
        self._window.columnconfigure(0, weight=1)
        self._window.resizable(True, True)

        messages_frame = tk.Frame(master=self._window)
        scrollbar = tk.Scrollbar(master=messages_frame)
        self.__messages = tk.Listbox(
            master=messages_frame,
            yscrollcommand=scrollbar.set
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.__messages.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        messages_frame.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")

        entry_frame = tk.Frame(master=self._window)
        text_input = tk.Entry(master=entry_frame)
        text_input.pack(fill=tk.BOTH, expand=True)
        entry_frame.grid(row=1, column=0, pady=5, padx=20, sticky="ew")

        self.__setup_text_input(text_input, network_manager)

    def get_messages(self) -> tk.Listbox:
        """ Get the listbox of messages. """
        return self.__messages

    def __setup_text_input(self, text_input: tk.Entry, network_manager: NetworkManager) -> None:
        def send_from_input_field():
            text = text_input.get()
            text_input.delete(0, tk.END)
            network_manager.send({
                'text': text,
            })

        text_input.bind("<Return>", lambda x: send_from_input_field())

        default_text = "Type your message here. Then press return to send."
        text_input.insert(0, default_text)

        def clear_placeholder(event):
            if text_input.get() == default_text:
                text_input.delete(0, tk.END)
        text_input.bind("<FocusIn>", clear_placeholder)
        
        def delete_field(event):
            text_input.configure(state=NORMAL)
            text_input.delete(0, tk.END)
            text_input.unbind('<Button-1>', delete_field_id)

        delete_field_id = text_input.bind('<Button-1>', delete_field)

class GridWindow(Window):
    """ A class to manage the grid window. """
    def __init__(self, root_window: tk.Tk, network_manager: NetworkManager, resource_manager: ResourceManager) -> None:
        """ Initialize the grid window. """

        super().__init__(root_window, title="Grid", width=GRID_WIDTH, height=GRID_HEIGHT, offset_x=0, offset_y=0)

        def handle_sigint(signum, frame):
            self.__on_closing()
            sys.exit(0)
        signal.signal(signal.SIGINT, handle_sigint)
        root_window.protocol("WM_DELETE_WINDOW", self.__on_closing)
        self._window.protocol("WM_DELETE_WINDOW", self.__on_closing)
        root_window.createcommand('::tk::mac::Quit', self.__on_closing)

        self.__root_window = root_window

        self.__last_move_time = 0
        self.__cur_grid = None
        self.__cur_room_name = None
        self.__image_refs = defaultdict(list)
        self.__grid_updates = PriorityQueue()
        #self.drawn_players = {}
        #self.movements = Queue() # TODO: Dict of queues for each sprite.
        self.__emotes = Queue()
        self.__emote_refs = {}
        self.__THROTTLE_INTERVAL = 0.05

        self.__canvas = self.__create_canvases()
        self.__message_window = MessageWindow(root_window, network_manager)
        self.__setup_canvases()
        self.__network_manager = network_manager
        self.__resource_manager = resource_manager

        self.__aux_queue = Queue()
        self.__rcv_t = threading.Thread(target=network_manager.rcv_thread, args=(self.__message_window.get_messages(), self.__grid_updates, self.__aux_queue))
        self.__rcv_t.daemon = True

    def __on_closing(self):
        print("Disconnecting from server")
        self.__network_manager.send({
            'type': 'disconnect',
        })
        time.sleep(0.1)
        self.__root_window.destroy()

    def __create_canvases(self) -> tk.Canvas:
        frm_main = tk.Frame(master=self._window, borderwidth=0, relief='flat', highlightthickness=0)
        frm_main.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        canvas = tk.Canvas(master=frm_main, width=GRID_WIDTH, height=GRID_HEIGHT, bg="white", borderwidth=0, highlightthickness=0)

        canvas.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        tk.Misc.lift(canvas)

        return canvas

    def __setup_canvases(self) -> None:
        tk.Misc.lift(self.__canvas)

        # when users click on the image_label, it should gain focus
        self.__canvas.bind('<Button-1>', lambda x: self.__canvas.focus_set())

        # give it focus by default
        self.__canvas.focus_set()

        # when users press the arrow keys when the image_label has focus, the command should be sent to the server
        def send_command(event):
            current_time = time.time()
        
            # Check if enough time has passed since the last move
            if current_time - self.__last_move_time < self.__THROTTLE_INTERVAL:
                # Throttle: ignore this keypress
                print(f"Ignored {event.keysym} keypress to throttle.")
                return

            # Update the last move time
            self.__last_move_time = current_time

            self.__network_manager.send({
                'move': event.keysym,
            })
        self.__canvas.bind('<Key>', send_command)
    
    def __del__(self) -> None:
        if self.__rcv_t.is_alive():
            self.__rcv_t.join()
    
    def __draw_grid(self, cur_grid, new_grid, image_refs, cur_room_name, new_room_name, position) -> tuple[defaultdict[Any, list], list]:
        movements = []

        grid_height = len(new_grid)
        grid_width  = len(new_grid[0]) if grid_height else 0

        # Camera (window) in terms of tile counts
        camera_width  = NUM_COLS
        camera_height = NUM_ROWS

        # Desired camera origin, then clamp
        desired_camera_x = position[1] - camera_width // 2
        desired_camera_y = position[0] - camera_height // 2

        camera_x = max(0, min(desired_camera_x, grid_width  - camera_width))
        camera_y = max(0, min(desired_camera_y, grid_height - camera_height))

        # Clear the (second) canvas
        new_image_refs = defaultdict(list)

        self.__canvas.delete("all")

        PADDING = 6
        row_start = max(0, camera_y - PADDING)
        row_end   = min(grid_height, camera_y + camera_height + PADDING)

        col_start = max(0, camera_x - PADDING)
        col_end   = min(grid_width, camera_x + camera_width + PADDING)

        to_draw = []
        for tile_row in range(row_start, row_end):
            for tile_col in range(col_start, col_end):
                # Draw the tile. The key is the canvas offset:
                canvas_x = (tile_col - camera_x) * TILE_SIZE
                canvas_y = (tile_row - camera_y) * TILE_SIZE

                cell = new_grid[tile_row][tile_col]  # list of (image_name, z_index)
                for (image_name, z_index) in cell:
                    if not image_name:
                        continue
                    image = self.__resource_manager.get_image(image_name)

                    # On-canvas position
                    canvas_x = (tile_col - camera_x) * TILE_SIZE
                    canvas_y = (tile_row - camera_y) * TILE_SIZE
                    if 'character/' in image_name:
                        canvas_y -= TILE_SIZE
                    
                    to_draw.append((canvas_x, canvas_y, image, z_index, image_name, tile_col, tile_row))
        

        # Sort by z_index
        to_draw.sort(key=lambda x: x[3])
        for canvas_x, canvas_y, image, z_index, image_name, tile_col, tile_row in to_draw:
            image_id = self.__canvas.create_image(canvas_x, canvas_y, image=image, anchor=tk.NW)
            #if z_index <= -1:
            #    self.__canvas2.tag_lower(image_id)
            new_image_refs[(tile_col, tile_row)].append((image, image_id, image_name))

        return new_image_refs, movements
    
    '''
    def animate(self):
        # The following function was written by ChatGPT. That's why it is crap.

        #print("Setting vars")
        current_move = None
        max_steps = 4
        step_counter = 4
        move_direction = None
        player_img = None
        room_name = None

        def get_direction(start_tile, end_tile):
            start_x, start_y = start_tile
            end_x, end_y = end_tile
            if start_x < end_x:
                return "down"
            elif start_x > end_x:
                return "up"
            elif start_y < end_y:
                return "right"
            elif start_y > end_y:
                return "left"
            raise ValueError(f"Invalid move: {start_tile} to {end_tile}")

        def get_sprite_name(player_img, move_direction, frame_index):
            assert 0 <= frame_index < 4
            assert move_direction in ["up", "down", "left", "right"], f"Invalid move_direction: {move_direction}"
            assert player_img in ["player1", "player2", "player3", "player4", "prof"], f"Invalid player_img: {player_img}"
            return f"character/{player_img}/{move_direction}{frame_index+1}"

        def start_move(move):
            print("Starting", move[2], "move at", move[0], "to", move[1])
            nonlocal current_move, move_direction, step_counter, player_img, room_name
            (start_tile, end_tile, player, cur_room_name) = move
            move_direction = get_direction(start_tile, end_tile)  # e.g. "up", "down", "left", "right"
            step_counter = 0
            #max_steps = 4  # how many sub-frames you want for the move
            current_move = (start_tile, end_tile)
            player_img = player
            room_name = cur_room_name
            if room_name != self.cur_room_name:
                current_move = None
        
        def animate_player_step():
            nonlocal step_counter
            #print("Animation:", step_counter, max_steps)
            if step_counter < max_steps:
                # 1) Calculate fractional position
                fraction = step_counter / float(max_steps)
                # 2) Lerp from start_tile to end_tile in pixel space
                start_tile_x, start_tile_y = current_move[0]
                end_tile_x, end_tile_y = current_move[1]

                #print("Starting at", start_tile_x, start_tile_y, "and ending at", end_tile_x, end_tile_y)

                current_px_x = start_tile_x*TILE_SIZE + (end_tile_x - start_tile_x)*TILE_SIZE*fraction
                current_px_y = start_tile_y*TILE_SIZE + (end_tile_y - start_tile_y)*TILE_SIZE*fraction

                # 3) Cycle sprite
                frame_index = step_counter % 4
                sprite_name = get_sprite_name(player_img, move_direction, frame_index)  
                # e.g. for "up" + frame_index 0 → "up1.png", index 1 → "up2.png", etc.
                
                #image_id = canvas.create_image(j*32, i*32, image=image, anchor=tk.NW)
                #image_refs[(j, i)].append((image, image_id))

                # 4) Update the canvas image to the new position and sprite
                #print(self.drawn_players[player_img], current_px_y, current_px_x, get_image(sprite_name))
                self.canvas.coords(self.drawn_players[player_img], current_px_y, current_px_x)
                self.canvas.itemconfig(self.drawn_players[player_img], image=get_image(sprite_name))

                #bring player to front
                self.canvas.tag_raise(self.drawn_players[player_img])

                # 5) Increment step
                step_counter += 1
            else:
                # Finalize at the exact end tile pixel
                #print("Finishing move (1)")
                finish_current_move()
        
        def finish_current_move():
            nonlocal current_move, player_img
            (start_tile, end_tile) = current_move

            # Place the player exactly on the end tile in pixel coordinates
            end_tile_x, end_tile_y = end_tile
            final_px_x = end_tile_x * TILE_SIZE
            final_px_y = end_tile_y * TILE_SIZE
            self.canvas.coords(self.drawn_players[player_img], final_px_y, final_px_x)

            current_move = None

            if len(self.movements.queue) > 0:
                # Start the next move right away
                next_move = self.movements.get()
                #print("Finished move; next:", next_move)
                start_move(next_move)
            else:
                pass
                # No more moves, revert to idle sprite (e.g., "down1.png")
                #print("Finished move; no more moves")
                #self.canvas.itemconfig(self.drawn_players[player_img], image=get_image(f'character/{player_img}/down1')) #sprite_dict["down1"])
        
        def animate_loop():
            nonlocal current_move
            delay_ms = 8
            # 1. If the player is currently in the middle of a move, animate that step.
            if current_move is not None and step_counter <= max_steps:
                if room_name != self.cur_room_name:
                    current_move = None
                else:
                    #print("Animating step")
                    animate_player_step()
                    delay_ms = 48
                    #self.window.after(48, animate_loop, movements)  # ~60 FPS or slower for simpler animation
            # 2. Else, if we have moves in the queue, pop the next one and start animating it.
            elif len(self.movements.queue) > 0:
                #print("Starting move")
                # dequeue from movements
                movement = self.movements.get()
                start_move(movement)
                delay_ms = 48
            self.window.after(delay_ms, animate_loop)  # ~60 FPS or slower for simpler animation
            # 3. Otherwise, if no moves are left, ensure the player is in the idle sprite.
            #print("Move ended")
        
        try:
            #print("Starting animation loop")
            animate_loop()
        except:
            print(traceback.format_exc())
    '''
    
    def __draw_emotes(self) -> None:
        def delete_emote(emote_id, pos):
            self.__canvas.delete(emote_id)
            del self.__emote_refs[pos]
        
        def draw_emote():
            while not self.__emotes.empty():
                emote, (i, j) = self.__emotes.get()
                i -= 1
                print("Drawing emote", emote, "at", i, j)
                image = self.__resource_manager.get_image(f'emote/{emote}')
                image_id = self.__canvas.create_image(j*TILE_SIZE, i*TILE_SIZE, image=image, anchor=tk.NW)
                self.__emote_refs[(i, j)] = image_id
                self.__canvas.tag_raise(image_id)
                self.__canvas.after(2000, delete_emote, image_id, (i, j))
        
        try:
            draw_emote()
        except:
            print(traceback.format_exc())
        self._window.after(16, self.__draw_emotes)

    def __check_for_grid_updates(self) -> None:
        try:
            # get all elements from the grid_updates queue
            while not self.__grid_updates.empty():
                timestamp, update_type, data = self.__grid_updates.get()
                if update_type == 'grid':
                    new_grid, room_name, position, bg_music = data
                    if self.__cur_room_name != room_name:
                        AudioPlayer.stop_sound()
                        if len(bg_music) > 0:
                            sound_file = self.__resource_manager.get_sound(bg_music)
                            
                            AudioPlayer.set_sound(sound_file)

                            # Start playing the sound in a separate thread
                            play_thread = threading.Thread(target=AudioPlayer.play_sound, args=(0.5,True))
                            play_thread.start()

                    self.__image_refs, movements = self.__draw_grid(self.__cur_grid, new_grid, self.__image_refs, self.__cur_room_name, room_name, position)

                    #print("Movements:", movements)
                    #for movement in movements:
                    #    self.movements.put(movement)
                    self.__cur_grid = new_grid
                    self.__cur_room_name = room_name
                elif update_type == 'emote':
                    self.__emotes.put(data)
                else:
                    raise ValueError(f"Invalid update type: {update_type}")
        except:
            print(traceback.format_exc())
        self._window.after(16, self.__check_for_grid_updates)

    def __check_for_window_requests(self) -> None:
        try:
            while not self.__aux_queue.empty():
                data = self.__aux_queue.get()
                print("Parsing aux queue data:", data)
                if data['classname'] == 'MenuMessage':
                    menu_name, menu_options = data['menu_name'], data['menu_options']
                    menu_window = MenuWindow(self.__root_window, self.__network_manager, self.__resource_manager, menu_name, menu_options)
                    menu_window.run()
                elif data['classname'] == 'SoundMessage':
                    sound_path = data['sound_path']
                    sound_file = self.__resource_manager.get_sound(sound_path)
                    volume = data.get('volume', 0.5)
                    repeat = data.get('repeat', False)
                    
                    AudioPlayer.set_sound(sound_file)

                    # start playing the sound in a separate thread
                    play_thread = threading.Thread(target=AudioPlayer.play_sound, args=(volume,repeat,))
                    play_thread.start()
                elif data['classname'] == 'DialogueMessage':
                    def extract_dialogue_data(data):
                        lines = data['dialogue_text'].split('\n')
                        short_lines = shorten_lines(lines, 35)
                        font = data.get('dialogue_font', 'pkmn')
                        bg_color = tuple(data.get('dialogue_bg_color', (255, 255, 255)))
                        text_color = tuple(data.get('dialogue_text_color', (0, 0, 0)))
                        press_enter = data.get('dialogue_press_enter', False)
                        auto_delay = data.get('dialogue_auto_delay', 500)
                        # TODO: Add npc_name and dialogue_image.
                        
                        dialogue_data = (('\n'.join(short_lines), font, bg_color, text_color, press_enter, auto_delay))
                        return dialogue_data

                    dialogue_datas = [extract_dialogue_data(data)]
                    while len(self.__aux_queue.queue) > 0 and self.__aux_queue.queue[0]['classname'] == 'DialogueMessage':
                        elmt = self.__aux_queue.get()
                        dialogue_datas.append(extract_dialogue_data(elmt))

                    dialogue_window = DialogueBox(self.__root_window, self.__resource_manager, dialogue_datas)
                    dialogue_window.run()
                    print("Done dialogue window")
                    #if event.keysym == "Return":
                    #    self.__dialogue_window.on_return(event)
                    #    return

        except:
            print(traceback.format_exc())
        self._window.after(64, self.__check_for_window_requests)

    def start(self) -> None:
        self.__rcv_t.start()
        self._window.after(32, self.__check_for_grid_updates)
        self._window.after(16, self.__draw_emotes)
        self._window.after(66, self.__check_for_window_requests)
        #self.window.after(16, self.animate)
        self._window.mainloop()

class MenuWindow(Window):
    def __init__(self, root_window: tk.Tk, network_manager: NetworkManager, resource_manager: ResourceManager, name: str, options: list[str]) -> None:
        self.__root_window = root_window
        self.__menu_options = options
        self.__network_manager = network_manager
        self.__resource_manager = resource_manager
        self.__selected_index = 0

        super().__init__(root_window, title="Menu", width=GRID_WIDTH//2, height=GRID_HEIGHT//2, offset_x=GRID_WIDTH//4, offset_y=GRID_HEIGHT//4)

        # Create a list to hold the Label widgets for each option
        self.__option_labels, self.__image_refs = self.__create_option_labels()

        # Bind the arrow keys and return key
        self._window.bind("<Up>", self.__on_up)
        self._window.bind("<Down>", self.__on_down)
        self._window.bind("<Return>", self.__on_return)

        # Ensure the window has focus so key events are captured.
        self._window.focus_set()

    def __create_option_labels(self):
        """Create and pack a label for each menu option."""
        option_labels, images = [], {}
        for index, option in enumerate(self.__menu_options):
            prefix = "X " if index == self.__selected_index else "  "
            label_image = self.__resource_manager.render_font(self.__resource_manager.get_font('pkmn'), prefix + option)
            tk_image = ImageTk.PhotoImage(label_image)
            label = tk.Label(self._window,
                             image=tk_image,
                             anchor="w",
                             padx=20,
                             pady=5)
            label.pack(fill='x')
            option_labels.append(label)
            images[index] = tk_image
        return option_labels, images

    def __update_labels(self):
        """Refresh the label text so that the selected option is marked with an X."""
        for index, label in enumerate(self.__option_labels):
            prefix = "X " if index == self.__selected_index else "  "
            label_image = self.__resource_manager.render_font(self.__resource_manager.get_font('pkmn'), prefix + self.__menu_options[index])
            tk_image = ImageTk.PhotoImage(label_image)
            label.config(image=tk_image)
            self.__image_refs[index] = tk_image

    def __on_up(self, event):
        """Move the selection up."""
        if self.__selected_index > 0:
            self.__selected_index -= 1
            self.__update_labels()

    def __on_down(self, event):
        """Move the selection down."""
        if self.__selected_index < len(self.__menu_options) - 1:
            self.__selected_index += 1
            self.__update_labels()

    def __on_return(self, event):
        """Send the selected option and close the window."""
        selected_option = self.__menu_options[self.__selected_index]
        self.__network_manager.send({
            'menu_option': selected_option,
        })
        self._window.destroy()

    def run(self):
        """Start the Tkinter main loop."""
        self.__root_window.wait_window(self._window)

def start() -> None:
    """ Start the client. """

    LOCAL = True

    root_window = tk.Tk()
    root_window.title('LOCAL')
    root_window.withdraw()

    resource_manager = ResourceManager()

    from .server_local import ChatBackend
    server = ChatBackend()
    server_inbox, server_outbox = server.start()
    network_manager = NetworkManager(root_window, server_inbox, server_outbox, resource_manager)

    main_window = GridWindow(root_window, network_manager, resource_manager)
    main_window.start()

#------ GROUP 7  ADDITIONS -----------------------------------------------
#-------------------------------------------------------------------------

class BoxingBattleWindow(Window):
    """
    A Pokémon‐style UI for a boxing match that sends moves back to the server directly.
    """
    def __init__(
        self,
        root_window: tk.Tk,
        network_manager: NetworkManager,
        npc_name: str,
        player_name: str,
        npc_initial_hp: int = 100,
        player_initial_hp: int = 100
    ):
        # Initialize the base Window: create self._window
        super().__init__(
            root_window,
            title="Boxing Battle",
            width=640, height=480,
            offset_x=0, offset_y=0,
            bg_color="lightgray"
        )
        self._net = network_manager

        # Track HP.
        self.npc_max_hp = npc_initial_hp
        self.player_max_hp = player_initial_hp
        self.npc_current_hp = npc_initial_hp
        self.player_current_hp = player_initial_hp

        # ============== TOP FRAME (NPC info and turn counter) ==============
        self.top_frame = tk.Frame(self._window, bg="white", height=80)
        self.top_frame.pack(side="top", fill="x")

        self.npc_name_label = tk.Label(
            self.top_frame, text=npc_name,
            font=("Arial", 14, "bold"),
            bg="white"
        )
        self.npc_name_label.pack(anchor="nw", padx=10, pady=5)

        self.npc_hp_bar = ttk.Progressbar(self.top_frame, length=200)
        self.npc_hp_bar.pack(anchor="nw", padx=10)
        self.npc_hp_bar["maximum"] = self.npc_max_hp
        self.npc_hp_bar["value"] = self.npc_current_hp

        self.turn_counter_label = tk.Label(
            self.top_frame, text="Turn: 0",
            font=("Arial", 12), bg="white"
        )
        self.turn_counter_label.pack(anchor="ne", padx=10, pady=5)

        # ============== MIDDLE FRAME (Sprites) ==============
        self.middle_frame = tk.Frame(self._window, bg="green", height=180)
        self.middle_frame.pack(side="top", fill="x", expand=True)

        # ============== LOG FRAME (Battle log) ==============
        self.log_frame = tk.Frame(self._window, bg="lightgray", height=60)
        self.log_frame.pack(side="top", fill="x")

        self.log_text = tk.Text(self.log_frame, height=3, bg="lightgray", fg="black", state="disabled")
        self.log_text.pack(fill="both", padx=10, pady=5)

        # ============== BOTTOM FRAME (Player info & moves) ==============
        self.bottom_frame = tk.Frame(self._window, bg="white", height=160)
        self.bottom_frame.pack(side="bottom", fill="x")

        self.player_name_label = tk.Label(
            self.bottom_frame, text=player_name,
            font=("Arial", 14, "bold"), bg="white"
        )
        self.player_name_label.pack(anchor="nw", padx=10, pady=(5,0))

        self.player_hp_bar = ttk.Progressbar(self.bottom_frame, length=200)
        self.player_hp_bar.pack(anchor="nw", padx=10)
        self.player_hp_bar["maximum"] = self.player_max_hp
        self.player_hp_bar["value"] = self.player_current_hp

        self.moves_frame = tk.Frame(self.bottom_frame, bg="white")
        self.moves_frame.pack(fill="both", expand=True, pady=10)

        for i, move_name in enumerate(["Punch", "Dodge", "Block", "Forfeit"]):
            btn = tk.Button(
                self.moves_frame,
                text=move_name,
                width=10,
                command=lambda m=move_name: self.__send_move(m,None)
            )
            row, col = divmod(i, 2)
            btn.grid(row=row, column=col, padx=10, pady=5)

        # allow window to be closed or Return to signal “done”
        self._window.protocol("WM_DELETE_WINDOW", self.__on_close)
        self._window.bind("<Return>", self.__on_close)

    def __send_move(self, move_name: str, event):
        self._net.send({
            "Your move": move_name
        })

    def __on_close(self, event=None):
        """Optionally notify server that the UI closed, then destroy."""
        self._net.send({
            "classname": "BattleUIClosedMessage"
        })
        self._window.destroy()

    def update_npc_hp(self, new_hp: int):
        self.npc_current_hp = max(0, min(new_hp, self.npc_max_hp))
        self.npc_hp_bar["value"] = self.npc_current_hp

    def update_player_hp(self, new_hp: int):
        self.player_current_hp = max(0, min(new_hp, self.player_max_hp))
        self.player_hp_bar["value"] = self.player_current_hp

    def update_turn_counter(self, turn: int):
        self.turn_counter_label.config(text=f"Turn: {turn}")

    def append_log(self, text: str):
        self.log_text.config(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def run(self):
        """Show and raise the window."""
        self._window.deiconify()
        self._window.lift()

class BattleResultWindow(Window):
    """
    A window to display the outcome of the battle.
    It shows an appropriate message and fighter information.
    """
    def __init__(self, root_window: tk.Tk, result: str, fighter_data: dict):
        width, height = 640, 480
        offset_x, offset_y = 100, 100
        # Use a dark background; adjust colors based on result.
        bg_color = "black"
        super().__init__(root_window, title="Battle Result", width=width, height=height,
                         offset_x=offset_x, offset_y=offset_y, bg_color=bg_color)
        self.result = result
        self.fighter_data = fighter_data
        result_text = "YOU WIN!" if result.upper() == "WIN" else "YOU LOSE!"
        label = tk.Label(self._window, text=result_text, font=("Arial", 48, "bold"),
                         fg="green" if result.upper() == "WIN" else "red", bg=bg_color)
        label.pack(expand=True, fill="both")
    
    def run(self):
        self._window.deiconify()
        self._window.lift()

class EnduranceGameWindow(Window):
    """
    A window that runs the endurance minigame.
    This window mimics our old endurance_game but is now triggered by a message.
    """
    def __init__(self, root_window: tk.Tk, time_left: int = 10):
        width, height = 600, 400
        offset_x, offset_y = 300, 200
        super().__init__(root_window, title="Endurance Game", width=width, height=height,
                         offset_x=offset_x, offset_y=offset_y, bg_color="white")
        self.time_left = time_left
        self.click_count = 0
        self.timer_started = False
        self.timer_label = tk.Label(self._window, text=f"Time: {self.time_left}", font=("Arial", 24))
        self.timer_label.pack(pady=20)
        self.click_button = tk.Button(self._window, text="Click as fast as you can!", font=("Arial", 20), command=self.button_clicked)
        self.click_button.pack(pady=20)

    def button_clicked(self):
        self.click_count += 1
        if not self.timer_started:
            self.timer_started = True
            self.countdown()

    def countdown(self):
        if self.time_left > 0:
            self.timer_label.config(text=f"Time: {self.time_left}")
            self.time_left -= 1
            self._window.after(1000, self.countdown)
        else:
            self.end_game()

    def end_game(self):
        self.click_button.pack_forget()
        self.timer_label.config(text=f"Clicks: {self.click_count}")

    def run(self):
        self._window.mainloop()

class WeightliftingMinigameWindow(Window):
    def __init__(self, root_window, network_manager, resource_manager, difficulty: float, player_email: str):
        super().__init__(
            root_window,
            title="Weightlifting Challenge",
            width=550,
            height=450,
            offset_x=0,
            offset_y=0
        )
        
        self.__network_manager = network_manager
        self.__result_label = None
        
        self.__player_email = player_email
        self.__current_difficulty = difficulty

        # Game constants
        self.__CANVAS_WIDTH = 400
        self.__SLIDER_WIDTH = 10
        self.__TARGET_BASE_WIDTH = 80
        self.__BASE_SPEED = 3
        
        # Game state
        self.__game_active = False
        self.__score = 0
        self.__target_position = 0
        self.__slider_position = 0
        self.__slider_direction = 1
        self.__slider_speed = self.__BASE_SPEED + self.__current_difficulty * 1.5
        
        # UI setup
        self.__setup_ui()
        self._window.bind("<Return>", self.__handle_key_press)
        self._window.focus_set()

    def __setup_ui(self):
        """Set up the game UI elements"""
        self._window.configure(bg="#1a0000")
        
        title_label = tk.Label(
            self._window,
            text=f"💪 Weightlifting Challenge (Difficulty: {self.__current_difficulty:.1f}) 💪",
            font=("Arial", 16, "bold"),
            bg="#1a0000",
            fg="#ff3300"
        )
        title_label.pack(pady=10)
        
        instr_label = tk.Label(
            self._window,
            text="Press ENTER when the bar aligns with the target!",
            font=("Arial", 12),
            bg="#1a0000",
            fg="#ff9999"
        )
        instr_label.pack(pady=5)
        
        # Create canvas for the minigame
        self.__canvas = tk.Canvas(
            self._window,
            width=self.__CANVAS_WIDTH,
            height=200,
            bg="#110000",
            highlightthickness=0
        )
        self.__canvas.pack(pady=20)
        
        # Draw the progress bar background
        bar_left = (self.__CANVAS_WIDTH - 300) // 2
        bar_right = bar_left + 300
        self.__canvas.create_rectangle(bar_left, 80, bar_right, 120, fill="#330000", outline="#660000")
        
        # Draw target zone
        target_width = int(self.__TARGET_BASE_WIDTH - (self.__current_difficulty * 10))
        self.__target_position = (self.__CANVAS_WIDTH - target_width) // 2
        self.__target = self.__canvas.create_rectangle(
            self.__target_position, 80,
            self.__target_position + target_width, 120,
            fill="#00aa00", outline=""
        )
        
        # Draw slider 
        self.__slider = self.__canvas.create_rectangle(
            bar_left, 70,
            bar_left + self.__SLIDER_WIDTH, 130,
            fill="#ff5500", outline=""
        )
        
        # Score display
        self.__score_label = tk.Label(
            self._window,
            text="Score: 0",
            font=("Arial", 14, "bold"),
            bg="#1a0000",
            fg="#ffffff"
        )
        self.__score_label.pack(pady=10)
        
        # Start button
        self.__start_button = tk.Button(
            self._window,
            text="Start",
            command=self.__start_game,
            bg="#ff3300",
            fg="white",
            font=("Arial", 12),
            padx=20
        )
        self.__start_button.pack(pady=10)

    def __start_game(self):
        """Start the minigame with current difficulty settings"""
        self.__game_active = True
        self.__score = 0
        self.__update_score()
        self.__start_button.pack_forget()
        
        # Set target width based on current difficulty
        target_width = int(self.__TARGET_BASE_WIDTH - (self.__current_difficulty * 10))
        self.__target_position = (self.__CANVAS_WIDTH - target_width) // 2
        
        # Update target display
        self.__canvas.coords(
            self.__target,
            self.__target_position, 80,
            self.__target_position + target_width, 120
        )
        
        # Start animation
        self.__animate_slider()
    
    def __update_score(self):
        """Update the score display and check for completion"""
        self.__score_label.config(text=f"Score: {self.__score}")
        
        if self.__score >= 10:
            self.__end_game(True)

    def __animate_slider(self):
        """Animate the slider moving back and forth"""
        if not self.__game_active:
            return
            
        bar_left = (self.__CANVAS_WIDTH - 300) // 2
        bar_right = bar_left + 300 - self.__SLIDER_WIDTH
        
        # Update slider position
        self.__slider_position += self.__slider_speed * self.__slider_direction
        
        # Reverse direction at edges
        if self.__slider_position <= 0:
            self.__slider_position = 0
            self.__slider_direction = 1
        elif self.__slider_position >= bar_right - bar_left:
            self.__slider_position = bar_right - bar_left
            self.__slider_direction = -1
            
        # Update slider position on canvas
        self.__canvas.coords(
            self.__slider,
            bar_left + self.__slider_position, 70,
            bar_left + self.__slider_position + self.__SLIDER_WIDTH, 130
        )
        
        # Continue animation
        self._window.after(20, self.__animate_slider)

    def __handle_key_press(self, event=None):
        """Handle the key press to attempt a lift"""
        if not self.__game_active:
            return
            
        slider_center = (self.__CANVAS_WIDTH - 300) // 2 + self.__slider_position + self.__SLIDER_WIDTH/2
        target_width = int(self.__TARGET_BASE_WIDTH - (self.__current_difficulty * 10))
        target_center = self.__target_position + target_width/2
        
        # Check if slider is in target zone
        if abs(slider_center - target_center) < target_width/2:
            # Successful lift
            self.__score += 1
            self.__update_score()
            
            # Flash green to indicate success
            self.__canvas.itemconfig(self.__target, fill="#00ff00")
            self._window.after(200, lambda: self.__canvas.itemconfig(self.__target, fill="#00aa00"))
        else:
            # Failed attempt
            self.__canvas.itemconfig(self.__target, fill="#ff0000")
            self._window.after(200, lambda: self.__canvas.itemconfig(self.__target, fill="#00aa00"))

    def __end_game(self, success: bool):
        self.__game_active = False
        if success:
            result_text = "SUCCESS!    Strength +1"
            self.__network_manager.send({
                'weightlifting_result': 'completed',
                'score': self.__score,
                'difficulty': self.__current_difficulty,
                'strength_increase': 1,        
                'player_email': self.__player_email
            })
        else:
            result_text = "Try again!"


        if self.__result_label is not None:
            self.__result_label.pack_forget()
            
        self.__result_label = tk.Label(
            self._window,
            text=result_text,
            font=("Arial", 14, "bold"),
            bg="#1a0000",
            fg="#00ff00" if success else "#ff0000"
        )
        self.__result_label.pack(pady=10)
        
        # Show start button again
        self.__start_button.pack(pady=10)
        
    def run(self):
        """Start the window's main loop"""
        self._window.mainloop()
#END OF GROUP 7 ADDITIONS ------------------------------------------------
# ------------------------------------------------------------------------

# Group 29 added these
# ---------------------------------------------------------------------------------
class PokemonBattleWindow(Window):
    """
    window for displaying a Pokemon battle between player Pokemon and enemy Pokemon.

    Shows sprites, HP bars, names and levels, and handles hit animations.
    """
    def __init__(self, root_window: tk.Tk, network_manager: NetworkManager, resource_manager: ResourceManager,
                 player_data: dict, enemy_data: dict) -> None:
        super().__init__(root_window, title="Battle", width=525, height=270, offset_x=-540, offset_y=-150)

        self.__network_manager = network_manager
        self.__resource_manager = resource_manager

        self.__player_data = player_data
        self.__enemy_data = enemy_data

        # Detect whether HP decreased during update
        self.__prev_player_hp = player_data["hp"]
        self.__prev_enemy_hp = enemy_data["hp"]

        # Detect whether Pokemon was switched during update
        self.__prev_player_name = player_data["name"]
        self.__prev_enemy_name = enemy_data["name"]

        self.__image_refs = []  # prevent images from being garbage collected

        self.__canvas = tk.Canvas(self._window, width=525, height=270)
        self.__canvas.pack(fill="both", expand=True)

        self.__load_images()

    def __load_images(self):
        """Draw background, Pokemon, and HP bars initially."""
        # Use get_pil_image to manually resize background
        pil_bg = self.__resource_manager.get_pil_image("fight_background").convert("RGB")
        pil_bg = pil_bg.resize((525, 270), Image.Resampling.NEAREST)
        bg_img = ImageTk.PhotoImage(pil_bg)
        self.__canvas.create_image(0, 0, image=bg_img, anchor=tk.NW)
        self.__image_refs.append(bg_img)

        # Draw both Pokemon and their health bars
        self.__draw_pokemon(self.__player_data["name"], back=True, position=(170, 190), resize=(160, 160))  # player
        self.__draw_pokemon(self.__enemy_data["name"], back=False, position=(355, 120), resize=(130, 130))  # enemy
        self.__draw_name_and_level(self.__player_data["name"], self.__player_data["level"], x=0, y=61)
        self.__draw_name_and_level(self.__enemy_data["name"], self.__enemy_data["level"], x=525, y=171, align="right")
        self.__draw_health_bar(-20, 70, self.__player_data["hp"], self.__player_data["max_hp"])
        self.__draw_health_bar(335, 180, self.__enemy_data["hp"], self.__enemy_data["max_hp"])

    def __draw_pokemon(self, pokemon_name: str, back: bool, position: tuple[int, int], resize: tuple[int, int]):
        """Draw a Pokemon sprite on the canvas with resizing support."""
        sprite_type = "back" if back else "front"
        key = f"Pokemon/{pokemon_name}_{sprite_type}"

        # Get raw PIL image, resize it, then convert to Tk image
        pil_image = self.__resource_manager.get_pil_image(key).convert("RGBA")
        pil_image = pil_image.resize(resize, Image.Resampling.NEAREST)
        tk_image = ImageTk.PhotoImage(pil_image)

        self.__canvas.create_image(*position, image=tk_image, anchor=tk.CENTER, tags="sprites")
        self.__image_refs.append(tk_image)

    def __draw_health_bar(self, x: int, y: int, hp: int, max_hp: int):
        """Draw Pokemon's health bar based on HP percentage."""
        percent = int((hp / max_hp) * 100)
        percent = max(0, min(100, percent))  # clamp to 0–100
        rounded = round(percent / 5) * 5  # round to nearest 5%
        if rounded == 0 and hp > 0:
            rounded = 1  # ensure min 1% is shown

        key = f"HealthBars/{rounded}"
        bar_image = self.__resource_manager.get_image(key)
        self.__canvas.create_image(x, y, image=bar_image, anchor=tk.NW, tags="sprites")
        self.__image_refs.append(bar_image)

    def __draw_name_and_level(self, name: str, level: int, x: int, y: int, align: str = "left"):
        """Draw Pokemon's name and level above HP bar with alignment options ('left', 'center', 'right')."""
        label = f" {name} Lv.{level} "
        pil_image = self.__resource_manager.render_font(
            self.__resource_manager.get_font("pkmn"),
            label,
            text_color=(255, 255, 255),  # white text
            bg_color=(32, 32, 32)  # dark grey background
        )

        # Add rounded corners
        radius = 10  # corner radius
        mask = Image.new("L", pil_image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, pil_image.width, pil_image.height], radius=radius, fill=255)
        rounded_image = pil_image.copy()
        rounded_image.putalpha(mask)

        if align == "right":
            x -= pil_image.width

        tk_image = ImageTk.PhotoImage(rounded_image)
        self.__canvas.create_image(x, y, image=tk_image, anchor=tk.NW, tags="sprites")
        self.__image_refs.append(tk_image)

    def update_battle_state(self, player_data: dict, enemy_data: dict):
        """Update both Pokemon and their HP. Overlay a white sprite if damage taken."""
        player_took_damage = player_data["hp"] < self.__prev_player_hp
        enemy_took_damage = enemy_data["hp"] < self.__prev_enemy_hp

        player_switched = player_data["name"] != self.__prev_player_name
        enemy_switched = enemy_data["name"] != self.__prev_enemy_name

        self.__prev_player_hp = player_data["hp"]
        self.__prev_enemy_hp = enemy_data["hp"]

        self.__player_data = player_data
        self.__enemy_data = enemy_data

        self.__canvas.delete("sprites")

        self.__draw_pokemon(player_data["name"], back=True, position=(170, 190), resize=(160, 160))
        self.__draw_pokemon(enemy_data["name"], back=False, position=(355, 120), resize=(130, 130))
        self.__draw_name_and_level(player_data["name"], player_data["level"], x=0, y=61)
        self.__draw_name_and_level(enemy_data["name"], enemy_data["level"], x=525, y=171, align="right")
        self.__draw_health_bar(-20, 70, player_data["hp"], player_data["max_hp"])
        self.__draw_health_bar(335, 180, enemy_data["hp"], enemy_data["max_hp"])

        if player_took_damage and not player_switched:
            self._window.after(0, lambda: self.__draw_white_flash(player_data["name"], back=True, position=(170, 190), resize=(160, 160)))
        if enemy_took_damage and not enemy_switched:
            self._window.after(0, lambda: self.__draw_white_flash(enemy_data["name"], back=False, position=(355, 120), resize=(130, 130)))

        self.__prev_player_name = player_data["name"]
        self.__prev_enemy_name = enemy_data["name"]

    def __draw_white_flash(self, pokemon_name: str, back: bool, position: tuple[int, int], resize: tuple[int, int]):
        """Overlay a white sprite momentarily to indicate damage taken."""
        sprite_type = "back" if back else "front"
        key = f"Pokemon/{pokemon_name}_{sprite_type}"

        # Use the new get_pil_image method
        image = self.__resource_manager.get_pil_image(key).convert("RGBA")
        image = image.resize(resize)

        r, g, b, a = image.split()
        white_base = Image.new("RGBA", image.size, (255, 255, 255, 0))
        white_overlay = Image.new("RGBA", image.size, (255, 255, 255, 255))
        white_masked = Image.composite(white_overlay, white_base, a)

        tk_image = ImageTk.PhotoImage(white_masked)
        sprite = self.__canvas.create_image(*position, image=tk_image, anchor=tk.CENTER)
        self.__image_refs.append(tk_image)

        self._window.after(1000, lambda: self.__canvas.delete(sprite))

    def is_open(self):
        """ Return whether a current instance of window is open. """
        return bool(self._window.winfo_exists())

    def run(self):
        """Start the Tkinter main loop."""
        self._window.mainloop()


class OptionsWindow(Window):
    def __init__(self, root_window: tk.Tk, network_manager: NetworkManager, resource_manager: ResourceManager, options: list[str]) -> None:
        self.__root_window = root_window
        self.__network_manager = network_manager
        self.__resource_manager = resource_manager

        self.__options = self.__to_grid(options)
        
        # Cursor position
        self.__selected_row = 0 
        self.__selected_col = 0

        super().__init__(root_window, title="Options", width=525, height=150, offset_x=-540, offset_y=150)

        self.__option_labels = []
        self.__image_refs = {} # so that the images don't get garbage collected
        self.__build_options()

        # Bind the arrow and return keys
        self._window.bind("<Up>", self.__on_up)
        self._window.bind("<Down>", self.__on_down)
        self._window.bind("<Left>", self.__on_left)
        self._window.bind("<Right>", self.__on_right)
        self._window.bind("<Return>", self.__on_return)
        self._window.focus_set()
        self._window.configure(bg="#424242") # bg is dark grey

    # Convert a 1D list of options to a 2D list. (this will be the grid)
    def __to_grid(self, options: list[str]) -> list[list[str]]:
        grid = []
        midpoint = (len(options) + 1) // 2
        for i in range(midpoint):
            if i + midpoint < len(options):
                grid.append([options[i], options[i + midpoint]])
            else:
                grid.append([options[i]])
        return grid

    def __get_prefix(self, row: int, col: int) -> str:
        """Return prefix for label based on current cursor location in grid."""
        return " > " if row == self.__selected_row and col == self.__selected_col else "  "

    def __make_label_image(self, text: str) -> ImageTk.PhotoImage:
        """Create a label image with the given text."""
        label_image = self.__resource_manager.render_font(
            self.__resource_manager.get_font('pkmn'), text)
        return ImageTk.PhotoImage(label_image)

    def __build_options(self):
        """Build the labels and set up the grid to make an options menu."""
        for row_index, row in enumerate(self.__options):
            label_row = []
            for col_index, option in enumerate(row):
                prefix = self.__get_prefix(row_index, col_index)
                tk_image = self.__make_label_image(prefix + option + "  ")
                label = tk.Label(self._window, image=tk_image, anchor="w")
                label.grid(row=row_index, column=col_index, padx=10, pady=5, sticky="w")
                label_row.append(label)
                self.__image_refs[(row_index, col_index)] = tk_image
            self.__option_labels.append(label_row)

        for col_index in range(max(len(row) for row in self.__options)):
            self._window.grid_columnconfigure(col_index, weight=1)

    def update_options(self, new_options: list[str]) -> None:
        """Update options displayed in window with new options. Public method because it's called from outside."""
        # Destroy previous labels
        for row in self.__option_labels:
            for label in row:
                label.destroy()
        self.__option_labels = []
        self.__options = self.__to_grid(new_options)
        self.__selected_row = 0
        self.__selected_col = 0
        self.__build_options()
        
    def __update_cursor(self):
        """Show where the cursor is in the grid. (by updating the label images)"""
        for row_index, row in enumerate(self.__options):
            for col_index, option in enumerate(row):
                prefix = self.__get_prefix(row_index, col_index)
                tk_image = self.__make_label_image(prefix + option + "  ")
                label = self.__option_labels[row_index][col_index]
                label.config(image=tk_image)
                self.__image_refs[(row_index, col_index)] = tk_image

    def __on_up(self, event):
        if self.__selected_row > 0:
            self.__selected_row -= 1
            self.__selected_col = min(self.__selected_col, len(self.__options[self.__selected_row]) - 1)
            self.__update_cursor()

    def __on_down(self, event):
        if self.__selected_row < len(self.__options) - 1:
            self.__selected_row += 1
            self.__selected_col = min(self.__selected_col, len(self.__options[self.__selected_row]) - 1)
            self.__update_cursor()

    def __on_left(self, event):
        if self.__selected_col > 0:
            self.__selected_col -= 1
            self.__update_cursor()

    def __on_right(self, event):
        if self.__selected_col < len(self.__options[self.__selected_row]) - 1:
            self.__selected_col += 1
            self.__update_cursor()

    def __on_return(self, event):
        """Send the selected option to the server and close the window."""
        selected_option = self.__options[self.__selected_row][self.__selected_col]
        self.__network_manager.send({
            'menu_option': selected_option,
        })

    def is_open(self) -> bool:
        """ Return whether a current instance of window is open. """
        return bool(self._window.winfo_exists())

    def run(self):
        """Start the Tkinter main loop."""
        self.__root_window.after(0, self._window.mainloop)
        
class ChooseObjectWindow(Window):
    """
    A window that allows the player to choose between n labeled options, each accompanied by a sprite.

    Intended for Pokemon selection, but it is generalized. You can use it for other purposes!
    
    It's perfect for sprites around 96x96 pixels.
    """
    def __init__(self, root_window: tk.Tk, network_manager: NetworkManager,
                 resource_manager: ResourceManager, options: list[dict], orientation: Literal["landscape", "portrait"],
                 sprite_size: int, window_title: str, width: int, height: int, gap: int, label_height: int, offset_x: int, offset_y: int) -> None:
        self.__root_window = root_window
        self.__network_manager = network_manager
        self.__resource_manager = resource_manager
        self.__options = options  # list of dicts: [{label: image_path}, ...]
        self.__orientation = orientation # portrait or landscape
        self.__selected_index = 0 # current selection index
        self.__image_refs = {}  # prevent images from being garbage collected
        self.__sprite_size = sprite_size  # scale factor for images
        self.__gap = gap # spacing multipler between options
        self._label_height = label_height # y positioning of labels

        super().__init__(root_window, title=window_title, width=width, height=height, offset_x=-offset_x, offset_y=offset_y)

        self.__canvas = tk.Canvas(self._window, width=width, height=height, bg="#424242", highlightthickness=0)
        self.__canvas.pack()

        self.__draw_sprites()
        self.__option_labels = self.__draw_option_labels()

        # Bind left, right and return key
        if (orientation == "landscape"):
            self._window.bind("<Left>", self.__on_left)
            self._window.bind("<Right>", self.__on_right)
        else: # if orientation is portrait
            self._window.bind("<Up>", self.__on_left)
            self._window.bind("<Down>", self.__on_right)

        self._window.bind("<Return>", self.__on_return)
        self._window.focus_set()

    def __draw_sprites(self):
        """Draw each image sprite with its corresponding label."""
        for i, option_dict in enumerate(self.__options):
            label, image_path = list(option_dict.items())[0]
            tk_image = self.__resource_manager.get_image(image_path.lower().replace("image/", ""))

            if self.__orientation == "landscape":
                # horizontal layout
                x = 100 + i * self.__gap
                y = 0
                anchor = tk.N
            else: # if orientation is "portrait"
                # vertical layout
                x = 50
                y = 20 + i * (self.__sprite_size + self.__gap) # stack vertically with gap
                anchor = tk.NW

            self.__canvas.create_image(x, y, image=tk_image, anchor=anchor)
            self.__image_refs[i] = tk_image

    def __draw_option_labels(self):
        """Render and place label text for each option."""
        labels = []
        for i, option_dict in enumerate(self.__options):
            label_text = list(option_dict.keys())[0]
            prefix = " > " if i == self.__selected_index else "   "  # cursor prefix
            
            # Create label image with pkmn font
            label_image = self.__resource_manager.render_font(
                self.__resource_manager.get_font('pkmn'), prefix + label_text + "  ")
            tk_image = ImageTk.PhotoImage(label_image)

            if self.__orientation == "landscape":
                x = 100 + i * self.__gap
                y = self._label_height
                anchor = tk.N
            else:
                # place labels to the right of sprites in portrait mode
                x = 70 + self.__sprite_size
                y = 20 + i * (self.__sprite_size + self.__gap)
                y += (self.__sprite_size // 2) + 10 # vertically center with sprite
                anchor = tk.W

            label = self.__canvas.create_image(x, y, image=tk_image, anchor=anchor)
            self.__image_refs[f"label_{i}"] = tk_image
            labels.append(label)
        return labels

    def __update_labels(self):
        """Update labels to reflect current cursor/selection."""
        for i, option_dict in enumerate(self.__options):
            label_text = list(option_dict.keys())[0]
            prefix = " > " if i == self.__selected_index else "   " # cursor prefix
            label_image = self.__resource_manager.render_font(
                self.__resource_manager.get_font('pkmn'), prefix + label_text + "  ")
            tk_image = ImageTk.PhotoImage(label_image)
            self.__canvas.itemconfig(self.__option_labels[i], image=tk_image)
            self.__image_refs[f"label_{i}"] = tk_image

    def __on_left(self, event):
        """Move selection to the previous option."""
        if self.__selected_index > 0:
            self.__selected_index -= 1
            self.__update_labels()
        else: # reset to last if first option
            self.__selected_index = len(self.__option_labels) - 1
            self.__update_labels()

    def __on_right(self, event):
        """Move selection to the next option."""
        if self.__selected_index < len(self.__option_labels) - 1:
            self.__selected_index += 1
            self.__update_labels()
        else: # reset to beginning if last option
            self.__selected_index = 0
            self.__update_labels()

    def __on_return(self, event):
        """Send selected option to server and close window."""
        selected_label = list(self.__options[self.__selected_index].keys())[0]
        self.__network_manager.send({
            'menu_option': selected_label,
        })
        self._window.destroy()

    def run(self):
        """Start the Tkinter main loop."""
        self.__root_window.after(0, self._window.mainloop)
        
class DisplayStatsWindow(Window):
    """
    A window that displays a list of formatted strings on the left and two images on the right (top and bottom).
    
    On [return], the window is closed.
    
    Created to display Pokemon stats and images, however, you can use it for other purposes!
    """
    def __init__(self, root_window: tk.Tk, network_manager: NetworkManager,
                 resource_manager: ResourceManager, stats: list[str],
                 top_image_path: str, bottom_image_path: str, scale: float = 1.5,
                 window_title: str = "Stats") -> None:
        super().__init__(root_window, title=window_title, width=440, height=440, offset_x=20, offset_y=30)

        self.__root_window = root_window
        self.__network_manager = network_manager
        self.__resource_manager = resource_manager
        self.__stats = stats
        self.__top_image_path = top_image_path  # updated to keep as relative path
        self.__bottom_image_path = bottom_image_path  # updated to keep as relative path
        self.__scale = scale  # scale factor for images
        self.__image_refs = []  # retain references to images to avoid garbage collection

        self.__canvas = tk.Canvas(self._window, width=440, height=440, bg="#424242", highlightthickness=0)
        self.__canvas.pack()

        self._window.bind("<Return>", self.__on_return)  # bind return key 
        self._window.focus_set()

        self.__draw_contents()

    def __draw_contents(self):
        """Render the list of str and images on the canvas."""
        
        y = 40  # initial vertical offset for lines

        # loop to render each line
        for line in self.__stats:
            text_image = self.__resource_manager.render_font(
                self.__resource_manager.get_font("pkmn"),  # use custom 'pkmn' font
                line,
                text_color=(255, 255, 255),  # white text
                bg_color=(66, 66, 66)  # dark grey background, equiv to #424242
            )
            tk_image = ImageTk.PhotoImage(text_image)
            self.__canvas.create_image(20, y, image=tk_image, anchor=tk.NW)  # draw text image
            self.__image_refs.append(tk_image)  # prevent image from being garbage collected
            y += 25 

        # Calculate image size based on scale
        img_size = int(self.__scale * 100)

        # Load and draw top image using resource manager
        top_img = self.__resource_manager.get_image(self.__top_image_path.lower().replace("image/", ""))
        self.__canvas.create_image(340, 100, image=top_img, anchor=tk.CENTER)
        self.__image_refs.append(top_img)

        # Load and draw bottom image using resource manager
        bottom_img = self.__resource_manager.get_image(self.__bottom_image_path.lower().replace("image/", ""))
        self.__canvas.create_image(340, 275, image=bottom_img, anchor=tk.CENTER)
        self.__image_refs.append(bottom_img)

        # Add instruction to close window
        self.__canvas.create_text(220, 410, text="----- Press [return] to exit -----",
                                  font=("Arial", 12))

    def __on_return(self, event):
        self._window.destroy()  # close the window

    def run(self):
        """Start the Tkinter main loop."""
        self.__root_window.after(0, self._window.mainloop)  
        
# ---------------------------------------------------------------------------------
# Group 69 added these
# ---------------------------------------------------------------------------------

class CombatUIWindow(Window):
    """
    Window for displaying combat statistics and status during fights.
    
    Shows character stats for both combatants including health bars, attack power, 
    and special ability cooldowns. 
    The UI is split into two panels, one for the player and one for the opponent.
    """
    
    def __init__(self, root_window: tk.Tk, network_manager: NetworkManager, resource_manager: ResourceManager,
                 left_character: dict = None, right_character: dict = None) -> None:
        super().__init__(root_window, title="Combat Stats", width=800, height=150, offset_x=0, offset_y=GRID_HEIGHT+210)
        
        self.__root_window = root_window
        self.__network_manager = network_manager
        self.__resource_manager = resource_manager
        self.__left_character = left_character
        self.__right_character = right_character
        
        # Create main frame with dark background
        self.__main_frame = tk.Frame(self._window, bg="#2E2E2E")
        self.__main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create two-column layout
        width = 800
        self.__left_frame = tk.Frame(self.__main_frame, bg="#2E2E2E", width=width//2)
        self.__left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.__left_frame.pack_propagate(False)
        
        self.__right_frame = tk.Frame(self.__main_frame, bg="#2E2E2E", width=width//2)
        self.__right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.__right_frame.pack_propagate(False)
        
        # Create panels
        self.__left_panel = self.__create_stat_panel(self.__left_frame, "PLAYER")
        self.__right_panel = self.__create_stat_panel(self.__right_frame, "OPPONENT")
        
        # Update panels with initial data
        if left_character:
            self.__update_panel(self.__left_panel, left_character)
        if right_character:
            self.__update_panel(self.__right_panel, right_character)
    
    def __create_stat_panel(self, parent_frame, panel_type):
        """Create a panel for character stats"""
        # Create the main panel frame
        panel_frame = tk.Frame(parent_frame, bg="#383838", bd=2, relief=tk.RIDGE)
        panel_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create HP section
        hp_label = tk.Label(
            panel_frame,
            text="HP:",
            font=("Arial", 10, "bold"),
            fg="white",
            bg="#383838",
            anchor=tk.W,
            padx=5,
            pady=2
        )
        hp_label.pack(fill=tk.X)
        
        # Create health bar
        health_bar = tk.Canvas(
            panel_frame,
            height=20,
            width=parent_frame.winfo_width(),
            bg="#444444",
            highlightthickness=0
        )
        health_bar.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Create attack section
        attack_frame = tk.Frame(panel_frame, bg="#383838")
        attack_frame.pack(fill=tk.X, padx=5, pady=2)
        
        attack_label = tk.Label(
            attack_frame,
            text="Attack:",
            font=("Arial", 10, "bold"),
            fg="white",
            bg="#383838"
        )
        attack_label.pack(side=tk.LEFT)
        
        attack_value = tk.Label(
            attack_frame,
            text="--",
            font=("Arial", 10, "bold"),
            fg="#FFCC00",
            bg="#383838"
        )
        attack_value.pack(side=tk.RIGHT)
        
        # Special cooldown section
        cooldown_frame = tk.Frame(panel_frame, bg="#383838")
        cooldown_frame.pack(fill=tk.X, padx=5, pady=2)
        
        cooldown_label = tk.Label(
            cooldown_frame,
            text="Special:",
            font=("Arial", 10, "bold"),
            fg="white",
            bg="#383838"
        )
        cooldown_label.pack(side=tk.LEFT)
        
        cooldown_value = tk.Label(
            cooldown_frame,
            text="Ready",
            font=("Arial", 10, "bold"),
            fg="#00FF00",
            bg="#383838"
        )
        cooldown_value.pack(side=tk.RIGHT)
        
        # Character name at the bottom
        name_frame = tk.Frame(panel_frame, bg="#555555")
        name_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        name_label = tk.Label(
            name_frame,
            text="No " + panel_type,
            font=("Arial", 9),
            fg="white",
            bg="#555555",
            padx=5,
            pady=2
        )
        name_label.pack(fill=tk.X)
        
        # Return components
        return {
            'frame': panel_frame,
            'health_bar': health_bar,
            'attack_value': attack_value,
            'cooldown_value': cooldown_value,
            'name_label': name_label
        }
    
    def update_characters(self, left_character: dict, right_character: dict):
        """Update character stats in both panels"""
        if left_character:
            self.__left_character = left_character
            self.__update_panel(self.__left_panel, left_character)
        
        if right_character:
            self.__right_character = right_character
            self.__update_panel(self.__right_panel, right_character)
    
    def __update_panel(self, panel: dict, stats: dict) -> None:
        """Update a panel with character stats"""
        if not panel:
            return
        
        # Update character name
        if 'name' in stats:
            panel['name_label'].config(text=stats['name'])
        
        # Update health bar
        if 'hp' in stats and 'max_hp' in stats:
            hp = stats['hp']
            max_hp = stats['max_hp']
            health_pct = hp / max_hp if max_hp > 0 else 0
            
            # Clear existing health bar
            health_bar = panel['health_bar']
            health_bar.delete("all")
            
            # Draw background
            health_bar.create_rectangle(
                0, 0, health_bar.winfo_width(), health_bar.winfo_height(),
                fill="#444444", outline=""
            )
            
            # Draw health bar
            bar_width = int(health_bar.winfo_width() * health_pct)
            
            # Choose color based on health percentage
            if health_pct > 0.5:
                color = "#00CC00"  # Green
            elif health_pct > 0.25:
                color = "#FFCC00"  # Yellow
            else:
                color = "#FF3333"  # Red
            
            health_bar.create_rectangle(
                0, 0, bar_width, health_bar.winfo_height(),
                fill=color, outline=""
            )
            
            # Draw health text
            health_bar.create_text(
                health_bar.winfo_width() // 2,
                health_bar.winfo_height() // 2,
                text=f"{hp}/{max_hp}",
                fill="white",
                font=("Arial", 10, "bold")
            )
        
        # Update attack value
        if 'attack' in stats:
            panel['attack_value'].config(text=str(stats['attack']))
        
        # Update special cooldown
        if 'special_cooldown' in stats:
            cooldown = stats['special_cooldown']
            
            if cooldown is None or cooldown <= 0:
                # Ready
                panel['cooldown_value'].config(text="Ready", fg="#00FF00")
            else:
                # On cooldown
                panel['cooldown_value'].config(text=f"{cooldown}s", fg="#FF6600")
    
    def run(self):
        """Run the window main loop"""
        self._window.mainloop()


class TimerWindow(Window):
    """
    Window for displaying the match timer during combat sessions.
    
    Shows a countdown timer for the battle with colored time indicators
    
    The timer helps players track the remaining duration of a combat match.
    """
    
    def __init__(self, root_window: tk.Tk, network_manager: NetworkManager, 
                 time_str: str = "03:00", is_match_over: bool = False) -> None:
        super().__init__(root_window, title="Match Timer", width=400, height=50, offset_x=0, offset_y=30)
        
        self.__root_window = root_window
        self.__network_manager = network_manager
        self.__time_str = time_str
        self.__is_match_over = is_match_over
        
        # Create main frame with dark background
        self.__main_frame = tk.Frame(self._window, bg="#2E2E2E")
        self.__main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create timer label
        self.__timer_label = tk.Label(
            self.__main_frame,
            text=time_str,
            font=("Arial", 24, "bold"),
            fg="#FFFFFF",
            bg="#2E2E2E"
        )
        self.__timer_label.pack(pady=5)
        
        # Update timer display
        self.update_timer(time_str, is_match_over)
    
    def update_timer(self, time_str: str, is_match_over: bool) -> None:
        """Update the timer display"""
        self.__time_str = time_str
        self.__is_match_over = is_match_over
        
        # Update timer text
        self.__timer_label.config(text=time_str)
        
        # Change color if time is running out
        if not is_match_over:
            time_parts = time_str.split(":")
            minutes = int(time_parts[0])
            seconds = int(time_parts[1])
            
            if minutes == 0 and seconds <= 30:
                # Less than 30 seconds - red
                self.__timer_label.config(fg="#FF3333")
            elif minutes == 0 and seconds <= 60:
                # Less than 1 minute - yellow
                self.__timer_label.config(fg="#FFCC00")
            else:
                # Normal - white
                self.__timer_label.config(fg="#FFFFFF")
        else:
            # Match is over
            self.__timer_label.config(fg="#FF0000", text="TIME'S UP!")
    
    def run(self):
        """Run the window main loop"""
        self._window.mainloop()


class CombatResultWindow(Window):
    """
    Window for displaying the result of a combat match.
    
    This window appears after a combat match concludes.
    """
    
    def __init__(self, root_window: tk.Tk, network_manager: NetworkManager, 
                 fighter_data: dict, result_type: str = "win") -> None:
        # Set window title based on result
        title = "Victory" if result_type == "win" else "Defeat"
        super().__init__(root_window, title=f"Combat {title}", width=400, height=350, offset_x=0, offset_y=0)
        
        self.__root_window = root_window
        self.__network_manager = network_manager
        self.__fighter_data = fighter_data
        self.__result_type = result_type
        
        # Configure colors based on result
        if result_type == "win":
            self.__header_color = "#FFD700"
            self.__header_text = "VICTORY!"
            self.__hp_color = "#00FF00"
            self.__bg_accent = "#2E2E2E"
        else: # losing colors
            self.__header_color = "#FF5555"
            self.__header_text = "DEFEAT!"
            self.__hp_color = "#FF9900"
            self.__bg_accent = "#3A2E2E"
        
        # Set window properties
        self._window.configure(bg="#1E1E1E")
        
        # Center the window on screen
        ws = self._window.winfo_screenwidth()
        hs = self._window.winfo_screenheight()
        x = (ws - 400) // 2
        y = (hs - 350) // 2
        self._window.geometry(f"400x350+{x}+{y}")
        
        # Prevent closing with X button
        self._window.protocol("WM_DELETE_WINDOW", lambda: None)
        
        self.__create_widgets()
        
        # Bind Return key
        self._window.bind("<Return>", lambda event: self.__on_return())
        
        # Force focus to this window
        self._window.focus_force()
        
        # Make window stay on top
        self._window.attributes("-topmost", True)
    
    def __create_widgets(self):
        """Create all window widgets based on result type"""
        # Create main frame
        main_frame = tk.Frame(self._window, bg="#1E1E1E")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create header label
        header_label = tk.Label(
            main_frame,
            text=self.__header_text,
            font=("Arial", 24, "bold"),
            fg=self.__header_color,
            bg="#1E1E1E"
        )
        header_label.pack(pady=(10, 20))
        
        # Create fighter info frame
        info_frame = tk.Frame(main_frame, bg=self.__bg_accent, relief=tk.RIDGE, bd=2)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Get fighter info
        fighter_name = self.__fighter_data.get("name", "Unknown Fighter")
        fighter_hp = self.__fighter_data.get("hp", 0)
        fighter_max_hp = self.__fighter_data.get("max_hp", 100)
        
        # Fighter label text depends on result
        fighter_prefix = "Victor" if self.__result_type == "win" else "Fighter"
        
        # Fighter name
        name_label = tk.Label(
            info_frame,
            text=f"{fighter_prefix}: {fighter_name}",
            font=("Arial", 16, "bold"),
            fg="white",
            bg=self.__bg_accent
        )
        name_label.pack(pady=(20, 10))
        
        # Fighter health
        health_label = tk.Label(
            info_frame,
            text=f"Remaining HP: {fighter_hp}/{fighter_max_hp}",
            font=("Arial", 14),
            fg=self.__hp_color,
            bg=self.__bg_accent
        )
        health_label.pack(pady=10)
        
        # Add result-specific message
        if self.__result_type == "win":
            message = "Congratulations on your victory!"
        else:
            message = "Better luck next time..."
            
        message_label = tk.Label(
            info_frame,
            text=message,
            font=("Arial", 12, "italic"),
            fg="#CCCCCC",
            bg=self.__bg_accent
        )
        message_label.pack(pady=15)
        
        # Return instruction
        return_frame = tk.Frame(main_frame, bg="#1E1E1E")
        return_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 0))
        
        return_label = tk.Label(
            return_frame,
            text="Press [Return] key to continue",
            font=("Arial", 10, "italic"),
            fg="#CCCCCC",
            bg="#1E1E1E"
        )
        return_label.pack(side=tk.RIGHT)
        
        # Also create a visible button for better visibility
        return_button = tk.Button(
            main_frame,
            text="Continue",
            command=self.__on_return,
            bg="#444444",
            fg="white",
            padx=10,
            pady=5
        )
        return_button.pack(side=tk.BOTTOM, pady=10)
    
    def __on_return(self):
        """Handle return button press or Return key"""
        # Send message back to original sender to trigger callback
        self.__network_manager.send({
            'combat_result_return': True,
            'result_type': self.__result_type
        })
        
        # Close the window
        self._window.destroy()
    
    def run(self):
        """Run the window main loop"""
        self._window.mainloop()
# ---------------------------------------------------------------------------------

class MagicalKeyWindow(Window):
    """Window that shows a potion being poured over a key to make it magical"""
    
    def __init__(self, root_window: tk.Tk, network_manager, resource_manager) -> None:
        super().__init__(root_window, title="Magical Key Transformation", 
                         width=400, height=300, offset_x=0, offset_y=0)
        
        self.__root_window = root_window
        self.__network_manager = network_manager
        self.__resource_manager = resource_manager
        self.__potion_types = ["Fire Resistance", "Water Breathing", "Invisibility", "Strength", "Night Vision"]
        self.__potion_colors = {
            "Fire Resistance": "#d23f48",
            "Water Breathing": "#47cfcf", 
            "Invisibility": "#69dd4e",
            "Strength": "#fbc832",
            "Night Vision": "#ab3fd5"
        }
        self.__potion_images = {
            "Fire Resistance": "image/tile/utility/redPotion.png",
            "Water Breathing": "image/tile/utility/bluePotion.png",
            "Invisibility": "image/tile/utility/greenPotion.png",
            "Strength": "image/tile/utility/yellowPotion.png",
            "Night Vision": "image/tile/utility/purplePotion.png"
        }
        self.__current_potion_index = 0
        self.__image_refs = []
        self.__animation_step = 0
        self.__animation_complete = False
        self.__potion_angle = 0
        self.__potion_id = 0
        self.__rotating = False
        self.__load_current_potion()

        self.__canvas = tk.Canvas(self._window, width=400, height=300, bg="#424242")
        self.__canvas.pack(fill="both", expand=True)
        
        self._window.bind("<space>", self.__pour_potion)
        self._window.bind("<Return>", self.__on_return)
        self._window.focus_set()
        
        self.__draw_initial_scene()
        
    def __load_current_potion(self):
        """Load the current potion image based on the current index"""
        current_potion = self.__potion_types[self.__current_potion_index]
        image_path = self.__potion_images[current_potion]
        self.__potion_image = Image.open(get_resource_path(image_path)).resize((40, 40), Image.Resampling.NEAREST)

    def __draw_initial_scene(self):
        """Draw the initial scene with key and potion"""
        self.__canvas.create_text(200, 30, text="Press SPACE to pour the potions!", 
                                  fill="white", font=("Arial", 14))
        
        # Draw key image
        try:
            key_img = Image.open(get_resource_path("image/tile/utility/boringKey.png"))
            key_img = key_img.resize((20, 55), Image.Resampling.NEAREST).rotate(-45, expand=True)
            key_photo = ImageTk.PhotoImage(key_img)
            self.__canvas.create_image(200, 200, image=key_photo)
            self.__image_refs.append(key_photo)
        except Exception as e:
            self.__canvas.create_rectangle(150, 150, 250, 190, fill="yellow", outline="gold")
            self.__canvas.create_text(200, 170, text="KEY", fill="black")
        
        # Draw potion image, colored based on potion type
        try:
            potion_photo = ImageTk.PhotoImage(self.__potion_image)
            self.__potion_id = self.__canvas.create_image(200, 85, image=potion_photo)
            self.__image_refs.append(potion_photo)
        except Exception as e:
            current_potion = self.__potion_types[self.__current_potion_index]
            potion_color = self.__potion_colors.get(current_potion, "#fbc832")
            self.__canvas.create_rectangle(180, 70, 220, 120, fill=potion_color, outline="black")
            self.__canvas.create_rectangle(195, 50, 205, 70, fill="brown", outline="black")
        
        
    def __pour_potion(self, event):
        """Begin the pouring animation"""
        if not self.__animation_complete and not self.__rotating:
            self.__rotating = True
            self.__rotate_potion()
            
    def __rotate_potion(self):
        """Rotate the potion bottle gradually"""
        if self.__potion_angle < 184:
            rotated_img = self.__potion_image.rotate(self.__potion_angle, expand=True)
            rotated_photo = ImageTk.PhotoImage(rotated_img)
            
            self.__canvas.itemconfig(self.__potion_id, image=rotated_photo)
            self.__image_refs.append(rotated_photo)
            self.__potion_angle += 15
            
            self._window.after(50, self.__rotate_potion)
        else:
            self.__rotating = False
            self.__animate_pouring()

    def __animate_pouring(self):
        """Animate the potion being poured"""
        if self.__animation_step < 10:
            self.__canvas.delete("pouring")
            
            current_potion = self.__potion_types[self.__current_potion_index]
            potion_color = self.__potion_colors.get(current_potion, "#fbc832")

            y_offset = self.__animation_step * 10
            self.__canvas.create_rectangle(
                198, 110 + y_offset, 
                202, 110, 
                fill=potion_color, 
                outline="black", 
                tags="pouring"
            )
            
            self.__animation_step += 1
            self._window.after(100, self.__animate_pouring)
        else:
            self.__move_to_next_potion()

    def __move_to_next_potion(self):
        """Move to the next potion in the sequence"""
        self.__current_potion_index += 1
        self.__animation_step = 0
        self.__potion_angle = 0
        self.__rotating = False
        
        if self.__current_potion_index < len(self.__potion_types):
            self.__load_current_potion()
            self.__draw_next_potion()
        else:
            self.__transform_key()

    def __draw_next_potion(self):
        """Draw the next potion after the previous one finished pouring"""
        self.__canvas.delete("pouring")
        
        try:
            potion_photo = ImageTk.PhotoImage(self.__potion_image)
            self.__canvas.itemconfig(self.__potion_id, image=potion_photo)
            self.__image_refs.append(potion_photo)
        except Exception as e:
            pass
        
        self.__canvas.coords(self.__potion_id, 200, 85)
        self._window.after(500, lambda: self.__pour_potion(None))
            
    def __transform_key(self):
        """Transform the key into a magical key"""
        def flash_on():
            self.__canvas.config(bg="white")
            self._window.after(200, flash_off)
            
        def flash_off():
            self.__canvas.config(bg="#424242")
            self.__show_transformed_key()
        
        flash_on()
        
    def __show_transformed_key(self):
        """Show the transformed magical key"""
        self.__canvas.delete("all")
        
        self.__canvas.create_text(200, 30, text="Key transformed with all Magical Potions!", 
                                  fill="white", font=("Arial", 14))
        self.__canvas.create_text(200, 60, text="You can now unlock the Chest!", 
                                  fill="white", font=("Arial", 14))
        self.__canvas.create_text(200, 250, text="Press ENTER to continue", 
                                  fill="white", font=("Arial", 12))
        
        try:
            key_img = Image.open(get_resource_path("image/tile/utility/magicalKey.png"))
            key_img = key_img.resize((20, 55), Image.Resampling.NEAREST).rotate(-45, expand=True)
            key_photo = ImageTk.PhotoImage(key_img)
            self.__canvas.create_image(200, 140, image=key_photo)
            self.__image_refs.append(key_photo)
        except Exception as e:
            self.__canvas.create_oval(140, 140, 260, 200, fill="#fbc832", outline="")
            self.__canvas.create_rectangle(150, 150, 250, 190, fill="gold", outline="white")
            self.__canvas.create_text(200, 170, text="MAGICAL KEY", fill="black")
        
        self.__animation_complete = True
        
    def __on_return(self, event):
        """Close the window and notify game of key transformation"""
        if self.__animation_complete:
            self.__network_manager.send({
                'action': 'transform_key',
            })
            self._window.destroy()
    
    def run(self):
        """Start the window's main loop"""
        self.__root_window.after(0, self._window.mainloop)


if __name__ == '__main__':
    start()
