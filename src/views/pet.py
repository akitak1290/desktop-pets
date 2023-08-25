

# TODO: add playback speed to Pet
# although, playback speed should not be conflicted
# with x speed and y speed
class Pet():
    def __init__(self,
                 canvas,
                 pet_actions_full_path,
                 sequence_list,
                 weights_list,
                 speeds_list) -> None:
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

    # def __del__(self):
    #     logging.info(('Pet deleted'))

    # def reset_state(self) -> None:
    #     self.is_drag = False
    #     self.falling = False
    #     self.offset_x, self.offset_y = 0, 0
    #     self.cycle = 0
    #     self.action_idx = 0
    #     self.x = int(self.screen_width*random.randrange(20, 80)*0.01)
    #     self.y = self.screen_height - self.pet_height  # drawing starts from top left

    # def process(self) -> bool:
    #     try:
    #         actions_names = [gif for gif in os.listdir(self.actions_full_path)
    #                          if os.path.isfile(os.path.join(self.actions_full_path, gif))]

    #         if len(actions_names) == 0:
    #             return False

    #         for idx, action_name in enumerate(actions_names):
    #             action_full_path = os.path.join(
    #                 self.actions_full_path, action_name)
    #             action_gif = Image.open(os.path.join(
    #                 self.actions_full_path, action_name))
    #             self.actions_img_objs[idx] = [tk.PhotoImage(file=action_full_path,
    #                                                         format='gif -index %i' % (i)) for i in range(action_gif.n_frames)]
    #         return True
    #     except Exception as e:
    #         # logging.error(f'{e.message}')
    #         return False

    # def update_frame(self) -> None:
    #     if self.is_drag:
    #         self.action_idx = len(self.sequence_list) - 1  # last action
    #         self.cycle = 0
    #         return

    #     if self.falling:
    #         self.action_idx = len(self.sequence_list) - \
    #             2  # second to last action
    #         self.cycle = 0
    #         return

    #     if self.cycle < len(self.actions_img_objs[self.action_idx]) - 1:
    #         self.cycle += 1
    #     else:  # end of an action
    #         self.cycle = 0
    #         possible_actions_indexes = [p_action_idx for p_action_idx, p_action in enumerate(
    #             self.sequence_list[self.action_idx]) if p_action]

    #         if len(possible_actions_indexes) == 0:
    #             # !play the current action permanently
    #             # if no successor actions found
    #             return

    #         # sum of remaining weights < 100%, need to scale them up...hidden/bad feature?
    #         possible_actions_weights = [weight for weight_idx, weight in enumerate(
    #             self.weights_list) if weight_idx in possible_actions_indexes]
    #         possible_actions_weights_scale = [
    #             weight/sum(possible_actions_weights) for weight in possible_actions_weights]

    #         self.action_idx = random.choices(
    #             possible_actions_indexes,
    #             weights=possible_actions_weights_scale,
    #             k=1
    #         )[0]

    # def draw_loop(self) -> None:
    #     # set current frame
    #     frame = self.actions_img_objs[self.action_idx][self.cycle]
    #     self.canvas.itemconfig(self.image_container, image=frame)

    #     # set new frame's position
    #     x_dist = self.speeds_list[self.action_idx][0]
    #     y_dist = self.speeds_list[self.action_idx][1]

    #     if self.x + x_dist >= self.screen_width + (2*self.pet_width) or self.x + x_dist <= 0-self.pet_width:
    #         x_dist = 0
    #     if self.y + y_dist <= 0-self.pet_height:
    #         y_dist = 0
    #     if self.y >= self.screen_height - self.pet_height and not self.is_drag:
    #         self.falling = False
    #         if self.y > self.screen_height - self.pet_height:
    #             y_dist = self.screen_height - self.pet_height - self.y
    #         else:
    #             y_dist = 0

    #     self.x += x_dist
    #     self.y += y_dist
    #     self.canvas.move(self.image_container, x_dist, y_dist)

    #     # update the next frame / update next gif
    #     self.update_frame()

    #     self.after_id = self.canvas.after(100, self.draw_loop)

    # def click_pet(self, event) -> None:
    #     self.offset_x = event.x - self.x
    #     self.offset_y = event.y - self.y
    #     self.is_drag = True

    # def drag_pet(self, event) -> None:
    #     x_dist = event.x - self.x - self.offset_x
    #     y_dist = event.y - self.y - self.offset_y
    #     self.x = event.x - self.offset_x
    #     self.y = event.y - self.offset_y
    #     # TODO: event.widget instead
    #     self.canvas.move(self.image_container, x_dist, y_dist)

    # def release_pet(self, event) -> None:
    #     self.falling = True
    #     self.is_drag = False

    # def run(self) -> None:
    #     self.after_id = self.canvas.after(100, self.draw_loop)

    # def release(self) -> None:
    #     """
    #     Release all resources used by this object
    #     before destroying instances
    #     NOTE:
    #     if events are not un-bind-ed, using del on
    #     instances of this object will not send 
    #     those instances to the garbage collector
    #     and they will keep taking up space until
    #     end of program
    #     """
    #     self.canvas.tag_unbind(self.image_container, '<Button-1>', self.event1)
    #     self.canvas.tag_unbind(self.image_container,
    #                            '<B1-Motion>', self.event2)
    #     self.canvas.tag_unbind(self.image_container,
    #                            '<ButtonRelease-1>', self.event3)

    #     self.canvas.after_cancel(self.after_id)
    #     # delete pet from main canvas
    #     self.canvas.delete(self.image_container)
