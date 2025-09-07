import os
import traceback
from glob import glob
from pathlib import Path
from pprint import pprint
from typing import Any, TYPE_CHECKING

from PIL import Image

from ..coord import Coord
from ..resources import get_resource_path, find_resource_path
from ..message import Message, SenderInterface
from ..keybinds import KeybindInterface
from ..util import get_all_subclasses, get_subclasses_from_folders

if TYPE_CHECKING:
    from Player import HumanPlayer
    from tiles.map_objects import Door

TILE_WIDTH = 16
TILE_HEIGHT = 16

class GameEvent:
    """ An event that occurs in the game that objects may wish to be notified about. """
    def __init__(self, event_type, data=None) -> None:
        self.event_type = event_type
        self.data = data or {}

class Observer:
    def update_on_notification(self, event):
        """Called by the subject (publisher) to push updates to this observer."""
        raise NotImplementedError

class Subject:
    def __init__(self):
        self._observers: list[Observer] = []

    def attach(self, observer: Observer):
        self._observers.append(observer)

    def notify(self, event):
        for obs in self._observers:
            obs.update_on_notification(event)

    def notify_each(self, data):
        """Notify each observer with a different piece of data."""
        #ssert len(data) == len(self._observers), f"Expected {len(self._observers)} pieces of data, but got {len(data)}"
        for observer, data_piece in zip(self._observers, data):
            observer.update_on_notification(data_piece)
    
    def notify_each_by_type(self, data, type_):
        """Notify each observer with a different piece of data."""
        observers_of_type = [obs for obs in self._observers if isinstance(obs, type_)]
        #assert len(data) == len(observers_of_type), f"Expected {len(observers_of_type)} pieces of data, but got {len(data)}"
        for observer, data_piece in zip(observers_of_type, data):
            if isinstance(observer, type_):
                observer.update_on_notification(data_piece)

class Exit:
    """ A class representing an exit from a map object. """

    def __init__(self, door: 'Door', door_position: Coord, linked_map: str = "", is_main_entrance: bool = False, group_number: int = 0) -> None:
        self.door: Door = door
        self.door_position: Coord = door_position
        self.linked_map: str = linked_map
        self.is_main_entrance: bool = is_main_entrance
        self.group_number: int = group_number
    
    def __repr__(self) -> str:
        return f'Exit(door:{self.door}, door_position:{self.door_position}, linked_map:{self.linked_map}, is_main_entrance:{self.is_main_entrance}, group_number:{self.group_number})'

class MapObject(SenderInterface, KeybindInterface):
    """ A class representing an object on the map. An object may consist of multiple tiles on the grid. """

    def __init__(self, image_name: str, passable: bool, z_index: int = 0) -> None:
        """ Initializes the map object.
        
        Arguments:
            image_name: str -- the name of the image file for the object
            passable: bool -- whether the object is passable (i.e., if players can walk through it)
            z_index: int -- the z-index of the object (higher z-index objects are drawn on top of lower z-index objects)
        """
        self._image_name: str = image_name
        self.__passable: bool = passable
        self.__z_index: int = z_index
        self._position : Coord = Coord(0, 0)

        self.__tilemap, self.num_rows, self.num_cols = self._get_tilemap()

        KeybindInterface.__init__(self)

    def get_image_name(self) -> str:
        """ Returns the name of the image file for the object. """
        return self._image_name

    def set_image_name(self, image_name: str) -> None:
        """ Sets the name of the image file for the object. """
        self._image_name = image_name

    def get_name(self) -> str:
        """ Returns the name of the object. """
        return self._image_name

    def get_position(self) -> Coord:
        """ Returns the position of the object on the map. """
        return self._position
    
    def set_position(self, position: Coord) -> None:
        """ Sets the position of the object on the map. """
        self._position = position

    def is_passable(self) -> bool:
        """ Returns whether the object is passable. """
        return self.__passable
    
    def set_passability(self, passable: bool) -> None:
        """ Sets the passability of the object. """
        self.__passable = passable

    def get_z_index(self) -> int:
        """ Returns the z-index of the object. """
        return self.__z_index
    
    def set_z_index(self, index: int) -> None:
        """ Updates the z-index of the object. """
        self.__z_index = index

    def get_exits(self) -> list[Exit]:
        """ Returns a list of exits from the object.
        A regular object has no exits, so this method should be overridden by subclasses that have exits.
        """
        return []

    def __repr__(self) -> str:
        """ Returns a string representation of the object. """
        return f'MapObject(image:{self._image_name}, type:{type(self)}, passable:{self.__passable})'

    def at(self, coord: Coord) -> "MapObject":
        """ Returns the object at the given coordinate. """
        assert type(coord) == Coord
        assert 0 <= coord.y < self.num_rows, f"Invalid y coordinate {coord.y} for {self._image_name}"
        assert 0 <= coord.x < self.num_cols, f"Invalid x coordinate {coord.x} for {self._image_name}"
        return self.__tilemap[coord.y][coord.x]
    
    def player_entered(self, player: "HumanPlayer") -> list[Message]:
        """ Called when a player enters the object's tile(s). """
        return []

    def player_exited(self, player: "HumanPlayer") -> list[Message]:
        """ Called when a player leaves the object's tile(s). """
        return []

    def player_interacted(self, player: "HumanPlayer") -> list[Message]:
        """ Called when a player interacts with the object's tile(s). """
        return []

    def update(self) -> list[Message]:
        """ Called every second. """
        return []

    def _get_image_size(self) -> tuple[int, int]:
        """ Returns the size of the image for the object. """
        # load the image with PIL

        image_fname = get_resource_path(f'image/{self._image_name}.png')
        if not os.path.exists(image_fname):
            print("Image not found:", image_fname)
            return 1, 1
        
        image = Image.open(image_fname)
        num_cols, num_rows = image.size[0] // TILE_WIDTH, image.size[1] // TILE_HEIGHT
        return num_rows, num_cols

    def _get_tilemap(self) -> tuple[list[list[Any]], int, int]:
        """ Returns the tilemap for the object with the given image name. """

        if len(self._image_name) == 0:
            return [[]], 1, 1
        
        num_rows, num_cols = self._get_image_size()
        assert num_rows > 0 and num_cols > 0, f"Invalid image size for {self._image_name}: {num_rows}x{num_cols}"
        tilemap: list[list[MapObject]] = [ [ self for _ in range(num_cols) ] for _ in range(num_rows) ]
        return tilemap, num_rows, num_cols

    OBJECTS: dict[str, 'MapObject'] = {}

    @staticmethod
    def load_object(image_path: Path, map_object_classes) -> bool:
        tile_type = image_path.parent.name.replace("_", "") # e.g. tile/building/house1.png -> building
        image_name = image_path.stem # e.g. tile/building/house1.png -> house1
        if image_name in MapObject.OBJECTS:
            #print("Already exists.")
            return True
        #print("Loading", image)

        image_class_name = image_name.replace("_", "")
        for map_object_classname, map_object_class in map_object_classes.items():
            if map_object_classname.lower() == image_class_name.lower():
                tile_type = map_object_classname
                tile_cls = map_object_classes[tile_type]
                #print("Matched", tile_type, "to", image)
                break
        else:
            for map_object_classname, map_object_class in map_object_classes.items():
                if map_object_classname.lower() == tile_type.lower():
                    tile_type = map_object_classname
                    tile_cls = map_object_classes[tile_type]
                    #print("Matched", tile_type, "to", image)
                    break
            else:
                print("Warning: Could not find tile type for", image_path, "with type", tile_type.lower()) #, "; available types:", map_object_classes.keys())
                tile_cls = MapObject
                #print("That means you can't use MapObject.get_obj() with this image.")
                #return False
                #raise ValueError(f"Could not find tile type for {image} with type {tile_type.lower()}; available types: {map_object_classes.keys()}")
        
        try:
            if tile_cls == MapObject:
                MapObject.OBJECTS[image_name.lower()] = tile_cls(image_name, passable=False)
            else:
                MapObject.OBJECTS[image_name.lower()] = tile_cls(image_name)
        except:
            print(f"Could not instantiate {tile_cls} with {image_name}: {traceback.format_exc()}")
            #pprint('\n'.join(traceback.format_stack()))
            return False
            #raise ValueError(f"Could not instantiate {tile_cls} with {image_name}: {traceback.format_exc()}")
        return True

    @staticmethod
    def load_objects(map_object_classes=None) -> None:
        """ Load all map objects from the resources/image/tile directory. Should only be called once."""
        if map_object_classes is None:
            map_object_classes = get_subclasses_from_folders([MapObject], verbose=False)[MapObject]

        tile_dir = get_resource_path('image/tile/')
        mud_folder_images = glob(os.path.join(tile_dir, "*", "*.png"))
        try:
            ext_folder_dir = get_resource_path('image/tile', ext_folder=True)
            ext_folder_images = glob(os.path.join(ext_folder_dir, "*", "*.png"))
        except:
            ext_folder_images = []
        for image in mud_folder_images + ext_folder_images:
            MapObject.load_object(Path(image), map_object_classes)
    
    @staticmethod
    def get_obj(image_name: str) -> 'MapObject':
        """ Get the map object with the given image name. """
        if image_name.lower() not in MapObject.OBJECTS:
            map_object_classes = get_all_subclasses(MapObject)
            #print("Trying to load", image_name.lower())
            result = MapObject.load_object(find_resource_path(image_name.lower()), map_object_classes)
            if not result:
                raise ValueError(f"Map object with image name {image_name.lower()} not found.")
        return MapObject.OBJECTS[image_name.lower()]

class Tile:
    """ A class representing a single tile on the grid. """

    def __init__(self, obj: MapObject, offset_from_parent: Coord) -> None:
        """ Initializes the tile.

        Arguments:
            obj: MapObject -- the object at this tile
            offset_from_parent: Coord -- the offset of this tile from the parent object
        """
        self.__obj: MapObject = obj
        self.__offset_from_parent: Coord = offset_from_parent
    
    def get_obj(self) -> MapObject:
        """ Returns the object of which this tile is a part. """
        return self.__obj

    def get_image_name(self) -> str:
        """ Returns the name of the image file for the object at this tile.
            Only returns the image if this tile represents the top-left corner of the object.
        """

        if self.__offset_from_parent.y == 0 and self.__offset_from_parent.x == 0:
            return self.__obj.get_image_name()
        return ''
    
    def is_passable(self) -> bool:
        """ Returns whether the object at this tile is passable. """
        return self.__obj.at(self.__offset_from_parent).is_passable()

    def get_z_index(self) -> int:
        """ Returns the z-index of the object at this tile. """
        return self.__obj.get_z_index()
    
    def player_entered(self, player) -> list[Message]:
        """ Called when a player enters the tile. """
        return self.__obj.at(self.__offset_from_parent).player_entered(player)
    
    def player_exited(self, player) -> list[Message]:
        """ Called when a player enters the tile. """
        return self.__obj.at(self.__offset_from_parent).player_exited(player)
    
    def player_interacted(self, player) -> list[Message]:
        """ Called when a player interacts with the tile. """
        return self.__obj.at(self.__offset_from_parent).player_interacted(player)
