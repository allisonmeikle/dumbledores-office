import os
os.environ["LOCAL"] = "True"

import math
import inspect
import tkinter as tk
from glob import glob
from pathlib import Path
from PIL import Image, ImageTk

from .maps.base import Map
from .tiles.buildings import *
from .tiles.map_objects import *
from .tiles.base import MapObject
from .resources import get_resource_path
from .util import get_ext_project_folder, get_subclasses_from_folders, get_subclasses_from_file, get_all_subclasses

CELL_SIZE = 32
GRID_ROWS = 550 // CELL_SIZE
GRID_COLS = 550 // CELL_SIZE
ENTRY_POINT_ROW = 8
ENTRY_POINT_COL = 5

#EXT_FOLDER = True
#GEN_MAP_FNAME = "generated_map_v2.py"

EXT_FOLDER = False
GEN_MAP_FNAME = "maps/trottier_town.py"

class MapEditor:
    def __init__(self, master):
        # Load classes and objects from folders.
        classes = get_subclasses_from_folders([Map, MapObject])
        MapObject.load_objects(classes[MapObject])

        images = set()
        map_objects = set()
        for cls in get_all_subclasses(MapObject).values():
            try:
                sig = inspect.signature(cls.__init__)
            except ValueError:
                continue
            params = list(sig.parameters.values())[1:]  # Exclude 'self'
            if all(param.default is not inspect.Parameter.empty or param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD) for param in params):
                obj = cls()
                if obj.get_image_name() == "" or obj.get_image_name() in images:
                    continue
                map_objects.add(obj)
                images.add(obj.get_image_name())

        # now find those with images but not in the list
        for image in glob(os.path.join(get_resource_path('image/tile/'), "*", "*.png")):
            image_path = Path(image)
            #tile_type = image_path.parent.name.replace("_", "")
            image_name = image_path.stem
            image_rel_path = image_path.relative_to(get_resource_path('image/'))
            image_rel_path = str(image_rel_path).replace(".png", "")
            if image_rel_path in images:
                continue
            map_obj = MapObject.get_obj(image_name)
            map_objects.add(map_obj)
            images.add(image_rel_path)

        self.available_objects: list[MapObject] = list(map_objects)
        self.available_objects.sort(key=lambda obj: obj.get_image_name())

        #print(self.available_objects)
        assert len(map_objects) > 0, "No map objects found."

        self.master = master
        self.master.title("Map Editor")
        max_grid_rows_to_show = 500 // CELL_SIZE
        max_grid_cols_to_show = 500 // CELL_SIZE
        self.master.geometry(f"{CELL_SIZE * max_grid_cols_to_show + 300 + 500}x{CELL_SIZE * max_grid_rows_to_show + 300}")
        self.main_frame = tk.Frame(master)
        self.main_frame.pack()

        # Sidebar frame for object selection.
        self.sidebar = tk.Frame(self.main_frame)
        self.sidebar.pack(side="left")
        
        self.current_object = self.available_objects[0]
        
        tk.Label(self.sidebar, text="Select Object:").pack()

        # Add a toggle for deletion mode.
        self.deletion_mode = tk.BooleanVar(value=False)
        delete_toggle = tk.Checkbutton(self.sidebar, text="Delete Mode", variable=self.deletion_mode)
        delete_toggle.pack(pady=5)

        # Create a canvas and scrollbar to allow scrolling on the sidebar.
        sidebar_canvas = tk.Canvas(self.sidebar, height=600)
        sidebar_scrollbar = tk.Scrollbar(self.sidebar, orient="vertical", command=sidebar_canvas.yview)
        sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)
        sidebar_canvas.pack(side="left", fill="both", expand=True)
        sidebar_scrollbar.pack(side="right", fill="y")

        sidebar_scrollable_frame = tk.Frame(sidebar_canvas)
        sidebar_canvas.create_window((0, 0), window=sidebar_scrollable_frame, anchor="nw")

        sidebar_scrollable_frame.bind(
            "<Configure>",
            lambda e: sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all"))
        )
        
        # Define a mouse wheel handler that returns "break".
        def on_mousewheel(event):
            sidebar_canvas.yview_scroll(-1 * int(event.delta / 120), "units")
            return "break"

        # Bind mouse wheel scrolling on the canvas area.
        sidebar_canvas.bind("<Enter>", lambda e: sidebar_canvas.bind_all("<MouseWheel>", on_mousewheel))
        sidebar_canvas.bind("<Leave>", lambda e: sidebar_canvas.unbind_all("<MouseWheel>"))

        sidebar_scrollable_frame.bind("<Enter>", lambda e: sidebar_canvas.bind_all("<MouseWheel>", on_mousewheel))
        sidebar_scrollable_frame.bind("<Leave>", lambda e: sidebar_canvas.unbind_all("<MouseWheel>"))
        sidebar_scrollable_frame.bind("<MouseWheel>", on_mousewheel)

        # Frame for the grid canvas with scrollbars.
        grid_frame = tk.Frame(self.main_frame)
        grid_frame.pack(side="left", padx=10, pady=10)
        self.grid_frame = grid_frame
        self.master = master
        self.sidebar_scrollable_frame = sidebar_scrollable_frame
        self.on_mousewheel = on_mousewheel
        self.sidebar_canvas = sidebar_canvas

        # Create the grid canvas.
        full_canvas_width = GRID_COLS * CELL_SIZE
        full_canvas_height = GRID_ROWS * CELL_SIZE

        # Visible viewport dimensions.
        visible_width = 800
        visible_height = 600

        self.canvas = tk.Canvas(
            self.grid_frame,
            width=visible_width,
            height=visible_height,
            scrollregion=(0, 0, full_canvas_width, full_canvas_height)
        )
        self.canvas.grid(row=0, column=0)

        # Add vertical scrollbar for the grid canvas.
        v_scroll = tk.Scrollbar(self.grid_frame, orient="vertical", command=self.canvas.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=v_scroll.set)

        # Add horizontal scrollbar for the grid canvas.
        h_scroll = tk.Scrollbar(self.grid_frame, orient="horizontal", command=self.canvas.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(xscrollcommand=h_scroll.set)
        
        # List to store all placements.
        self.placements = []
        
        # Variables to handle click-and-drag.
        self.dragging = False
        self.last_cell = None

        # Bind mouse events for click and drag.
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_button_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_button_release)
        # Right-click remains for deletion.
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        
        self.save_button = tk.Button(self.master, text="Save", command=self.save_map)
        self.save_button.pack(pady=10)

        # Sidebar images and buttons.
        self.object_images = {}
        self.thumb_images = {}
        buttons_frame = tk.Frame(self.sidebar_scrollable_frame)
        buttons_frame.pack()
        buttons_frame.bind("<MouseWheel>", self.on_mousewheel)
        buttons_frame.bind("<Enter>", lambda e: self.sidebar_canvas.bind_all("<MouseWheel>", self.on_mousewheel))
        buttons_frame.bind("<Leave>", lambda e: self.sidebar_canvas.unbind_all("<MouseWheel>"))

        for i, obj in enumerate(self.available_objects):
            image_name = obj.get_image_name()
            if len(image_name) == 0:
                continue
            file_path = get_resource_path("image/" + image_name + ".png")
            pil_img = Image.open(file_path)
            full_width = pil_img.width * 2
            full_height = pil_img.height * 2
            full_img_pil = pil_img.resize((full_width, full_height), Image.Resampling.NEAREST)
            full_img = ImageTk.PhotoImage(full_img_pil)
            self.object_images[obj.get_name()] = full_img

            # Create thumbnail.
            if full_width > 32:
                thumb_width = 32
                thumb_height = int(full_height * 32 / full_width)
            else:
                thumb_width = full_width
                thumb_height = full_height

            thumb_img_pil = full_img_pil.resize((thumb_width, thumb_height), Image.Resampling.NEAREST)
            thumb_img = ImageTk.PhotoImage(thumb_img_pil)
            self.thumb_images[obj.get_name()] = thumb_img

            b = tk.Button(
                buttons_frame,
                image=thumb_img,
                command=lambda o=obj: self.select_object(o),
                borderwidth=0, padx=0, pady=0,
                highlightthickness=0
            )
            b.bind_all("<MouseWheel>", self.on_mousewheel)
            row = i // 8
            col = i % 8
            b.grid(row=row, column=col, padx=0, pady=0)

        self.update_canvas(GRID_ROWS, GRID_COLS)

        # Load existing placements from generated_map.py if available.
        self.load_generated_map()

    def update_canvas(self, num_rows, num_cols):
        # update scroll region
        self.canvas.config(scrollregion=(0, 0, num_cols * CELL_SIZE, num_rows * CELL_SIZE))
        
        # Change grid cell to hold a list of placements
        self.grid = {}
        for row in range(num_rows):
            for col in range(num_cols):
                x1 = col * CELL_SIZE
                y1 = row * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="black")
                self.grid[(row, col)] = {"rect": rect_id, "placements": []}

    def get_project_root(self):
        """
        Returns the project root directory.
        In this example, editor.py is in a subfolder (e.g., 303MUD) and the project root is its parent.
        """
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def select_object(self, obj):
        self.current_object = obj

    def place_object_at(self, row, col):
        """Place the current object at the specified grid cell (row, col)."""
        if row < 0 or row >= GRID_ROWS or col < 0 or col >= GRID_COLS:
            return

        # Get the image for the current object.
        img = self.object_images[self.current_object.get_name()]
        img_width, img_height = (img.width(), img.height())
        col_span = int(math.ceil(img_width / CELL_SIZE))
        row_span = int(math.ceil(img_height / CELL_SIZE))
        if row + row_span > GRID_ROWS or col + col_span > GRID_COLS:
            return

        # Determine cells that will be covered.
        cells_to_cover = [(r, c) for r in range(row, row + row_span) for c in range(col, col + col_span)]
        # Remove any placements already in these cells.
        '''
        placements_to_remove = []
        for (r, c) in cells_to_cover:
            for placement in self.grid[(r, c)]["placements"]:
                placements_to_remove.append(placement)
        for placement in placements_to_remove:
            self.canvas.delete(placement["image_id"])
            if placement in self.placements:
                self.placements.remove(placement)
            for (r, c) in placement["cells"]:
                if placement in self.grid[(r, c)]["placements"]:
                    self.grid[(r, c)]["placements"].remove(placement)
        '''
        x = col * CELL_SIZE
        y = row * CELL_SIZE
        image_id = self.canvas.create_image(x, y, anchor="nw", image=img)
        placement = {
            "top_left": (row, col),
            "image_id": image_id,
            "cells": cells_to_cover,
            "object": self.current_object,
            "z_index": self.current_object.get_z_index(),
        }
        self.placements.append(placement)
        assert type(placement["cells"]) == list
        for (r, c) in cells_to_cover:
            self.grid[(r, c)]["placements"].append(placement)

    def delete_objects_at(self, row, col):
        """Delete all objects at the given grid cell (row, col)."""
        cell = self.grid.get((row, col))
        if not cell:
            return
        # Make a copy of placements since we'll modify the list.
        placements_to_remove = list(cell["placements"])
        for placement in placements_to_remove:
            self.canvas.delete(placement["image_id"])
            if placement in self.placements:
                self.placements.remove(placement)
            for (r, c) in placement["cells"]:
                if placement in self.grid[(r, c)]["placements"]:
                    self.grid[(r, c)]["placements"].remove(placement)

    def on_canvas_button_press(self, event):
        # Called when left mouse button is pressed.
        col = int(self.canvas.canvasx(event.x) // CELL_SIZE)
        row = int(self.canvas.canvasy(event.y) // CELL_SIZE)
        self.dragging = True
        self.last_cell = (row, col)
        # If delete mode is enabled, delete objects at this cell; otherwise, place object.
        if self.deletion_mode.get():
            self.delete_objects_at(row, col)
        else:
            self.place_object_at(row, col)

    def on_canvas_drag(self, event):
        # Called when mouse is moved with left button held down.
        if not self.dragging:
            return
        col = int(self.canvas.canvasx(event.x) // CELL_SIZE)
        row = int(self.canvas.canvasy(event.y) // CELL_SIZE)
        if (row, col) != self.last_cell:
            self.last_cell = (row, col)
            if self.deletion_mode.get():
                self.delete_objects_at(row, col)
            else:
                self.place_object_at(row, col)

    def on_canvas_button_release(self, event):
        # Called when left mouse button is released.
        self.dragging = False
        self.last_cell = None

    def on_canvas_right_click(self, event):
        # Right-click deletes the topmost placement at the clicked cell.
        col = int(self.canvas.canvasx(event.x) // CELL_SIZE)
        row = int(self.canvas.canvasy(event.y) // CELL_SIZE)
        if row < 0 or row >= GRID_ROWS or col < 0 or col >= GRID_COLS:
            return

        cell_placements = self.grid.get((row, col), {}).get("placements", [])
        if cell_placements:
            # Remove the last (topmost) placement.
            placement_to_remove = cell_placements[-1]
            self.canvas.delete(placement_to_remove["image_id"])
            if placement_to_remove in self.placements:
                self.placements.remove(placement_to_remove)
            for (r, c) in placement_to_remove["cells"]:
                if placement_to_remove in self.grid[(r, c)]["placements"]:
                    self.grid[(r, c)]["placements"].remove(placement_to_remove)

    def load_generated_map(self):
        """
        Dynamically import GEN_MAP_FNAME and load its placements.
        Adjust sys.path to include the project root so that modules such as 'maps' can be found.
        """
        fname = f"{GEN_MAP_FNAME}"
        if EXT_FOLDER:
            ext_project_folder = get_ext_project_folder()
            fname = f"{ext_project_folder}/{fname}"
            package_root = ext_project_folder
        else:
            fname = os.path.join("303MUD", fname)
            package_root = "303MUD"

        if not os.path.exists(fname):
            print("Generated map file not found:", fname)
            return
        
        # import the module
        #mod = importlib.import_module(fname.replace("/", ".").replace(".py", ""))
        # find the first Map subclass
        maps = get_subclasses_from_file(fname, [Map], package_root)
        if Map not in maps or len(maps[Map]) == 0:
            return
        map_subclass = list(maps[Map].items())[0][-1]
        gm = map_subclass()
        #if "GeneratedMap" not in maps[Map]:
        #    return
        
        #gm_class = maps[Map]["GeneratedMap"]
        #gm = gm_class()
        self.update_canvas(gm._map_rows, gm._map_cols)
        global GRID_ROWS, GRID_COLS
        GRID_ROWS = gm._map_rows
        GRID_COLS = gm._map_cols

        placements_list = gm.get_objects()  # Expected list of tuples: (MapObject, Coord)
        placements_list.sort(key=lambda tup: tup[0].get_z_index())
        for (obj, coord) in placements_list:
            # Expect coord to have attributes x and y (or col and row).
            col, row = coord.x, coord.y
            if row is None or col is None:
                print("Invalid coordinate:", coord)
                continue
            # Ensure we have the image for the object.
            if obj.get_name() not in self.object_images:
                file_path = get_resource_path("image/" + obj.get_image_name() + ".png")
                pil_img = Image.open(file_path)
                full_width = pil_img.width * 2
                full_height = pil_img.height * 2
                full_img_pil = pil_img.resize((full_width, full_height), Image.NEAREST)
                img = ImageTk.PhotoImage(full_img_pil)
                self.object_images[obj.get_name()] = img
            else:
                img = self.object_images[obj.get_name()]
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            image_id = self.canvas.create_image(x, y, anchor="nw", image=img)
            img_width, img_height = img.width(), img.height()
            col_span = int(math.ceil(img_width / CELL_SIZE))
            row_span = int(math.ceil(img_height / CELL_SIZE))
            cells = [(r, c) for r in range(row, row + row_span) for c in range(col, col + col_span)]
            placement = {
                "top_left": (row, col),
                "image_id": image_id,
                "z_index": obj.get_z_index(),
                "cells": cells,
                "object": obj
            }
            self.placements.append(placement)
            for (r, c) in cells:
                self.grid[(r, c)]["placements"].append(placement)

    def save_map(self):
        objects = []
        # Save each placement once.
        for placement in self.placements:
            r, c = placement["top_left"]
            objects.append((c, r, placement["object"]))
        code = self.generate_map_code(objects)
        #project_root = self.get_project_root()
        ext_project_folder = get_ext_project_folder()
        with open(os.path.join(ext_project_folder, GEN_MAP_FNAME), "w") as f:
            f.write(code)
        print(f"Map saved to {GEN_MAP_FNAME}")

    def generate_map_code(self, objects):
        header = (
            "# Generated Map Code\n"
            "from .imports import *\n"
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            "    from tiles.map_objects import Background\n"
            "    from maps.base import Map\n"
            "    from tiles.base import MapObject\n"
            "    from coord import Coord\n\n"
            "class GeneratedMap(Map):\n"
            "    def __init__(self) -> None:\n"
            "        super().__init__(\n"
            "            name='Generated Map',\n"
            f"            size=({GRID_ROWS}, {GRID_COLS}),\n"
            f"            entry_point=Coord({ENTRY_POINT_ROW}, {ENTRY_POINT_COL}),\n"
            "            description='description here',\n"
            "            background_tile_image='grass',\n"
            "            background_music='blithe',\n"
            "        )\n\n"
            "    def get_objects(self) -> list[tuple[MapObject, Coord]]:\n"
            "        return [\n"
        )
        body = ""
        for x, y, obj in objects:
            if type(obj) == MapObject:
                name = f"MapObject.get_obj({obj.get_image_name()})"
                image_name = obj.get_image_name().split('/')[-1]
                name = obj.__class__.__name__ + f"('{image_name}')"
            else:
                image_name = obj.get_image_name().split('/')[-1]
                name = obj.__class__.__name__ + f"('{image_name}')"
            body += f"            ({name}, Coord(x={x}, y={y})),\n"
        footer = "        ]\n\n"
        return header + body + footer

if __name__ == "__main__":
    root = tk.Tk()
    app = MapEditor(root)
    root.mainloop()
