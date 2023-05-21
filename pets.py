import os
import sys
import random
import math
import json
import ntpath
from collections import OrderedDict
from win32api import GetMonitorInfo, MonitorFromPoint

import tkinter as tk
from tkinter import filedialog
from PIL import Image

"""
TODO:
    handle Setting frame resize? is static atm
    add static typing for class variables
    add json struct and json validator for configs
    refactor PetCreator to subclasses
"""

dir_path = os.path.dirname(os.path.realpath(__file__))
pets_path = os.path.join(dir_path, "pets")
cat_path = os.path.join(dir_path, "pets", "demo_cat")

placeholder_img = os.path.join(dir_path, "pets", "placeholder.png")

sequence = [
    [1, 0, 0, 1, 0, 0, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 0, 0],
    [1, 0, 0, 0, 0, 0, 1, 1],
    [1, 0, 0, 1, 0, 0, 1, 1],
    [1, 0, 0, 1, 0, 0, 1, 1]
]
weights = [0.3, 0, 0, 0.1, 0.3, 0.1, 0.1, 0.1]
speeds = [(0, 0), (0, 10), (0, 0), (0, 0), (0, 0), (0, 0), (-3, 0), (3, 0)]

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
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.pet_config_path = os.path.join(dir_path, "configs.json")
        self.pets_path = os.path.join(dir_path, "pets")

        self.pets = {}

        pet_configs = None
        with open(self.pet_config_path) as config_json:
            pet_configs = json.load(config_json)

        for config_dict in pet_configs:
            abs_path = config_dict["abs_path"]
            config = PetConfigStruct(sequence=config_dict["sequence"],
                                     weights=config_dict["weights"],
                                     movement_speeds=config_dict["movement_speeds"],
                                     playback_speeds=config_dict["playback_speeds"])
            # pet = Pet(canvas=self.canvas,
            #           pet_actions_full_path=abs_path,
            #           sequence_list=config.sequence,
            #           weights_list=config.weights,
            #           speeds_list=config.movement_speeds)

            self.pets[ntpath.basename(abs_path)] = {
                "abs_path": abs_path,
                "config": config
            }

        Setting(self)

        # event listener
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # initiate the app
        self.run()

    def add_pet() -> None:
        # pet = Pet(self.root_window, cat_path, sequence, weights, speeds)
        # pet.run()
        pass

    def remove_pet() -> None:
        pass

    def create_pet() -> None:
        pass

    def on_closing(self) -> None:
        with open(self.pet_config_path, "w") as config_json:
            data = []
            for pet_name, pet in self.pets.items():
                pet_config = pet["config"]
                data.append({
                    "sequence": pet_config.sequence,
                    "weights": pet_config.weights,
                    "movement_speeds": pet_config.movement_speeds,
                    "playback_speeds": pet_config.playback_speeds,
                    "abs_path": pet["abs_path"]
                })
            json.dump(data, config_json)
        self.destroy()

    def run(self) -> None:
        print('Pets are chilling... (Press Ctrl+C to kill the pets!)')
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


class Setting(tk.Frame):
    def __init__(self, root_window) -> None:
        tk.Frame.__init__(self, root_window)
        # setting window
        self.root_window = root_window
        dir_path = os.path.dirname(os.path.realpath(__file__))
        pets_path = os.path.join(dir_path, "pets")
        available_pets = [1, 2, 3, 4, 5, 6]

        max_column = 4
        frame_height, frame_wide = 100, 100
        padding = 0

        self.main_frame = tk.Frame(root_window)
        self.pet_create_panel = tk.Frame(self.main_frame, bd=0, bg="#060522")
        self.selection_panel = tk.Frame(self.main_frame, bd=0, bg="#060522")
        self.left_menu = tk.Frame(self.selection_panel, bd=0)
        self.right_menu = tk.Frame(self.selection_panel, bd=0)

        self.main_frame.grid()
        self.pet_create_panel.grid(column=0, row=0, sticky='news')
        self.selection_panel.grid(column=0, row=0, sticky='news')
        self.selection_panel.grid()
        self.left_menu.grid(column=0, row=0, sticky="n")
        self.right_menu.grid(column=1, row=0)

        tk.Button(self.left_menu, text='All pets',
                  command=lambda: available_pets_frame.tkraise()).pack(expand=True, fill="x")
        tk.Button(self.left_menu, text='Current pets',
                  command=lambda: current_pets_frame.tkraise()).pack(expand=False, fill="x")

        tk.Button(self.pet_create_panel, text="Back",
                  command=lambda: self.selection_panel.tkraise()).grid(row=0, column=0, sticky='w')
        PetCreator(self.pet_create_panel).grid(column=0, row=1, sticky='news')

        available_pets_frame = tk.Frame(self.right_menu)
        current_pets_frame = tk.Frame(self.right_menu)
        add_pet_frame = tk.Frame(self.right_menu)
        available_pets_frame.grid(column=0, row=1, sticky='news')
        current_pets_frame.grid(column=0, row=1, sticky='news')
        add_pet_frame.grid(column=0, row=1, sticky='news')

        self.ph = tk.PhotoImage(file=placeholder_img)

        pet_cnt = 0
        labels = []
        for row_idx in range(math.ceil(len(available_pets)/max_column)):
            for column_idx in range(max_column):
                labels.append(tk.Label(available_pets_frame, image=self.ph))
                labels[pet_cnt].grid(
                    column=column_idx, row=row_idx, padx=padding, pady=padding)
                labels[pet_cnt].bind('<Enter>', )
                pet_cnt += 1
                if pet_cnt == len(available_pets):
                    break

        tk.Button(self.right_menu, text="Create new pet",
                  command=lambda: self.pet_create_panel.tkraise()).grid(row=0, column=0, sticky='e')

        # button to close the window
        tk.Button(root_window, text="Quit",
                  command=root_window.destroy).grid()

    # def toggle_setting(self) -> None:
    #     self.frame.grid_forget() if self.frame.winfo_manager() else self.frame.grid()


class PetCreator(tk.Frame):
    def __init__(self, root) -> None:
        tk.Frame.__init__(self, root)

        dir_path = os.path.dirname(os.path.realpath(
            __file__))  # refactor all usage of this
        add_icon = os.path.join(dir_path, "assets", "add.PNG")
        self.add_icon_pht_obj = tk.PhotoImage(file=add_icon)

        # canvas
        self.canvas_state = CanvasState.SCROLLABLE

        # config settings
        self.connection_dict = {}
        self.canvas_item_dict = OrderedDict()
        self.config_dict = {}

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

        self.canvas = tk.Canvas(
            self, width=400, height=400, background="bisque")
        self.scrollbar_x = tk.Scrollbar(
            self, orient="horizontal", command=self.canvas.xview)
        self.scrollbar_y = tk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview)
        # add scrollbar to canvas
        self.canvas.configure(
            yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)
        self.canvas.configure(scrollregion=(0, 0, 1000, 1000))

        self.scrollbar_x.grid(row=1, column=0, sticky="we")
        self.scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.canvas.grid(row=0, column=0, sticky="news")
        # grow canvas to frame
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas.bind("<ButtonPress-1>", self.scroll_start)
        self.canvas.bind("<B1-Motion>", self.scroll_move)
        self.canvas.bind("<Motion>", self.hover_on_canvas)
        self.canvas.bind("<Leave>", self.leave_canvas)

        tk.Button(self, text="New", command=self.create_new).grid(
            row=0, column=0, sticky='ne')

        self.config_frame = tk.Frame(self)
        self.config_frame.grid(column=2, row=0, sticky="n")

        self.name_var = tk.StringVar(self.config_frame, "")
        self.m_speed_var_x = tk.IntVar(self.config_frame, 0)
        self.m_speed_var_y = tk.IntVar(self.config_frame, 0)
        self.p_speed_var = tk.IntVar(self.config_frame, 0)
        # 10, 20, 30
        self.chance_options = [
            "Rare",
            "Normal",
            "Frequent"
        ]  # etc
        self.chance = tk.StringVar(self.config_frame, self.chance_options[0])

        self.name_var.trace_add("write", lambda name,
                                index, mode: self.set_name())
        self.m_speed_var_x.trace_add("write", lambda name,
                                index, mode: self.set_m_speed_x())
        self.m_speed_var_y.trace_add("write", lambda name,
                                index, mode: self.set_m_speed_y())
        self.p_speed_var.trace_add("write", lambda name,
                                index, mode: self.set_p_speed_var())
        self.chance.trace_add("write", lambda name,
                                index, mode: self.set_chance())

        name_label = tk.Label(
            self.config_frame, text='Name: ', font=('calibre', 10, 'bold'))
        name_entry = tk.Entry(
            self.config_frame, textvariable=self.name_var, font=('calibre', 10, 'normal'))

        m_speed_x_label = tk.Label(
            self.config_frame, text='Movement Speed x: ', font=('calibre', 10, 'bold'))
        m_speed_x_entry = tk.Entry(
            self.config_frame, textvariable=self.m_speed_var_x, font=('calibre', 10, 'normal'))
        m_speed_y_label = tk.Label(
            self.config_frame, text='Movement Speed y: ', font=('calibre', 10, 'bold'))
        m_speed_y_entry = tk.Entry(
            self.config_frame, textvariable=self.m_speed_var_y, font=('calibre', 10, 'normal'))

        p_speed_label = tk.Label(
            self.config_frame, text='Playback Speed: ', font=('calibre', 10, 'bold'))
        p_speed_entry = tk.Entry(
            self.config_frame, textvariable=self.p_speed_var, font=('calibre', 10, 'normal'))

        chance_label = tk.Label(
            self.config_frame, text='Chance: ', font=('calibre', 10, 'bold'))
        chance_entry = tk.OptionMenu(
            self.config_frame, self.chance, *self.chance_options)

        name_label.grid(column=0, row=0, sticky="nw")
        name_entry.grid(column=1, row=0, sticky="n")

        m_speed_x_label.grid(column=0, row=1, sticky="nw")
        m_speed_x_entry.grid(column=1, row=1, sticky="n")

        m_speed_y_label.grid(column=0, row=2, sticky="nw")
        m_speed_y_entry.grid(column=1, row=2, sticky="n")

        p_speed_label.grid(column=0, row=3, sticky="nw")
        p_speed_entry.grid(column=1, row=3, sticky="n")

        chance_label.grid(column=0, row=4, sticky="nw")
        chance_entry.grid(column=1, row=4, sticky="n")

        self.disable_config()

        tk.Button(self, text="Submit", command=self.submit).grid(
            row=2, column=2, sticky='e')

    # load gif and create canvas items
    def create_new(self) -> None:
        # TODO: refactor this

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

        file_list = filedialog.askopenfilenames(
            filetypes=[("Gif files", "*.gif")])

        if not file_list:
            return

        self.object_id = [-1]*(len(file_list))

        for idx, file in enumerate(file_list):
            # setup canvas's items
            x = random.randint(0, 400)
            y = random.randint(0, 400)
            file_name = ntpath.basename(file)
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
                "chance": self.chance_options[0]
            }

            # canvas's items' event listeners
            self.canvas.tag_bind(img_id, '<Enter>', self.enter)
            self.canvas.tag_bind(img_id, '<Button-1>', lambda event,
                                 img_id=img_id: self.click_action_item(event, img_id=img_id))
            self.canvas.tag_bind(img_id, '<ButtonRelease-1>', self.release)
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
                self.current_img_id = None #! this has to be called before sets
                self.name_var.set("")
                self.m_speed_var_x.set(0)
                self.m_speed_var_y.set(0)
                self.p_speed_var.set(0)
                self.chance.set(self.chance_options[0])

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
            x, y, x, y, fill="black", width=2)
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

    def delete_line(self, event) -> None:
        pass

    def enter(self, event) -> None:
        pass

    def click_action_item(self, event, img_id) -> None:
        if self.canvas_state == CanvasState.CONNECTING:
            # don't drag if a connection is underway
            if self.connection_dict[self.current_connection_id]["start"] == img_id:
                # connection has to be between 2 different actions
                return

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
         
            self.current_connection_id = None
            self.set_canvas_state(CanvasState.SCROLLABLE)

        elif self.canvas_state == CanvasState.SCROLLABLE:
            self.canvas.tag_raise(img_id)
            self.canvas.tag_raise(self.canvas_item_dict[img_id]["text_id"])
            self.canvas.tag_raise(self.canvas_item_dict[img_id]["add_id"])

            self.enable_config()
            self.current_img_id = img_id # !this has to be called before sets
            self.name_var.set(self.config_dict[img_id]["file_name"])
            self.m_speed_var_x.set(self.config_dict[img_id]["m_speed_x"])
            self.m_speed_var_y.set(self.config_dict[img_id]["m_speed_y"])
            self.p_speed_var.set(self.config_dict[img_id]["p_speed"])
            self.chance.set(self.config_dict[img_id]["chance"])

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

    def release(self, event) -> None:
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
            if self.m_speed_var_x.get() != "":
                self.config_dict[self.current_img_id]["m_speed_x"] = self.m_speed_var_x.get()

    def set_m_speed_y(self) -> None:
        if self.current_img_id != None:
            if self.m_speed_var_y.get() != "":
                self.config_dict[self.current_img_id]["m_speed_y"] = self.m_speed_var_y.get()

    def set_p_speed_var(self) -> None:
        if self.current_img_id != None:
            if self.p_speed_var.get() != "":
                self.config_dict[self.current_img_id]["p_speed"] = self.p_speed_var.get()

    def set_chance(self) -> None:
        if self.current_img_id != None:
            self.config_dict[self.current_img_id]["chance"] = self.chance.get()

    # submit
    def submit(self, event) -> None:
        pass

    # Utils
    def random_pet_name(self, cnt) -> None:
        # TODO
        return ['John Doe']*cnt

    def disable_config(self) -> None:
        for child in self.config_frame.winfo_children():
            child.configure(state='disabled')

    def enable_config(self) -> None:
        for child in self.config_frame.winfo_children():
            child.configure(state='normal')

    # Debug
    def set_canvas_state(self, state) -> None:
        self.canvas_state = state
        states = {
            1: "scrollable",
            2: "draggable",
            3: "connecting"
        }
        print(str(sys._getframe(1).f_code.co_name) +
              " set state: " + str(states[state]))


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
        self.ph = tk.PhotoImage(file=placeholder_img)
        self.image_container = self.canvas.create_image(
            self.x, self.y, anchor="nw", image=self.ph)

        # event listeners
        self.canvas.tag_bind(self.image_container,
                             '<Button-1>', self.click_pet)
        self.canvas.tag_bind(self.image_container,
                             '<B1-Motion>', self.drag_pet)
        self.canvas.tag_bind(self.image_container,
                             '<ButtonRelease-1>', self.release_pet)

        # loop id
        self.after_id = None
        # # begin animation loop
        # self.run()

    def reset_state(self) -> None:
        self.is_drag = False
        self.falling = False
        self.offset_x, self.offset_y = 0, 0
        self.cycle = 0
        self.action_idx = 0
        self.x = int(self.screen_width*random.randrange(20, 80)*0.01)
        self.y = self.screen_height - self.pet_height  # drawing starts from top left

    def process(self) -> bool:
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

    def update_frame(self) -> None:
        if self.is_drag:
            self.action_idx = 2
            self.cycle = 0
            return

        if self.falling:
            self.action_idx = 1
            self.cycle = 0
            return

        if self.cycle < len(self.actions_img_objs[self.action_idx]) - 1:
            self.cycle += 1
        else:  # end of an action
            self.cycle = 0
            possible_actions_indexes = [p_action_idx for p_action_idx, p_action in enumerate(
                self.sequence_list[self.action_idx]) if p_action]
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

        # self.canvas.after(100, self.draw_loop)

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

    def stop(self) -> None:
        # self.image_container.destroy()
        self.canvas_cancel(self.after_id)
        self.reset_state()

    def run(self) -> None:
        self.after_id = self.canvas.after(100, self.draw_loop)


if __name__ == "__main__":
    root = App()
