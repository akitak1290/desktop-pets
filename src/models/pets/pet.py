from dataclasses import dataclass
import random
import numpy as np
import os
from PIL import Image
from PIL.Image import Image as pilImg

from tkinter import PhotoImage

from models.base import ObservableModel

# TODO: specify that movement speed is pixel per frame!!!
@dataclass
class PetData:
	''' Class to keep track of data that describe a pet, to store/load/create pets'''
	def __init__(self, sequence, weights, movement_speeds, playback_speeds, storage_path) -> None:
		''' 
		A 2d integer list mapping the next possible actions  for
		each available action, value can be either 0 or 1 for
		False or True
		'''
		self.sequence: list[list[int]] = sequence

		'''
		A list of floating numbers, value ranges from 0 to 1,
		to indicate the chance the chance of a next possible action
		'''
		self.weights: list[float] = weights

		'''
		A list of tuple of 2 int, representing vertical speed and
		horizontal speed of each action, direction on each axes is
		shown by the value being negative or positive
		'''	
		self.movement_speeds: list[list[int]] = movement_speeds

		'''
		A list of int, representing the playback speed of each 
		action in milliseconds, value should be from 1 to 1000
		'''
		self.playback_speeds: list[int] = playback_speeds

		'''
		Path to image/gif resource
		'''
		self.storage_path: str = storage_path

class Pet(ObservableModel):
	'''
	In charge of storing, loading, drawing, updating a
	pet (a tkinter pet frame)
	Keep track of:
		animation data for each action,
		current pet position on the the desktop plane,
		list of image(action) sequences,
		and a tracker to the current action + a tracker to current action's frame index

	TODO: add def for options parameter
	'''
	def __init__(self, pet_data: PetData, start_pos: np.ndarray[any], options: {}):
		super().__init__()
		self.pet_data: PetData = pet_data
		self.position: np.ndarray[any] = start_pos.copy()

		self.actions = {}
		self.action_frame_idx: int = 0
		self._process_images()

		self.action_idx: int = 0

		self.options = options

		self.trigger_event("new_pet")

	# get image/gif resource
	def _process_images(self):
		storage_path: str = self.pet_data.storage_path
		try:
			actions_names: list[str] = [gif for gif in os.listdir(storage_path)
							 			if os.path.isfile(os.path.join(storage_path, gif))]

			if len(actions_names) == 0:
				return False

			for idx, action_name in enumerate(actions_names):
				action_full_path: str = os.path.join(storage_path, action_name)
				action_gif: pilImg = Image.open(action_full_path)
				self.actions[idx] = [PhotoImage(file=action_full_path,
				    							format='gif -index %i' % (i)) for i in range(action_gif.n_frames)]

			return True
		except Exception as e:
			# logging.error(f'{e.message}')
			return False
		
	# update pet position
	# if new_pos is not specified,
	# update position using internal data
	def update_position(self, new_pos: np.ndarray[any]|None=None):
		if new_pos is not None:
			self.position = new_pos.copy()
			return

		speed_v = np.array(self.pet_data.movement_speeds[self.action_idx])

		keys = self.options.keys()
		if "v_bound" in keys and "h_bound" in keys:
			# border checking
			v_border = self.options["v_bound"]
			h_border = self.options["h_bound"]
			new_pos = np.add(self.position, speed_v)

			if new_pos[0] >= v_border[1] or new_pos[0] <= v_border[0]:
				new_pos[0] = self.position[0]

			self.position = new_pos
		else:
			self.position = np.add(self.position, speed_v)
		# ! Border checking
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

	# release resources
	def release(self):
		self.trigger_event("remove_pet")

	# move to the next frame or next action
	def update_frame(self, new_frame_idx):
		if new_frame_idx:
			if self.action_idx != new_frame_idx:
				self.action_idx = new_frame_idx
			else:
				if self.action_frame_idx < len(self.actions[self.action_idx]) - 1:
					# still more frames, go to next frame
					self.action_frame_idx += 1
				else:
					self.action_frame_idx = 0
			return

		if self.action_frame_idx < len(self.actions[self.action_idx]) - 1:
			# still more frames, go to next frame
			self.action_frame_idx += 1
		else:
			# no more frame, restart frame index for later and go to next action
			self.action_frame_idx = 0
			sequence_list = self.pet_data.sequence
			possible_actions_indexes = [p_action_idx for p_action_idx, p_action in enumerate(
	           							sequence_list[self.action_idx]) if p_action]

			if len(possible_actions_indexes) == 0:
				# !play the current action permanently
				# !if no successor actions found
				return

			weights_list = self.pet_data.weights
			possible_actions_weights = [weight for weight_idx, weight in enumerate(
                						weights_list) if weight_idx in possible_actions_indexes]
			# sum of remaining weights < 100%, need to scale them up...hidden/bad feature?
			possible_actions_weights_scale = [weight/sum(possible_actions_weights) 
				     						  for weight in possible_actions_weights]
			
			# TODO: fix weights to be more accurate
			self.action_idx = random.choices(
                possible_actions_indexes,
                weights=possible_actions_weights_scale,
                k=1
            )[0]

		self.trigger_event("action_update")

	# play
	# def play_pet(self):

	# 	self.trigger_event("action_update")

	# set_action