import sys
import random

from ..coord import *
from ..maps.base import Map
from ..command import MenuCommand
from ..tiles.map_objects import *
from ..tiles.base import MapObject
from ..maps.map_helper import is_large_tree_area
from ..tiles.buildings import *

if any("server_remote" in arg for arg in sys.argv):
    from ..tiles.map_objects2 import *

class TellJokeCommand(MenuCommand):
    def execute(self, context: "Map", player: "HumanPlayer") -> list[Message]:
        num_jokes_told_to_player = player.get_state('num_jokes_received', 0)
        player.set_state('num_jokes_received', num_jokes_told_to_player+1)
        
        num_jokes_told = context.get_state('num_jokes_told', 0)
        context.set_state('num_jokes_told', num_jokes_told+1)
        
        return [ServerMessage(player, "Why did the scarecrow win an award? Because he was outstanding in his field!")]

class TrottierTown(Map):
    def __init__(self) -> None:
        super().__init__(
            name="Trottier Town",
            size=(40, 31),
            entry_point=Coord(19, 13), #60-6-2-15-9, 26),
            description="description here",
            background_tile_image='grass',
            background_music='blithe',
        )

    def get_objects(self) -> list[tuple[MapObject, Coord]]:
        objects: list[tuple[MapObject, Coord]] = []

        objects.extend([
            (Background('grass'), Coord(x=15, y=0)),
            (Background('grass'), Coord(x=15, y=1)),
            (Background('grass'), Coord(x=15, y=1)),
            (Background('grass'), Coord(x=15, y=2)),
            (Background('grass'), Coord(x=16, y=2)),
            (Background('grass'), Coord(x=16, y=4)),
            (Background('grass'), Coord(x=16, y=3)),
            (Background('grass'), Coord(x=17, y=4)),
            (Background('grass'), Coord(x=17, y=5)),
            (Background('grass'), Coord(x=17, y=6)),
            (Background('grass'), Coord(x=17, y=7)),
            (Background('grass'), Coord(x=17, y=8)),
            (Background('grass'), Coord(x=16, y=8)),
            (ExtDecor('signpost'), Coord(x=16, y=8)),
            (Door('empty', linked_room="Forest"), Coord(x=15, y=0)),
            (Sign('sign'), Coord(x=12, y=18)),
            (Background('road2'), Coord(x=0, y=17)),
            (Background('road2'), Coord(x=1, y=17)),
            (Background('road2'), Coord(x=2, y=17)),
            (Background('road2'), Coord(x=3, y=17)),
            (Background('road2'), Coord(x=4, y=17)),
            (Background('road2'), Coord(x=5, y=17)),
            (Background('road2'), Coord(x=6, y=17)),
            (Background('road2'), Coord(x=6, y=19)),
            (Background('road2'), Coord(x=5, y=19)),
            (Background('road2'), Coord(x=4, y=19)),
            (Background('road2'), Coord(x=4, y=19)),
            (Background('road2'), Coord(x=3, y=19)),
            (Background('road2'), Coord(x=3, y=19)),
            (Background('road2'), Coord(x=2, y=19)),
            (Background('road2'), Coord(x=1, y=19)),
            (Background('road2'), Coord(x=0, y=19)),
            (Background('road3'), Coord(x=6, y=18)),
            (Background('road3'), Coord(x=5, y=18)),
            (Background('road3'), Coord(x=4, y=18)),
            (Background('road3'), Coord(x=2, y=18)),
            (Background('road3'), Coord(x=1, y=18)),
            (Background('road3'), Coord(x=0, y=18)),
            (Background('road3'), Coord(x=3, y=18)),
            (ExtDecor('signpost'), Coord(x=6, y=16)),
            (Door('empty', linked_room="Urban City"), Coord(x=0, y=18)),
            (ExtDecor('signpost'), Coord(x=19, y=31)),
            (Background('grass2'), Coord(x=20, y=32)),
            (Background('grass3'), Coord(x=21, y=32)),
            (Background('grass_left'), Coord(x=20, y=33)),
            (Background('grass_left'), Coord(x=20, y=34)),
            (Background('grass_left'), Coord(x=20, y=35)),
            (Background('grass_left'), Coord(x=20, y=36)),
            (Background('grass_right'), Coord(x=21, y=33)),
            (Background('grass_right'), Coord(x=21, y=34)),
            (Background('grass_right'), Coord(x=21, y=35)),
            (Background('grass4'), Coord(x=20, y=37)),
            (Background('grass_left'), Coord(x=21, y=38)),
            (Background('grass_right'), Coord(x=22, y=38)),
            (Background('grass_right'), Coord(x=22, y=39)),
            (Background('grass3'), Coord(x=22, y=36)),
            (Background('grass_right'), Coord(x=22, y=37)),
            (Background('sand'), Coord(x=21, y=36)),
            (Background('sand'), Coord(x=21, y=37)),
            (Background('grass'), Coord(x=20, y=38)),
            (Background('grass'), Coord(x=20, y=39)),
            (Background('grass'), Coord(x=23, y=36)),
            (Background('grass'), Coord(x=23, y=37)),
            (Background('grass'), Coord(x=23, y=38)),
            (Background('grass'), Coord(x=23, y=39)),
            (ExtDecor('bush_spiky'), Coord(x=20, y=38)),
            (ExtDecor('bush'), Coord(x=23, y=36)),
            (Background('grass4'), Coord(x=21, y=39)),
            (Door('empty', linked_room="Rural"), Coord(x=22, y=39)),
            (Background('road2'), Coord(x=23, y=17)),
            (Background('road2'), Coord(x=24, y=17)),
            (Background('road2'), Coord(x=25, y=17)),
            (Background('road2'), Coord(x=27, y=17)),
            (Background('road2'), Coord(x=28, y=17)),
            (Background('road2'), Coord(x=29, y=17)),
            (Background('road2'), Coord(x=30, y=17)),
            (Background('road2'), Coord(x=29, y=17)),
            (Background('road2'), Coord(x=28, y=17)),
            (Background('road2'), Coord(x=26, y=17)),
            (Background('road2'), Coord(x=25, y=17)),
            (Background('road2'), Coord(x=25, y=18)),
            (Background('road2'), Coord(x=24, y=18)),
            (Background('road2'), Coord(x=23, y=18)),
            (Background('road2'), Coord(x=23, y=19)),
            (Background('road2'), Coord(x=24, y=19)),
            (Background('road2'), Coord(x=26, y=18)),
            (Background('road2'), Coord(x=27, y=18)),
            (Background('road2'), Coord(x=27, y=19)),
            (Background('road2'), Coord(x=28, y=19)),
            (Background('road2'), Coord(x=28, y=18)),
            (Background('road2'), Coord(x=28, y=19)),
            (Background('road2'), Coord(x=29, y=19)),
            (Background('road2'), Coord(x=29, y=18)),
            (Background('road2'), Coord(x=30, y=18)),
            (Background('road2'), Coord(x=30, y=19)),
            (Background('road3'), Coord(x=24, y=18)),
            (Background('road3'), Coord(x=27, y=18)),
            (Background('street3'), Coord(x=26, y=17)),
            (Background('street3'), Coord(x=29, y=19)),
            (Background('street3'), Coord(x=29, y=18)),
            (Background('street3'), Coord(x=30, y=18)),
            (Background('street3'), Coord(x=25, y=18)),
            (Background('street3'), Coord(x=23, y=17)),
            (Background('road3'), Coord(x=28, y=18)),
            (Background('road3'), Coord(x=26, y=18)),
            (Background('street5'), Coord(x=25, y=19)),
            (Background('street5'), Coord(x=26, y=19)),
            (Door('empty', linked_room="City Edge"), Coord(x=30, y=18)),
            (Background('stone'), Coord(x=7, y=31)),
            (Background('stone'), Coord(x=7, y=32)),
            (Background('stone'), Coord(x=7, y=33)),
            (Background('stone'), Coord(x=7, y=34)),
            (Background('stone'), Coord(x=7, y=35)),
            (Background('stone'), Coord(x=6, y=35)),
            (Background('stone'), Coord(x=6, y=36)),
            (Background('stone'), Coord(x=5, y=36)),
            (Background('stone'), Coord(x=5, y=37)),
            (Background('stone'), Coord(x=5, y=38)),
            (Background('stone'), Coord(x=4, y=39)),
            (Background('stone'), Coord(x=3, y=39)),
            (Background('stone'), Coord(x=4, y=38)),
            (Background('stone'), Coord(x=5, y=35)),
            (Background('stone'), Coord(x=6, y=34)),
            (Background('stone'), Coord(x=7, y=36)),
            (ExtDecor('signpost'), Coord(x=8, y=31)),
            #(ExtDecor('signpost'), Coord(x=25, y=26)),
            (ExtDecor('road_decor2'), Coord(x=2, y=19)),
            (Door('empty', linked_room="Medieval"), Coord(x=4, y=39)),
            (ExtDecor('signpost'), Coord(x=23, y=16)),
            (Background('cobblestone'), Coord(x=6, y=27)),
            (Background('cobblestone'), Coord(x=5, y=27)),
            (Background('cobblestone'), Coord(x=4, y=27)),
            (Background('cobblestone'), Coord(x=3, y=27)),
            (Background('cobblestone'), Coord(x=2, y=27)),
            (Background('cobblestone'), Coord(x=3, y=28)),
            (Background('cobblestone'), Coord(x=2, y=28)),
            (Background('cobblestone'), Coord(x=0, y=28)),
            (Background('cobblestone'), Coord(x=1, y=29)),
            (Background('cobblestone'), Coord(x=0, y=29)),
            (Background('cobblestone'), Coord(x=1, y=28)),
            (Background('cobblestone'), Coord(x=4, y=28)),
            (Background('cobblestone'), Coord(x=5, y=28)),
            (Background('cobblestone'), Coord(x=6, y=28)),
            (Door('empty', linked_room="Old City"), Coord(x=0, y=29)),
            (ExtDecor('signpost'), Coord(x=6, y=26)),
            (Background('road1'), Coord(x=23, y=9)),
            (Background('road1'), Coord(x=25, y=9)),
            (Background('road1'), Coord(x=26, y=9)),
            (Background('road1'), Coord(x=27, y=9)),
            (Background('road1'), Coord(x=29, y=9)),
            (Background('road1'), Coord(x=30, y=9)),
            (Background('road2'), Coord(x=23, y=10)),
            (Background('road2'), Coord(x=24, y=10)),
            (Background('road2'), Coord(x=27, y=10)),
            (Background('road2'), Coord(x=28, y=10)),
            (Background('road2'), Coord(x=27, y=10)),
            (Background('road2'), Coord(x=25, y=10)),
            (Background('road2'), Coord(x=26, y=10)),
            (Background('road2'), Coord(x=29, y=10)),
            (Background('road2'), Coord(x=30, y=10)),
            (Background('road2'), Coord(x=24, y=9)),
            (Background('road2'), Coord(x=28, y=9)),
            (ExtDecor('signpost'), Coord(x=23, y=11)),
            (Door('empty', linked_room="Cyber City"), Coord(x=30, y=10)),
            (Door('stairs_down', linked_room="Casino"), Coord(x=8, y=10)),
            (ExtDecor('signpost'), Coord(x=9, y=10)),
        ])

        empty_rect = [
            Rect(Coord(7, 6), Coord(30, 22)),
        ]
        used_coords = [coord.to_tuple() for obj, coord in objects]

        tree_spaces = []
        large_tree_positions = []
        tree_types = ["tree_small_1","tree_large_1", "tree_large_2","mapletree_small_1", "mapletree_large_2"]
        random.seed(64)
        TREE_SPARSITY = 0.95  # probability in (0-1) of placing a tree

        for i in range(self._map_rows-2):
            for j in range(self._map_cols-1):
                if any(rect.top_left.y <= i <= rect.bottom_right.y and rect.top_left.x <= j <= rect.bottom_right.x for rect in empty_rect):
                    continue
                if (i, j) in used_coords:
                    continue

                if random.random() < TREE_SPARSITY:
                    # choose a tree type
                    tree_type = random.choices(tree_types, weights=[6, 3, 4, 2, 2], k=1)[0]
                    if "_small_" in tree_type and is_large_tree_area(large_tree_positions,i, j):
                        continue 
                    elif "_large_" in tree_type:
                        large_tree_positions.append((i, j))
                    
                    if random.random() < 0.2:
                        tree = SpecialTree()
                    else:
                        tree = MapObject.get_obj(tree_type)
                    tr, rows, cols = tree._get_tilemap()
                    used = False
                    for row in range(rows):
                        for col in range(cols):
                            c = (i+row, j+col)
                            if c in used_coords:
                                used = True
                                break
                    if used:
                        continue

                    tree_spaces.append(Coord(i, j))
                    objects.append((tree, Coord(i, j)))
        random.seed(None)
        
        # add a building
        building1 = GreenHouseLarge(linked_room_str="Upload House")
        building_pos1 = Coord(11, 11)
        objects.append((building1, building_pos1))

        building = GreenHouseSmall(linked_room_str="Trivia House")
        objects.append((building, Coord(21, 17)))

        if any("server_remote" in arg for arg in sys.argv):
            building = SpecialGroupHouse()
        else:
            building = PurpleHouseSmall(linked_room_str="Example House")
        objects.append((building, Coord(22, 8))) #Coord(22, 25)))

        sign = Sign(text="Welcome to Trottier Town!")
        objects.append((sign, Coord(28, 14)))

        sign = Sign(text="Upload House\nWhere dreams come true...")
        objects.append((sign, building_pos1 + Coord(7, 1)))

        #objects.append((CircusTent(linked_room_str="Funhouse"), Coord(43, 29)))

        return objects
