
from ..tiles.map_objects import Background
from ..maps.base import Map
from ..tiles.base import MapObject
from ..tiles.map_objects import Door
from ..tiles.buildings import *
from ..coord import Coord

class CyberCity(Map):
    def __init__(self) -> None:
        super().__init__(
            name='Cyber City',
            size=(17, 17),
            entry_point=Coord(8, 5),
            description='description here',
            background_tile_image='road2',
            background_music='blithe',
        )

    def get_objects(self) -> list[tuple[MapObject, Coord]]:
        objects = [
            (make_group_house(11), Coord(x=13, y=0)), ##
            (Background('lava'), Coord(x=0, y=13)),
            (Background('lava'), Coord(x=1, y=14)),
            (Background('lava'), Coord(x=2, y=15)),
            (Background('lava'), Coord(x=1, y=15)),
            (Background('lava'), Coord(x=0, y=14)),
            (Background('lava'), Coord(x=0, y=15)),
            (Background('lava'), Coord(x=3, y=16)),
            (Background('lava'), Coord(x=2, y=16)),
            (Background('lava'), Coord(x=1, y=16)),
            (make_group_house(7), Coord(x=0, y=16)), #
            (make_group_house(43), Coord(x=13, y=8)), #
            (make_group_house(5), Coord(x=6, y=0)), ##
            (make_group_house(57), Coord(x=8, y=6)), ##
            (make_group_house(30), Coord(x=1, y=1)), #
            (make_group_house(58), Coord(x=3, y=8)),
        ]

        door = Door('tube', linked_room="Trottier Town")
        objects.append((door, Coord(0, 0)))

        return objects

