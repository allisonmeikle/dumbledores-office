
import traceback
from abc import ABC
from typing import Any

from ..coord import Coord
from ..tiles.base import MapObject, Exit
from ..tiles.map_objects import Door

# maps image name to door position (in terms of rows and columns, 16px each.)
building_info = {
    'green_house_large': Coord(6, 3),
    'purple_house_large': Coord(6, 3),
    'green_house_small': Coord(4, 1),
    'purple_house_small': Coord(4, 1),
    'shop1': Coord(4, 1),
    'shop2': Coord(2, 1),
    'shop3': Coord(4, 1),
    'shop4': Coord(3, 1),
    'shop5': Coord(2, 1),
    'shop6': Coord(3, 1),
    'shop7': Coord(2, 1),
    'shop8': Coord(6, 1),
    'stonehouse': Coord(4, 4),
    'hayshop': Coord(6, 4),
    'hayhouse': Coord(4, 3),
    'circus_tent': Coord(3, 1),
}

group_building_info = {

    ## urban city
    4: Coord(-1, 1),
    20: Coord(-1, 5),
    27: Coord(-1, 2),
    44: Coord(-1, 1),
    45: Coord(-1, 2),
    61: Coord(-1, 3),
    62: Coord(-1, 2),
    122: Coord(-1, 1),

    ## old city
    9: Coord(-1, 4),
    14: Coord(-1, 3),
    18: Coord(-1, 3),
    28: Coord(-1, 3),
    50: Coord(-1, 3),
    54: Coord(-1, 3),
    72: Coord(-1, 2),
    98: Coord(-1, 1),

    ## city's edge
    2: Coord(-1, 3),
    6: Coord(-1, 0),
    23: Coord(-1, 1),
    48: Coord(-1, 2),
    69: Coord(-1, 1),
    95: Coord(-1, 3),

    ## cyber city
    11: Coord(-1, 1),
    30: Coord(-1, 1),
    5: Coord(-1, 1),
    7: Coord(-1, 0),
    43: Coord(-1, 1),
    57: Coord(-1, 1),
    58: Coord(-1, 1),

    ## medieval
    126: Coord(-1, 3),
    8: Coord(-1, 5),
    19: Coord(-1, 1),
    47: Coord(-1, 4),
    26: Coord(-1, 2),
    14: Coord(-1, 3),
    53: Coord(-1, 3),
    32: Coord(-1, 7),
    90: Coord(-1, 1),
    73: Coord(-1, 1),

    ## casino
    1: Coord(-1, 0),
    52: Coord(-1, 0),
    13: Coord(-1, 0),
    63: Coord(-1, 0),
    25: Coord(-1, 0),
    34: Coord(-1, 0),

    ## rural
    10: Coord(-1, 0),
    140: Coord(-1, 0),
    15: Coord(-1, 3),
    17: Coord(-1, 2),
    37: Coord(-1, 2),

    3: Coord(-1, 3),
    12: Coord(-1, 3),
    29: Coord(-1, 3),
    39: Coord(-1, 3),
    41: Coord(-1, 3),
    46: Coord(-1, 3),
    97: Coord(-1, 3),

    ##
    1997: Coord(-1, 1),
}

building_infos = {}
building_infos.update(building_info)
building_infos.update(group_building_info)

class Building(MapObject, ABC):
    def __init__(self, image_name: str, door_position = Coord(0, 0), linked_room_str: str = "") -> None:
        #print("Building constructor called with args:", image_name, door_position, linked_room_str)
        #print("From:", traceback.extract_stack())
        if image_name in building_infos:
            door_position = building_infos[image_name]
        self._door = self._get_door()
        #print(self.__class__.__name__, "door position(B)", door_position)
        self._door_position = door_position
        self._linked_room_str: str = linked_room_str
        super().__init__(f'tile/building/{image_name}', passable=False)
    
    def _get_door(self):
        return Door('empty')

    def get_door_position(self) -> Coord:
        return self._door_position

    def get_exits(self) -> list[Exit]:
        return [Exit(self._door, self._position + self._door_position, self._linked_room_str)]

    def _get_tilemap(self) -> tuple[list[list[Any]], int, int]:
        tilemap, num_rows, num_cols = super()._get_tilemap()

        door_position_y = self._door_position.y
        if door_position_y == -1:
            door_position_y = num_rows - 1

        # make door passable
        #print(self.__class__.__name__, "Making door passable at", door_position_y, self._door_position.x)
        tilemap[door_position_y][self._door_position.x] = self._door
        return tilemap, num_rows, num_cols

for image_name, door_position in building_info.items():
    name = ''.join([x.capitalize() for x in image_name.split('_')])
    building_cls = type(name, (Building,), {
        '__init__': lambda self, image_name=image_name, door_position=door_position, linked_room_str = "": Building.__init__(self, image_name, door_position=door_position, linked_room_str=linked_room_str),
        '__module__': __name__  # or another desired module name
    })
    globals()[name] = building_cls
    #print(name, "door position", globals()[name]().get_door_position())

for group_number, door_position in group_building_info.items():
    name = f'Group{group_number}'
    building_cls = type(name, (Building,), {
        '__init__': lambda self, image_name=f'group{group_number}', door_position=door_position, linked_room_str="": Building.__init__(self, image_name, door_position=door_position, linked_room_str=linked_room_str),
        '__module__': __name__  # or another desired module name
    })
    globals()[name] = building_cls
    #print(name, "door position(A)", globals()[name]().get_door_position())

class GroupHouseMixin:
    def __init__(self, group_number):
        super().__init__()
        self.__group_number = group_number

    def get_exits(self) -> list[Exit]:       
        door_position_y = self._door_position.y
        if door_position_y == -1:
            num_rows, num_cols = self._get_image_size()
            door_position_y = num_rows - 1
        door_position = Coord(x=self._door_position.x, y=door_position_y)
        return [Exit(self._door, self._position + door_position, group_number=self.__group_number)]        

def make_group_house(group_number: int) -> Building:
    building_cls_name = f"Group{group_number}"
    building_cls = globals().get(building_cls_name)
    return type(f'GroupHouse{group_number}', (GroupHouseMixin, building_cls), {})(group_number=group_number)
