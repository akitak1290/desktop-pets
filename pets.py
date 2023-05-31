import os
import sys
import random
import math
import json
import shutil
from pathlib import Path
import ntpath
import tempfile
from collections import OrderedDict
from win32api import GetMonitorInfo, MonitorFromPoint

import logging

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image

"""
TODO:
    add static typing for class variables
    add json struct and json validator for configs
    refactor PetCreator to subclasses
"""

ROOT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
LOG_FILE_PATH = os.path.join(ROOT_DIR_PATH, "runtime.log")

# Abstract main components into classes


class CanvasState:
    SCROLLABLE = 1
    DRAGGABLE = 2
    CONNECTING = 3


class App(tk.Tk):
    """
    An overlay windows app that always sits on top of the 
    app stack that draws animated 'pets' to the screen

    The root widget, also serves as a controller to allow
    subwidgets to communicate with each other

    Pets will be drawn onto child canvas with transparent bg,
    the parent widget's (this) bg will also be transparent

    Users can add new pets to the screen or create new ones
    from a set of PNG gif files through the Setting widget.
    """

    def __init__(self, *args, **kwargs) -> None:
        tk.Tk.__init__(self, *args, **kwargs)

        # additional metadata
        transparent_color = '#00ffff'
        monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
        work_area = monitor_info.get("Work")
        self.screen_width = work_area[2]
        self.screen_height = work_area[3]

        # config
        self.config(highlightbackground=transparent_color)
        self.config(bg=transparent_color)
        self.wm_attributes('-transparentcolor', transparent_color)
        self.overrideredirect(True)
        self.call("wm", "attributes", ".", "-topmost", "true")
        self.geometry(str(self.screen_width)+'x' +
                      str(self.screen_height)+'+0+0')

        # subwidgets
        # main canvas to display pets, fill entire root window
        self.canvas = tk.Canvas(self, width=self.screen_width,
                                height=self.screen_height, bd=0, highlightthickness=0)
        self.canvas.config(bg=transparent_color)
        self.canvas.place(x=0, y=0)

        # load available pets
        self.pet_config_path = os.path.join(ROOT_DIR_PATH, "configs.json")
        self.pets_path = os.path.join(ROOT_DIR_PATH, "pets")

        self.loaded_pets_config_dict = {}
        self.loaded_pets_dict = {}

        pets_configs_list = None
        with open(self.pet_config_path) as config_json:
            try:
                pets_configs_list = json.load(config_json)
            except json.JSONDecodeError:
                logging.error("Failed to read config json file")
                pets_configs_list = []

        for config_dict in pets_configs_list:
            abs_path = config_dict["abs_path"]
            config = PetConfigStruct(sequence=config_dict["sequence"],
                                     weights=config_dict["weights"],
                                     movement_speeds=config_dict["movement_speeds"],
                                     playback_speeds=config_dict["playback_speeds"])

            self.loaded_pets_config_dict[ntpath.basename(abs_path)] = {
                "abs_path": abs_path,
                "config": config
            }

        self.setting_panel = None
        gear_icon = tk.PhotoImage(file=os.path.join(
            ROOT_DIR_PATH, "assets", "gear.PNG"))
        setting_btn = tk.Button(self, image=gear_icon, relief=tk.FLAT)
        setting_btn.configure(background=transparent_color)
        setting_btn.bind("<Button>", self.toggle_setting_panel)
        setting_btn.place(anchor="nw", x=10, y=60)

        # event listener
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.toggle_setting_panel()

        # initiate the app
        self.run()

    def toggle_setting_panel(self, event=None) -> None:
        if not self.setting_panel:
            self.setting_panel = Setting(self)
            self.setting_panel.protocol(
                "WM_DELETE_WINDOW", self.close_setting_panel)
        else:
            self.close_setting_panel()
    
    def close_setting_panel(self) -> None:
        self.setting_panel.destroy()
        self.setting_panel = None

    def get_pets_configs(self) -> dict:
        return self.loaded_pets_config_dict

    def get_pets(self) -> dict:
        return self.loaded_pets_dict

    def add_pet_config(self, abs_path, config) -> None:
        self.loaded_pets_config_dict[ntpath.basename(abs_path)] = {
            "abs_path": abs_path,
            "config": config
        }

        if not self.save():
            logging.error("Can't save new pet's config")

    def create_pet(self, key) -> None:
        config = self.loaded_pets_config_dict[key]["config"]

        pet_name = self.random_pet_name()
        self.loaded_pets_dict[pet_name] = {
            "abs_path": self.loaded_pets_config_dict[key]["abs_path"],
            "pet": Pet(canvas=self.canvas,
                       pet_actions_full_path=self.loaded_pets_config_dict[
                           key]["abs_path"],
                       sequence_list=config.sequence,
                       weights_list=config.weights,
                       speeds_list=config.movement_speeds)
        }

    def remove_pet(self, key) -> None:
        self.loaded_pets_dict[key]["pet"].release()
        # del self.loaded_pets_dict[key]["pet"]
        self.loaded_pets_dict.pop(key)

    def save(self) -> bool:
        if Path(self.pet_config_path).is_file():
            with open(self.pet_config_path, "w") as config_json:
                data = []
                for pet_name, pet in self.loaded_pets_config_dict.items():
                    pet_config = pet["config"]
                    data.append({
                        "sequence": pet_config.sequence,
                        "weights": pet_config.weights,
                        "movement_speeds": pet_config.movement_speeds,
                        "playback_speeds": pet_config.playback_speeds,
                        "abs_path": pet["abs_path"]
                    })
                json.dump(data, config_json)
                return True
        return False

    def close(self) -> None:
        self.destroy()

    def random_pet_name(self) -> str:
        # lazy random string gen,
        # TODO: add real names
        return ntpath.basename(tempfile.NamedTemporaryFile().name)

    def run(self) -> None:
        logging.info('Pets are chilling... (Press Ctrl+C to kill the pets!)')
        self.mainloop()


class PetConfigStruct:
    def __init__(self, sequence, weights, movement_speeds, playback_speeds) -> None:

        # a 2d list mapping the next possible
        # actions  for each available action,
        # value can be either 0 or 1
        # [
        #   [int],
        #   [int],
        #   ..
        # ]
        self.sequence = sequence

        # a list of double, value ranges from
        # 0 to 1, to indicate the chance the
        # chance of a next possible action
        # [double]
        self.weights = weights

        # a list of tuple of 2 int, representing
        # vertical speed and horizontal speed of
        # each action, direction on each axes
        # is shown by the value being negative
        # or positive
        # [(int, int)]
        self.movement_speeds = movement_speeds

        # a list of int, representing the
        # playback speed of each action in
        # millisecond, value should be from
        # 1 to 1000
        # [int]
        self.playback_speeds = playback_speeds


class Setting(tk.Toplevel):
    def __init__(self, root_window) -> None:
        super().__init__(root_window)

        self.geometry("577x300")
        self.minsize(577, 0)
        self.maxsize(577, 700)
        self.title("Setting")
        self.configure(background='#d9ced7')

        # additional metadata
        transparent_color = '#00ffff'
        # frame_height, frame_wide = 100, 100

        # setting window
        self.root_window = root_window
        self.loaded_pets_configs_dict = root_window.get_pets_configs()
        self.loaded_pets_dict = root_window.get_pets()

        self.max_column = 5
        self.padding = 0
        self.thumbnails_available = {}
        self.labels_available = []
        self.thumbnails_current = {}
        self.labels_current = []

        # tk.Label(self, text="Desktop Pet").pack(fill="x")

        # nav frame
        self.nav_bar = tk.Frame(self, bd=0)
        self.nav_bar.pack(fill="x")

        # Create a canvas object and a vertical scrollbar for scrolling it.
        vscrollbar = ttk.Scrollbar(self, orient="vertical")
        vscrollbar.pack(fill="y", side="right", expand=0)
        canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                           yscrollcommand=vscrollbar.set, bg='#d9ced7')
        canvas.pack(fill="both", expand=1, padx=(20, 20), pady=(20, 0))
        vscrollbar.config(command=canvas.yview)

        # Reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # Create a frame inside the canvas which will be scrolled with it.
        self.interior = interior = tk.Frame(canvas, bg='#d9ced7')
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor="nw")
 
        canvas.itemconfigure(interior_id, width=1000)

        def _configure_interior(event):
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
        interior.bind('<Configure>', _configure_interior)

        # frames
        all_pets_btn = tk.Button(self.nav_bar, borderwidth=0, text='All pets', bg='#d9ced7',
                                 command=lambda: self.raise_frame(self.available_pets_frame, 0, 1))
        current_pet_btn = tk.Button(self.nav_bar, borderwidth=0, text='Current pets',
                                    command=lambda: self.raise_frame(self.current_pets_frame, 1, 0))
        new_btn = tk.Button(self.nav_bar, borderwidth=0, text="+ᓚᘏᗢ")

        all_pets_btn.grid(row=0, column=0, padx=(20, 0))
        current_pet_btn.grid(row=0, column=1)
        new_btn.grid(row=0, column=2, padx=(360, 0))

        self.nav_btn = (all_pets_btn, current_pet_btn)

        self.pet_create_panel = None
        new_btn.bind("<Button>", self.open_creator_panel)

        self.current_pets_frame = tk.Frame(interior, bg='#d9ced7')
        self.available_pets_frame = tk.Frame(interior, bg='#d9ced7')
        
        self.available_pets_frame.grid(
            column=0, row=0, sticky='news')
        self.current_pets_frame.grid(
            column=0, row=0, sticky='news')

        placeholder_img = os.path.join(
            ROOT_DIR_PATH, "pets", "placeholder.png")
        self.ph = tk.PhotoImage(file=placeholder_img)

        self.load_pets_configs()
        self.load_current_pets()

    def raise_frame(self, frame, current_idx, new_idx) -> None:
        frame.tkraise()
        self.nav_btn[new_idx].configure(background='#f7e4f4')
        self.nav_btn[current_idx].configure(background='#d9ced7')

    def open_creator_panel(self, event) -> None:
        if not self.pet_create_panel:
            self.pet_create_panel = PetCreator(self, self)
            self.pet_create_panel.protocol(
                "WM_DELETE_WINDOW", self.close_creator_panel)

    def close_creator_panel(self) -> None:
        if self.pet_create_panel:
            self.pet_create_panel.release()
            self.pet_create_panel.destroy()
            self.pet_create_panel = None

    def load_pets_configs(self) -> None:
        pet_cnt = 0

        for label in self.labels_available:
            label.destroy()
        self.labels_available = []

        # TODO: maybe get user to add a real thumbnail would
        # be more efficient and better visually
        self.thumbnails_available = {}

        for idx, key in enumerate(self.loaded_pets_configs_dict.keys()):
            abs_path = self.loaded_pets_configs_dict[key]["abs_path"]
            file = os.path.join(ROOT_DIR_PATH, "pets",
                                ntpath.basename(abs_path),
                                os.listdir(abs_path)[0])

            self.thumbnails_available[idx] = {
                "key": key,
                "image": tk.PhotoImage(file=file)
            }

        for row_idx in range(math.ceil(len(self.loaded_pets_configs_dict)/self.max_column)):
            for column_idx in range(self.max_column):
                self.labels_available.append(tk.Label(
                    self.available_pets_frame, image=self.thumbnails_available[pet_cnt]["image"], bg='#d9ced7'))
                self.labels_available[pet_cnt].grid(
                    column=column_idx, row=row_idx, padx=self.padding, pady=self.padding)
                self.labels_available[pet_cnt].bind('<Enter>', self.on_hover)
                self.labels_available[pet_cnt].bind('<Leave>', self.on_leave)
                self.labels_available[pet_cnt].bind(
                    '<Button-1>', lambda event, key=self.thumbnails_available[pet_cnt]["key"]: self.on_create_pet(event, key))
                pet_cnt += 1
                if pet_cnt == len(self.loaded_pets_configs_dict):
                    break

    def load_current_pets(self) -> None:
        pet_cnt = 0

        for label in self.labels_current:
            label.destroy()
        self.labels_current = []

        self.thumbnails_current = {}

        for idx, key in enumerate(self.loaded_pets_dict.keys()):
            abs_path = self.loaded_pets_dict[key]["abs_path"]
            file = os.path.join(ROOT_DIR_PATH, "pets",
                                ntpath.basename(abs_path),
                                os.listdir(abs_path)[0])

            self.thumbnails_current[idx] = {
                "key": key,
                "image": tk.PhotoImage(file=file)
            }

        for row_idx in range(math.ceil(len(self.loaded_pets_dict)/self.max_column)):
            for column_idx in range(self.max_column):
                self.labels_current.append(tk.Label(
                    self.current_pets_frame, image=self.thumbnails_current[pet_cnt]["image"], bg='#d9ced7'))
                self.labels_current[pet_cnt].grid(
                    column=column_idx, row=row_idx, padx=self.padding, pady=self.padding)
                self.labels_current[pet_cnt].bind('<Enter>', self.on_hover)
                self.labels_current[pet_cnt].bind('<Leave>', self.on_leave)
                self.labels_current[pet_cnt].bind(
                    '<Button-1>', lambda event, key=self.thumbnails_current[pet_cnt]["key"]: self.on_remove_pet(event, key))
                pet_cnt += 1
                if pet_cnt == len(self.loaded_pets_dict):
                    break

    def add_pet_config(self, abs_path, config) -> None:
        self.root_window.add_pet_config(abs_path, config)
        self.load_pets_configs()  # reload with new pet config object

    def remove_pet(self, key) -> None:
        self.root_window.remove_pet(key)

    def create_pet(self, key) -> None:
        self.root_window.create_pet(key)

    def on_hover(self, event) -> None:
        self.config(cursor="hand2")

    def on_leave(self, event) -> None:
        self.config(cursor="")

    def on_create_pet(self, event, key) -> None:
        self.create_pet(key)
        self.load_current_pets()

    def on_remove_pet(self, event, key) -> None:
        self.remove_pet(key)
        self.load_current_pets()
        self.root_window.config(cursor="")


class PetCreator(tk.Toplevel):
    def __init__(self, parent_frame, controller) -> None:
        super().__init__(parent_frame)

        self.title("Pet Creator")

        self.controller = controller

        add_icon = os.path.join(ROOT_DIR_PATH, "assets", "add.PNG")
        self.add_icon_pht_obj = tk.PhotoImage(file=add_icon)

        # canvas
        self.canvas_state = CanvasState.SCROLLABLE

        # config settings
        self.connection_dict = {}
        self.canvas_item_dict = OrderedDict()
        self.config_dict = OrderedDict()
        self.action_files_names_list = []

        # for dragging
        self.current_img_id = None
        self.img_x = 0
        self.img_y = 0
        self.is_drag = False

        # for connection
        self.new_connection_delay = False
        self.current_connection_id = None

        """
        dummies to hold canvas object to avoid garbage collection
        photoimage bug?
        https://web.archive.org/web/20201112023229/http://effbot.org/tkinterbook/photoimage.htm
        """
        self.object_id = None

        # UI elements
        self.canvas_bg = tk.PhotoImage(file=os.path.join(ROOT_DIR_PATH, "assets", "grid.PNG"))
        self.canvas = tk.Canvas(
            self, width=700, height=500, background="bisque")
        self.hscrollbar = tk.Scrollbar(
            self, orient="horizontal", command=self.canvas.xview)
        self.vscrollbar = tk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview)
        # add scrollbar to canvas
        self.canvas.configure(
            yscrollcommand=self.vscrollbar.set, xscrollcommand=self.hscrollbar.set)
        self.canvas.configure(scrollregion=(0, 0, 1000, 1000))

        self.hscrollbar.grid(row=1, column=0, sticky="we")
        self.vscrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.grid(row=0, column=0, sticky="news")
        self.canvas.create_image( 0, 0, image = self.canvas_bg, anchor = "nw")
        # grow canvas to frame
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.c_scroll_begin_cb = self.canvas.bind(
            "<ButtonPress-1>", self.scroll_start)
        self.c_scroll_move_cb = self.canvas.bind(
            "<B1-Motion>", self.scroll_move)
        self.c_hover_cb = self.canvas.bind("<Motion>", self.hover_on_canvas)
        self.c_leave_cb = self.canvas.bind("<Leave>", self.leave_canvas)

        tk.Button(self, text="New", command=self.create_new).grid(
            row=0, column=0, sticky='ne')

        self.config_frame = tk.Frame(self)
        self.config_frame.grid(column=2, row=0, sticky="n")

        self.current_frame_label = tk.Label(
            self.config_frame, text="Action Config", font=('calibre', 10, 'bold'))
        separator1 = ttk.Separator(self.config_frame, orient='horizontal')
        self.config_general_frame = tk.Frame(self.config_frame)
        separator2 = ttk.Separator(self.config_frame, orient='horizontal')
        self.config_action_frame = tk.Frame(self.config_frame)

        self.current_frame_label.grid(column=0, row=0, sticky="n")
        separator1.grid(column=0, row=1, sticky="we", pady=(10, 10))
        self.config_general_frame.grid(column=0, row=2, sticky="nwe")
        separator2.grid(column=0, row=3, sticky="we", pady=(10, 10))
        self.config_action_frame.grid(column=0, row=4, sticky="nwe")

        self.falling_action_name = tk.StringVar()
        falling_action_selection_label = tk.Label(
            self.config_general_frame, text='Falling Action: ', font=('calibre', 10, 'bold'))
        self.falling_action_entry = tk.OptionMenu(self.config_general_frame,
                                                  self.falling_action_name,
                                                  *self.action_files_names_list if self.action_files_names_list else [0])

        self.dragging_action_name = tk.StringVar()
        dragging_action_selection_label = tk.Label(
            self.config_general_frame, text='Dragging Action: ', font=('calibre', 10, 'bold'))
        self.dragging_action_entry = tk.OptionMenu(self.config_general_frame,
                                                   self.dragging_action_name,
                                                   *self.action_files_names_list if self.action_files_names_list else [0])

        self.config_general_frame.grid_columnconfigure(0, weight=1)
        self.config_general_frame.grid_columnconfigure(1, weight=1)
        falling_action_selection_label.grid(column=0, row=0, sticky="w")
        self.falling_action_entry.grid(column=1, row=0, sticky="w")
        dragging_action_selection_label.grid(column=0, row=1, sticky="w")
        self.dragging_action_entry.grid(column=1, row=1, sticky="w")

        self.name_var = tk.StringVar(self.config_action_frame, "")
        self.m_speed_var_x = tk.StringVar(self.config_action_frame, "0")
        self.m_speed_var_y = tk.StringVar(self.config_action_frame, "0")
        self.p_speed_var = tk.StringVar(self.config_action_frame, "0")
        # 10, 20, 30
        self.chance_options = [
            "Rare",
            "Normal",
            "Frequent"
        ]  # etc
        self.chance = tk.StringVar(
            self.config_action_frame, self.chance_options[0])
        self.can_repeat = tk.IntVar(self.config_action_frame, 0)

        self.name_var_cb = self.name_var.trace_add("write", lambda name,
                                                   index, mode: self.set_name())
        self.m_speed_var_x_cb = self.m_speed_var_x.trace_add("write", lambda name,
                                                             index, mode: self.set_m_speed_x())
        self.m_speed_var_y_cb = self.m_speed_var_y.trace_add("write", lambda name,
                                                             index, mode: self.set_m_speed_y())
        self.p_speed_var_cb = self.p_speed_var.trace_add("write", lambda name,
                                                         index, mode: self.set_p_speed_var())
        self.chance_cb = self.chance.trace_add("write", lambda name,
                                               index, mode: self.set_chance())
        self.can_repeat_cb = self.can_repeat.trace_add("write", lambda name,
                                                       index, mode: self.set_can_repeat())

        # https://stackoverflow.com/questions/55184324/why-is-calling-register-required-for-tkinter-input-validation/55231273#55231273
        vcmd = (parent_frame.register(self.entry_validation), '%P')

        name_label = tk.Label(
            self.config_action_frame, text='Name: ', font=('calibre', 10, 'bold'))
        name_entry = tk.Label(
            self.config_action_frame, textvariable=self.name_var, font=('calibre', 10, 'normal'))

        m_speed_x_label = tk.Label(
            self.config_action_frame, text='Movement Speed x: ', font=('calibre', 10, 'bold'))
        self.m_speed_x_entry = tk.Entry(
            self.config_action_frame,
            textvariable=self.m_speed_var_x,
            font=('calibre', 10, 'normal'),
            validate='key', validatecommand=vcmd)
        m_speed_y_label = tk.Label(
            self.config_action_frame, text='Movement Speed y: ', font=('calibre', 10, 'bold'))
        self.m_speed_y_entry = tk.Entry(
            self.config_action_frame,
            textvariable=self.m_speed_var_y,
            font=('calibre', 10, 'normal'),
            validate='key', validatecommand=vcmd)

        p_speed_label = tk.Label(
            self.config_action_frame, text='Playback Speed: ', font=('calibre', 10, 'bold'))
        self.p_speed_entry = tk.Entry(
            self.config_action_frame,
            textvariable=self.p_speed_var,
            font=('calibre', 10, 'normal'),
            validate='key', validatecommand=vcmd)

        chance_label = tk.Label(
            self.config_action_frame, text='Chance: ', font=('calibre', 10, 'bold'))
        chance_entry = tk.OptionMenu(
            self.config_action_frame, self.chance, *self.chance_options)

        can_repeat = tk.Checkbutton(self.config_action_frame, text="Can Repeat",
                                    variable=self.can_repeat, onvalue=1, offvalue=0)

        name_label.grid(column=0, row=0, sticky="nw")
        name_entry.grid(column=1, row=0, sticky="n")

        m_speed_x_label.grid(column=0, row=1, sticky="nw")
        self.m_speed_x_entry.grid(column=1, row=1, sticky="n")

        m_speed_y_label.grid(column=0, row=2, sticky="nw")
        self.m_speed_y_entry.grid(column=1, row=2, sticky="n")

        p_speed_label.grid(column=0, row=3, sticky="nw")
        self.p_speed_entry.grid(column=1, row=3, sticky="n")

        chance_label.grid(column=0, row=4, sticky="nw")
        chance_entry.grid(column=1, row=4, sticky="n")

        can_repeat.grid(column=0, row=5, sticky="nw")

        self.disable_config()

        tk.Button(self, text="Submit", command=self.submit).grid(
            row=1, column=2, sticky="n")

    def __del__(self) -> None:
        logging.info(('Pet creator deleted'))

    def release(self) -> None:
        self.canvas.unbind("<ButtonPress-1>", self.c_scroll_begin_cb)
        self.canvas.unbind("<B1-Motion>", self.c_scroll_move_cb)
        self.canvas.unbind("<Motion>", self.c_hover_cb)
        self.canvas.unbind("<Leave>", self.c_leave_cb)

        self.name_var.trace_remove("write", self.name_var_cb)
        self.m_speed_var_x.trace_remove("write", self.m_speed_var_x_cb)
        self.m_speed_var_y.trace_add("write", self.m_speed_var_y_cb)
        self.p_speed_var.trace_add("write", self.p_speed_var_cb)
        self.chance.trace_add("write", self.chance_cb)
        self.can_repeat.trace_add("write", self.can_repeat_cb)

    # load gif and create canvas items
    def create_new(self) -> None:
        # TODO: refactor this

        self.reset_canvas()

        file_list = filedialog.askopenfilenames(
            filetypes=[("Gif files", "*.gif")])

        if not file_list:
            return

        self.object_id = [-1]*(len(file_list))
        self.action_files_names_list = []

        for idx, file in enumerate(file_list):
            # setup canvas's items
            x = random.randint(0, 400)
            y = random.randint(0, 400)
            file_name = ntpath.basename(os.path.splitext(file)[0])

            self.action_files_names_list.append(file_name)
            # img = (Image.open(file))
            # resized_img = img.resize((100, 100), Image)
            self.object_id[idx] = tk.PhotoImage(file=file)
            img_id = self.canvas.create_image(
                x, y, anchor="nw", image=self.object_id[idx])
            text_id = self.canvas.create_text(x, y+100, anchor="nw",
                                              text=file_name)
            add_id = self.canvas.create_image(
                x+100, y+50, anchor="nw", image=self.add_icon_pht_obj)
            self.canvas.itemconfigure(add_id, state='hidden')

            self.canvas_item_dict[img_id] = {
                "text_id": text_id,
                "add_id": add_id,
                "lines_ids_list": []
            }

            # setup config per img item
            self.config_dict[img_id] = {
                "file_name": file_name,
                "m_speed_x": 0,
                "m_speed_y": 0,
                "p_speed": 100,
                "can_repeat": 0,
                "chance": self.chance_options[0],
                "format": os.path.splitext(file)[1],
                "abs_path": file
            }

            # canvas's items' event listeners
            self.canvas.tag_bind(img_id, '<Button-1>', lambda event,
                                 img_id=img_id: self.click_action_item(event, img_id=img_id))
            self.canvas.tag_bind(img_id, '<ButtonRelease-1>', self.release_img)
            self.canvas.tag_bind(img_id, '<Motion>', lambda event,
                                 add_id=add_id: self.hover(event, add_id=add_id))
            self.canvas.tag_bind(img_id, '<Leave>', lambda event,
                                 add_id=add_id: self.leave(event, add_id=add_id))
            self.canvas.tag_bind(
                img_id, '<B1-Motion>',
                lambda event, img_id=img_id, text_id=text_id, add_id=add_id: self.drag(event, img_id=img_id, text_id=text_id, add_id=add_id))

            self.canvas.tag_bind(add_id, '<Motion>', lambda event,
                                 add_id=add_id: self.hover(event, add_id=add_id))
            self.canvas.tag_bind(add_id, '<Leave>', lambda event,
                                 add_id=add_id: self.leave(event, add_id=add_id))
            self.canvas.tag_bind(
                add_id, '<Button-1>',
                lambda event, img_id=img_id: self.create_connection(event, img_id=img_id))

        # update dropdown menu
        falling_menu = self.falling_action_entry["menu"]
        dragging_menu = self.dragging_action_entry["menu"]
        falling_menu.delete(0, "end")
        dragging_menu.delete(0, "end")
        for name in self.action_files_names_list:
            falling_menu.add_command(label=name,
                                     command=lambda value=name: self.falling_action_name.set(value))
            dragging_menu.add_command(label=name,
                                      command=lambda value=name: self.dragging_action_name.set(value))

    def add_custom(self) -> None:
        add_id = self.canvas.create_image(
            200, 200, anchor="nw", image=self.add_icon_pht_obj)

    # canvas event callbacks
    def scroll_start(self, event) -> None:
        # CONNECTION state: terminate a connection
        if self.canvas_state == CanvasState.CONNECTING and not self.new_connection_delay:
            # release connection
            self.canvas_item_dict[self.connection_dict[self.current_connection_id]
                                  ["start"]]["lines_ids_list"].pop()
            self.connection_dict.pop(self.current_connection_id)
            self.canvas.delete(self.current_connection_id)
            self.current_connection_id = None

            self.set_canvas_state(CanvasState.SCROLLABLE)

        # SCROLLABLE state: mouse input directly on canvas
        # background
        elif self.canvas_state == CanvasState.SCROLLABLE:
            self.canvas.scan_mark(event.x, event.y)

            if self.current_img_id != None:
                self.disable_config()
                self.current_img_id = None  # ! this has to be called before sets
                self.name_var.set("")
                self.m_speed_var_x.set("0")
                self.m_speed_var_y.set("0")
                self.p_speed_var.set("0")
                self.chance.set(self.chance_options[0])
                self.can_repeat.set(0)

    def scroll_move(self, event) -> None:
        if self.canvas_state == CanvasState.SCROLLABLE:
            self.canvas.scan_dragto(event.x, event.y, gain=1)

    def leave_canvas(self, event) -> None:
        self.canvas_state == CanvasState.SCROLLABLE

    def hover_on_canvas(self, event) -> None:
        if self.new_connection_delay:
            self.new_connection_delay = False

        if self.canvas_state == CanvasState.CONNECTING:
            y0 = int(self.connection_dict[self.current_connection_id]["y0"])
            x0 = int(self.connection_dict[self.current_connection_id]["x0"])
            x = int(event.widget.canvasx(event.x))
            y = int(event.widget.canvasy(event.y))

            # HACK: shorten the line a bit so it doesn't
            # shadow items beneath it
            r = 0.95

            x = r * x + (1 - r) * x0  # find point that divides the segment
            y = r * y + (1 - r) * y0  # into the ratio (1-r):r

            self.canvas.coords(self.current_connection_id, x0, y0, x, y)

    # action/item event callbacks
    def create_connection(self, event, img_id) -> None:
        if self.canvas_state == CanvasState.CONNECTING:
            # already a connection
            return

        # NOTE: to avoid click through to canvas
        # and immediately delete the line item
        self.new_connection_delay = True

        # adjust for scan_mark
        add_id_coor = self.canvas.coords(
            self.canvas_item_dict[img_id]["add_id"])
        x = add_id_coor[0] + 10  # TODO: magic number, half width
        y = add_id_coor[1] + 10
        # store connection/line
        self.current_connection_id = self.canvas.create_line(
            x, y, x, y, fill="black", width=2, arrow=tk.LAST)
        self.connection_dict[self.current_connection_id] = {
            "x0": x,
            "y0": y,
            "x": x,
            "y": y,
            "start": img_id,
            "stop": None
        }
        self.canvas_item_dict[img_id]["lines_ids_list"].append(
            self.current_connection_id)

        self.set_canvas_state(CanvasState.CONNECTING)

    def move_line(self, event) -> None:
        pass

    def delete_line(self, event, line_id) -> None:
        if self.canvas_state == CanvasState.SCROLLABLE:

            for key in self.canvas_item_dict.keys():
                if line_id in self.canvas_item_dict[key]["lines_ids_list"]:
                    self.canvas_item_dict[key]["lines_ids_list"].remove(
                        line_id)

            self.connection_dict.pop(line_id)

            self.canvas.delete(line_id)

    def hover_line(self, event) -> None:
        self.config(cursor="hand2")

    def leave_line(self, event) -> None:
        self.config(cursor="")

    def click_action_item(self, event, img_id) -> None:
        if self.canvas_state == CanvasState.CONNECTING:
            # don't drag if a connection is underway
            if self.connection_dict[self.current_connection_id]["start"] == img_id:
                # connection has to be between 2 different actions
                return  # TODO: rewrite this instead of adding a new checkbox?

            # finish the connection
            img_id_coor = self.canvas.coords(img_id)
            # TODO: magic number, half width/height
            self.connection_dict[self.current_connection_id]["x"] = img_id_coor[0] + 50
            self.connection_dict[self.current_connection_id]["y"] = img_id_coor[1] + 50
            self.connection_dict[self.current_connection_id]["stop"] = img_id
            self.canvas.coords(
                self.current_connection_id,
                self.connection_dict[self.current_connection_id]["x0"],
                self.connection_dict[self.current_connection_id]["y0"],
                self.connection_dict[self.current_connection_id]["x"],
                self.connection_dict[self.current_connection_id]["y"])

            self.canvas.tag_raise(
                self.connection_dict[self.current_connection_id]["stop"])

            self.canvas_item_dict[img_id]["lines_ids_list"].append(
                self.current_connection_id)

            self.canvas.tag_bind(self.current_connection_id,
                                 '<Motion>', self.hover_line)
            self.canvas.tag_bind(self.current_connection_id,
                                 '<Leave>', self.leave_line)

            self.canvas.tag_bind(self.current_connection_id,
                                 '<Button-1>',
                                 lambda event, line_id=self.current_connection_id: self.delete_line(event, line_id))

            self.current_connection_id = None
            self.set_canvas_state(CanvasState.SCROLLABLE)

        elif self.canvas_state == CanvasState.SCROLLABLE:
            self.canvas.tag_raise(img_id)
            self.canvas.tag_raise(self.canvas_item_dict[img_id]["text_id"])
            self.canvas.tag_raise(self.canvas_item_dict[img_id]["add_id"])

            self.enable_config()
            self.current_img_id = img_id  # !this has to be called before sets
            self.name_var.set(self.config_dict[img_id]["file_name"])
            self.m_speed_var_x.set(self.config_dict[img_id]["m_speed_x"])
            self.m_speed_var_y.set(self.config_dict[img_id]["m_speed_y"])
            self.p_speed_var.set(self.config_dict[img_id]["p_speed"])
            self.chance.set(self.config_dict[img_id]["chance"])
            self.can_repeat.set(self.config_dict[img_id]["can_repeat"])

            # drag action
            # self.is_drag = True
            self.set_canvas_state(CanvasState.DRAGGABLE)
            self.img_x = event.widget.canvasx(event.x)
            self.img_y = event.widget.canvasy(event.y)

    def drag(self, event, img_id, text_id, add_id) -> None:
        if not self.canvas_state == CanvasState.DRAGGABLE:
            return

        x_dist = event.widget.canvasx(event.x) - self.img_x
        y_dist = event.widget.canvasy(event.y) - self.img_y
        self.canvas.move(img_id, x_dist, y_dist)
        self.canvas.move(
            self.canvas_item_dict[img_id]["text_id"], x_dist, y_dist)
        self.canvas.move(
            self.canvas_item_dict[img_id]["add_id"], x_dist, y_dist)

        img_id_coor = self.canvas.coords(img_id)
        add_id_coor = self.canvas.coords(
            self.canvas_item_dict[img_id]["add_id"])
        for line_id in self.canvas_item_dict[img_id]["lines_ids_list"]:
            if img_id == self.connection_dict[line_id]["start"]:
                # TODO: magic number, half width/height
                self.connection_dict[line_id]["x0"] = add_id_coor[0] + 10
                self.connection_dict[line_id]["y0"] = add_id_coor[1] + 10
            elif img_id == self.connection_dict[line_id]["stop"]:
                # TODO: magic number, half width/height
                self.connection_dict[line_id]["x"] = img_id_coor[0] + 50
                self.connection_dict[line_id]["y"] = img_id_coor[1] + 50
            self.canvas.coords(
                line_id,
                self.connection_dict[line_id]["x0"],
                self.connection_dict[line_id]["y0"],
                self.connection_dict[line_id]["x"],
                self.connection_dict[line_id]["y"])

        self.img_x = event.widget.canvasx(event.x)
        self.img_y = event.widget.canvasy(event.y)

    def release_img(self, event) -> None:
        # self.is_drag = False
        self.set_canvas_state(CanvasState.SCROLLABLE)

    def hover(self, event, add_id) -> None:
        self.canvas.itemconfigure(add_id, state='normal')
        self.config(cursor="hand2")

    def leave(self, event, add_id) -> None:
        if self.canvas_state == CanvasState.DRAGGABLE:
            self.set_canvas_state(CanvasState.SCROLLABLE)

        self.canvas.itemconfigure(add_id, state='hidden')
        self.config(cursor="")

    # config event callbacks
    # TODO:
    # current behavior: if sets are used to !reset! (not user input) state
    # of config variables, it shouldn't update an action/img config
    # !refactor! ifs in sets atm is stupid
    def set_name(self) -> None:
        if self.current_img_id != None:
            self.config_dict[self.current_img_id]["file_name"] = self.name_var.get()

    def set_m_speed_x(self) -> None:
        if self.current_img_id != None:
            value = None
            if self.m_speed_var_x.get() == "":
                value = 0
            else:
                value = int(self.m_speed_var_x.get())
            self.config_dict[self.current_img_id]["m_speed_x"] = value

    def set_m_speed_y(self) -> None:
        if self.current_img_id != None:
            value = None
            if self.m_speed_var_y.get() == "":
                value = 0
            else:
                value = int(self.m_speed_var_y.get())
            self.config_dict[self.current_img_id]["m_speed_y"] = value

    def set_p_speed_var(self) -> None:
        if self.current_img_id != None:
            value = None
            if self.p_speed_var.get() == "":
                value = 0
            else:
                value = int(self.p_speed_var.get())
            self.config_dict[self.current_img_id]["p_speed"] = value

    def set_chance(self) -> None:
        if self.current_img_id != None:
            self.config_dict[self.current_img_id]["chance"] = self.chance.get()

    def set_can_repeat(self) -> None:
        if self.current_img_id != None:
            self.config_dict[self.current_img_id]["can_repeat"] = self.can_repeat.get(
            )

    # submit
    def submit(self) -> None:
        # store images to local
        pet_dir = os.path.join(ROOT_DIR_PATH, "pets")
        new_dir = os.path.join(ROOT_DIR_PATH, "pets",
                               self.random_pet_name())
        if not os.path.exists(pet_dir):
            logging.error(f"Can't create new pet, {pet_dir} not found")
            return

        logging.info(f"New pet config: {self.config_dict}")
        # some hacky stupid code to move the 2 special actions to the end
        # of the list to properly work with the Pet class
        # TODO: rewrite this method
        sub_list = []
        falling_idx, dragging_idx = None, None

        for key in self.config_dict.keys():
            if self.config_dict[key]["file_name"] == self.dragging_action_name.get():
                dragging_idx = key
            elif self.config_dict[key]["file_name"] == self.falling_action_name.get():
                falling_idx = key
            else:
                sub_list.append(key)

        if not falling_idx or not dragging_idx:
            logging.error(
                "Missing falling and dragging animations, can't submit")
            # TODO: add error prompt
            return

        new_ordered_config_dict = {k: self.config_dict[k] for k in sub_list}

        # this order matters here
        new_ordered_config_dict[falling_idx] = self.config_dict[falling_idx]
        new_ordered_config_dict[dragging_idx] = self.config_dict[dragging_idx]

        logging.info(f"Reordered pet config: {new_ordered_config_dict}")

        Path(new_dir).mkdir(parents=False, exist_ok=False)
        for idx, key in enumerate(new_ordered_config_dict.keys()):
            origin = new_ordered_config_dict[key]["abs_path"]
            des_file_name = str(idx) + "_" + str(
                new_ordered_config_dict[key]["file_name"]) + new_ordered_config_dict[key]["format"]
            des = os.path.join(new_dir, des_file_name)
            shutil.copy(origin, des)

        # # store pet config
        pet_action_cnt = len(new_ordered_config_dict.keys())
        sequence = [[0]*pet_action_cnt for i in range(pet_action_cnt)]
        weights_list = []
        m_speeds_list = []
        p_speeds_list = []

        # self.dragging_action_name
        # self.falling_action_name

        logging.info(f"Sequence: {self.connection_dict}")

        img_ids = new_ordered_config_dict.keys()  # ordered dict
        for idx, img_id in enumerate(img_ids):
            weights_options = [10, 20, 30]
            weight = weights_options[
                self.chance_options.index(new_ordered_config_dict[img_id]["chance"])]
            m_speed = [new_ordered_config_dict[img_id]["m_speed_x"],
                       new_ordered_config_dict[img_id]["m_speed_y"]]

            weights_list.append(weight)
            m_speeds_list.append(m_speed)
            p_speeds_list.append(self.config_dict[img_id]["p_speed"])

            for line_id in self.canvas_item_dict[img_id]["lines_ids_list"]:
                if self.connection_dict[line_id]["start"] == img_id:
                    stop = list(img_ids).index(
                        self.connection_dict[line_id]["stop"])
                    sequence[idx][stop] = 1

            if new_ordered_config_dict[img_id]["can_repeat"]:
                sequence[idx][idx] = 1

        # store add pet config to configs.json
        config = PetConfigStruct(sequence=sequence,
                                 weights=weights_list,
                                 movement_speeds=m_speeds_list,
                                 playback_speeds=p_speeds_list)

        self.add_pet_config(new_dir, config)

        self.reset_canvas()

    # Utils
    def random_pet_name(self) -> str:
        # lazy random string gen,
        # TODO: add real names
        return ntpath.basename(tempfile.NamedTemporaryFile().name)

    def disable_config(self) -> None:
        for child in self.config_action_frame.winfo_children():
            child.configure(state='disabled')

    def enable_config(self) -> None:
        for child in self.config_action_frame.winfo_children():
            child.configure(state='normal')

    def entry_validation(self, P) -> None:
        if str.isdigit(P) or P == "":
            return True
        else:
            return False

    def reset_canvas(self) -> None:
        items_ids = []
        for key in self.canvas_item_dict.keys():
            items_ids.append(key)
            items_ids.append(self.canvas_item_dict[key]["text_id"])
            items_ids.append(self.canvas_item_dict[key]["add_id"])
            items_ids += self.canvas_item_dict[key]["lines_ids_list"]

        for item_id in items_ids:
            self.canvas.delete(item_id)

        self.canvas_item_dict = OrderedDict()
        self.connection_dict = {}

        self.object_id = None

    def add_pet_config(self, abs_path, config) -> None:
        self.controller.add_pet_config(abs_path, config)

    def remove_pet(self, key) -> None:
        self.controller.remove_pet(key)

    def create_pet(self, key) -> None:
        self.controller.create_pet(key)

    # Debug
    def set_canvas_state(self, state) -> None:
        self.canvas_state = state
        states = {
            1: "scrollable",
            2: "draggable",
            3: "connecting"
        }
        logging.info(str(sys._getframe(1).f_code.co_name) +
                     " set state: " + str(states[state]))


# TODO: add playback speed to Pet
# although, playback speed should not be conflicted
# with x speed and y speed
class Pet:
    def __init__(self, canvas, pet_actions_full_path, sequence_list, weights_list, speeds_list) -> None:
        # drawing canvas reference
        self.canvas = canvas

        # additional metadata
        canvas.update()  # force update to get latest changes to canvas
        self.screen_width = canvas.winfo_width()
        self.screen_height = canvas.winfo_height()
        self.pet_width, self.pet_height = 100, 100

        # animation data
        self.actions_full_path = pet_actions_full_path
        self.sequence_list = sequence_list
        self.weights_list = weights_list
        self.speeds_list = speeds_list
        self.actions_img_objs = {}

        self.is_drag: bool
        self.falling: bool
        self.offset_x: int
        self.offset_y: int
        self.cycle: int
        self.action_idx: int
        self.x: int
        self.y: int
        self.reset_state()

        # populate animation data
        self.process()

        # add animation to canvas
        placeholder_img = os.path.join(
            ROOT_DIR_PATH, "pets", "placeholder.png")
        self.ph = tk.PhotoImage(file=placeholder_img)
        self.image_container = self.canvas.create_image(
            self.x, self.y, anchor="nw", image=self.ph)

        # event listeners
        self.event1 = self.canvas.tag_bind(self.image_container,
                                           '<Button-1>', self.click_pet)
        self.event2 = self.canvas.tag_bind(self.image_container,
                                           '<B1-Motion>', self.drag_pet)
        self.event3 = self.canvas.tag_bind(self.image_container,
                                           '<ButtonRelease-1>', self.release_pet)

        # loop id
        self.after_id = None
        # # begin animation loop
        self.run()

    def __del__(self):
        logging.info(('Pet deleted'))

    def reset_state(self) -> None:
        self.is_drag = False
        self.falling = False
        self.offset_x, self.offset_y = 0, 0
        self.cycle = 0
        self.action_idx = 0
        self.x = int(self.screen_width*random.randrange(20, 80)*0.01)
        self.y = self.screen_height - self.pet_height  # drawing starts from top left

    def process(self) -> bool:
        try:
            actions_names = [gif for gif in os.listdir(self.actions_full_path)
                             if os.path.isfile(os.path.join(self.actions_full_path, gif))]

            if len(actions_names) == 0:
                return False

            for idx, action_name in enumerate(actions_names):
                action_full_path = os.path.join(
                    self.actions_full_path, action_name)
                action_gif = Image.open(os.path.join(
                    self.actions_full_path, action_name))
                self.actions_img_objs[idx] = [tk.PhotoImage(file=action_full_path,
                                                            format='gif -index %i' % (i)) for i in range(action_gif.n_frames)]
            return True
        except Exception as e:
            # logging.error(f'{e.message}')
            return False

    def update_frame(self) -> None:
        if self.is_drag:
            self.action_idx = len(self.sequence_list) - 1  # last action
            self.cycle = 0
            return

        if self.falling:
            self.action_idx = len(self.sequence_list) - \
                2  # second to last action
            self.cycle = 0
            return

        if self.cycle < len(self.actions_img_objs[self.action_idx]) - 1:
            self.cycle += 1
        else:  # end of an action
            self.cycle = 0
            possible_actions_indexes = [p_action_idx for p_action_idx, p_action in enumerate(
                self.sequence_list[self.action_idx]) if p_action]

            if len(possible_actions_indexes) == 0:
                # !play the current action permanently
                # if no successor actions found
                return

            # sum of remaining weights < 100%, need to scale them up...hidden/bad feature?
            possible_actions_weights = [weight for weight_idx, weight in enumerate(
                self.weights_list) if weight_idx in possible_actions_indexes]
            possible_actions_weights_scale = [
                weight/sum(possible_actions_weights) for weight in possible_actions_weights]

            self.action_idx = random.choices(
                possible_actions_indexes,
                weights=possible_actions_weights_scale,
                k=1
            )[0]

    def draw_loop(self) -> None:
        # set current frame
        frame = self.actions_img_objs[self.action_idx][self.cycle]
        self.canvas.itemconfig(self.image_container, image=frame)

        # set new frame's position
        x_dist = self.speeds_list[self.action_idx][0]
        y_dist = self.speeds_list[self.action_idx][1]

        if self.x + x_dist >= self.screen_width + (2*self.pet_width) or self.x + x_dist <= 0-self.pet_width:
            x_dist = 0
        if self.y + y_dist <= 0-self.pet_height:
            y_dist = 0
        if self.y >= self.screen_height - self.pet_height and not self.is_drag:
            self.falling = False
            if self.y > self.screen_height - self.pet_height:
                y_dist = self.screen_height - self.pet_height - self.y
            else:
                y_dist = 0

        self.x += x_dist
        self.y += y_dist
        self.canvas.move(self.image_container, x_dist, y_dist)

        # update the next frame / update next gif
        self.update_frame()

        self.after_id = self.canvas.after(100, self.draw_loop)

    def click_pet(self, event) -> None:
        self.offset_x = event.x - self.x
        self.offset_y = event.y - self.y
        self.is_drag = True

    def drag_pet(self, event) -> None:
        x_dist = event.x - self.x - self.offset_x
        y_dist = event.y - self.y - self.offset_y
        self.x = event.x - self.offset_x
        self.y = event.y - self.offset_y
        # TODO: event.widget instead
        self.canvas.move(self.image_container, x_dist, y_dist)

    def release_pet(self, event) -> None:
        self.falling = True
        self.is_drag = False

    def run(self) -> None:
        self.after_id = self.canvas.after(100, self.draw_loop)

    def release(self) -> None:
        """
        Release all resources used by this object
        before destroying instances
        NOTE:
        if events are not un-bind-ed, using del on
        instances of this object will not send 
        those instances to the garbage collector
        and they will keep taking up space until
        end of program
        """
        self.canvas.tag_unbind(self.image_container, '<Button-1>', self.event1)
        self.canvas.tag_unbind(self.image_container,
                               '<B1-Motion>', self.event2)
        self.canvas.tag_unbind(self.image_container,
                               '<ButtonRelease-1>', self.event3)

        self.canvas.after_cancel(self.after_id)
        # delete pet from main canvas
        self.canvas.delete(self.image_container)


if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE_PATH, filemode='w',
                        format='%(name)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG)
    root = App()
