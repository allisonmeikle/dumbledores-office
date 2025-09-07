import random
from ..coord import *
from ..maps.base import Map
from ..tiles.base import MapObject
from ..tiles.map_objects import *
from ..tiles.buildings import *
from ..maps.map_helper import *

class GrassTown(Map):
    def __init__(self) -> None:
        super().__init__(
            name="Grass Town",
            size=(25, 60),
            entry_point=Coord(1, 2),
            description="A quiet village with two rows of upload houses connected by tubes",
            background_tile_image="grass",
            background_music="blue_val",
        )

    def get_objects(self) -> list[tuple[MapObject, Coord]]:
        objects, tree_spaces = [], []
        random.seed(12)
        empty_spaces = [Rect(Coord(0, 0), Coord(24, 1)), 
                        Rect(Coord(0, 4), Coord(1, self._map_cols-1)),]
        fill_area(objects, MapObject.get_obj("tree_small_1"), Coord(0, self._map_cols-1), Coord(self._map_rows-1, self._map_cols-1))
        for i in range(self._map_rows-1):
            for j in range(self._map_cols-1):
                if any(r.top_left.y <= i <= r.bottom_right.y and r.top_left.x <= j <= r.bottom_right.x for r in empty_spaces):
                    if Coord(i, j) not in tree_spaces:
                        objects.append((MapObject.get_obj("tree_small_1"), Coord(i, j)))
                        tree_spaces.append(Coord(i, j))

        path = MapObject.get_obj("sand")
        houses = [GreenHouseLarge(linked_room_str="Upload House"), PurpleHouseLarge(linked_room_str="Upload House")]
        fill_area(objects, MapObject.get_obj("grass_left"), Coord(0, 2), Coord(self._map_rows, 2))
        fill_area(objects, MapObject.get_obj("grass_right"), Coord(0, 3), Coord(self._map_rows, 3))

        for i, gap in enumerate(range(10, 55, 10)):
            objects.append((houses[i % 2], Coord(2, gap)))
            objects.append((houses[i % 2], Coord(14, gap)))

        for x in [11, 22]:
            fill_area(objects, MapObject.get_obj("grass_up"), Coord(x, 4), Coord(x + 1, self._map_cols-1))
            fill_area(objects, MapObject.get_obj("grass_down"), Coord(x + 1, 4), Coord(x + 2, self._map_cols-1))
        for coord in [Coord(11, 3), Coord(12, 3), Coord(22, 3), Coord(23, 3)]:
            replace_object_at_coord(objects, coord, path)

        flowers = ["flower_large_red", "flower_large_yellow", "flower_small_red", "flower_large_blue"]
        flower_spaces = [Rect(Coord(4, 5), Coord(9, 8)), Rect(Coord(14, 5), Coord(20, 8))]
        
        for rect in flower_spaces:
            for i in range(rect.top_left.y, rect.bottom_right.y + 1):
                for j in range(rect.top_left.x, rect.bottom_right.x + 1):
                    if i == rect.top_left.y or i == rect.bottom_right.y or j == rect.top_left.x or j == rect.bottom_right.x:
                        objects.append((MapObject.get_obj("bush"), Coord(i, j)))
                    else:
                        objects.append((MapObject.get_obj(random.choice(flowers)), Coord(i, j)))
        
        first_bush_y = 17
        for y in range(first_bush_y, self._map_cols-1, 10):
            objects.append((MapObject.get_obj("red_bush"), Coord(7, y)))
            objects.append((MapObject.get_obj("blue_bush"), Coord(19, y)))
        door = Door('tube', linked_room="Trottier Town")
        objects.append((door, Coord(0, 2)))
        return objects
