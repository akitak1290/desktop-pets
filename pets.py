import os
import random
from win32api import GetMonitorInfo, MonitorFromPoint

import tkinter as tk
from PIL import Image

dir_path = os.path.dirname(os.path.realpath(__file__))
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

# Abstract away the root window use by multiple Pet instances
class Window:
    def __init__(self) -> None:
        # creating window
        self.window = tk.Tk()

        # additional metadata
        monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
        work_area = monitor_info.get("Work")
        self.screen_width = work_area[2]
        self.screen_height = work_area[3]

        # config window
        self.window.config(highlightbackground='black')
        self.window.config(bg='black')
        self.window.wm_attributes('-transparentcolor', 'black')
        self.window.overrideredirect(True)
        self.window.call("wm", "attributes", ".", "-topmost", "true")
        self.window.geometry(str(self.screen_width)+'x' +
                             str(self.screen_height)+'+0+0')

        # canvas to display pets
        self.canvas = tk.Canvas(self.window, width=self.screen_width,
                                height=self.screen_height, bd=0, highlightthickness=0)
        self.canvas.config(bg='black')
        self.canvas.place(x=0, y=0)

        # button to add pet
        tk.Button(self.window, text="Add pets", command=self.add_label).pack()

        # initiate the app
        self.run()

    def add_label(self) -> None:
        pet = Pet(self, cat_path, sequence, weights, speeds)
        pet.run()


    def run(self) -> None:
        print('Pets are chilling... (Press Ctrl+C to kill the pets!)')
        self.window.mainloop()  # move this to Window()


class Pet(Window):
    def __init__(self, root_window, pet_actions_full_path, sequence_list, weights_list, speeds_list) -> None:
        # root window
        self.root_window = root_window

        self.screen_width = root_window.screen_width
        self.screen_height = root_window.screen_height

        # animation data
        self.actions_full_path = pet_actions_full_path
        self.sequence_list = sequence_list
        self.weights_list = weights_list
        self.speeds_list = speeds_list
        self.actions_img_objs = {}
        self.is_drag = False
        self.falling = False
        self.offset_x, self.offset_y = 0, 0

        self.cycle = 0
        self.action_idx = 0
        self.x = int(self.screen_width*random.randrange(20, 80)*0.01)
        # TODO: magic number is model height
        self.y = self.screen_height - 100

        # populate animation data
        self.process()

        # add animation to root_window.canvas
        self.canvas = root_window.canvas
        self.ph = tk.PhotoImage(file=placeholder_img)

        self.image_container = self.canvas.create_image(
            self.x, self.y, anchor=tk.NW, image=self.ph)
        
        # event listeners
        self.canvas.tag_bind(self.image_container, '<Button-1>', self.click_pet)
        self.canvas.tag_bind(self.image_container, '<B1-Motion>', self.drag_pet)
        self.canvas.tag_bind(self.image_container, '<ButtonRelease-1>', self.release_pet)

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

        if self.x + x_dist >= self.screen_width + 200 or self.x + x_dist <= -100:
            x_dist = 0
        if self.y + y_dist <= -100:
             y_dist = 0
        if self.y >= self.screen_height - 100 and not self.is_drag:
            self.falling = False
            if self.y > self.screen_height - 100:
                y_dist = self.screen_height - 100 - self.y
            else:
                y_dist = 0

        self.x += x_dist
        self.y += y_dist
        self.canvas.move(self.image_container, x_dist, y_dist)

        # update the next frame / update next gif
        self.update_frame()

        # loop, refresh rate = 10/sec
        self.root_window.window.after(100, self.draw_loop)

    def click_pet(self, event) -> None:
        self.offset_x = event.x - self.x
        self.offset_y = event.y - self.y
        self.is_drag = True

    def drag_pet(self, event) -> None:
        x_dist = event.x - self.x - self.offset_x
        y_dist = event.y - self.y - self.offset_y
        self.x = event.x - self.offset_x
        self.y = event.y - self.offset_y
        self.canvas.move(self.image_container, x_dist, y_dist)
    
    def release_pet(self, event) -> None:
        self.falling = True
        self.is_drag = False

    def run(self) -> None:
        self.root_window.window.after(1, self.draw_loop)


root_window = Window()
