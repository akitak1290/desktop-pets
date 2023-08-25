import numpy as np

from models.main import Model
from models.pets.pet import Pet, PetData
from views.main import View

import tkinter as tk
from PIL import ImageTk

class PetController:
	def __init__(self, model: Model, view: View, pet_data: PetData) -> None:
		self.main_canvas = view.main_canvas
		self._canvas_item_events = {}

		# pet
		self.pet_id: int = None
		self.pet: Pet = Pet(pet_data, np.array([200, 200]),
		      				{"v_bound": [0, view.monitor_width],
	     					 "h_bound": [0, view.monitor_height]})
		self._on_pet_created()

		# tracker for canvas after-loop
		self.after_loop_id: int = 0
		# self._delta_t = 17 #ms, roughly 60fps

		# offset for pet position
		self.pos_offset: np.ndarray[any] = np.array([0, 0])
		self.override_pos: np.ndarray[any]|None = None
		self.override_frame_idx: int|None = None
		
		self.pet.add_event_listener("remove_pet", self._on_remove_pet)
		# self.pet.add_event_listener("action_update", self._on_action_update)

		self.draw_pet()


	def draw_pet(self):
		if self.override_pos is None:
			self.pet.update_position()
			self.main_canvas.coords(self.pet_id, self.pet.position[0], self.pet.position[1])

		img = self.pet.actions[self.pet.action_idx][self.pet.action_frame_idx]
		self.main_canvas.itemconfig(self.pet_id, image=img)
		self.pet.update_frame(self.override_frame_idx)

		delta_time = self.pet.pet_data.playback_speeds[self.pet.action_idx]
		self.after_loop_id = self.main_canvas.after(delta_time, self.draw_pet)

	# def stop_pet(self):

	def _on_pet_created(self):
		self.pet_id = self.main_canvas.create_image(self.pet.position[0],
					      							self.pet.position[1],
													anchor="nw")
		
		self._bind_canvas_event('<Button-1>', self._click_pet)
		self._bind_canvas_event('<B1-Motion>', self._drag_pet)
		self._bind_canvas_event('<ButtonRelease-1>', self._release_pet)

	def _click_pet(self, event):
		self.pos_offset = np.array([event.x - self.pet.position[0],
			      					event.y - self.pet.position[1]])

	def _drag_pet(self, event):
		self.override_pos = np.subtract([event.x, event.y], self.pos_offset)
		self.pet.update_position(self.override_pos)
		self.main_canvas.coords(self.pet_id, self.pet.position[0], self.pet.position[1])

	def _release_pet(self, event):
		self.pos_offset = np.array([0, 0])
		self.override_pos = None

	def _on_remove_pet(self, data):
		self._unbind_canvas_event()

		self.main_canvas.delete(self.pet_id)

		self.main_canvas.after_cancel(self.after_loop_id)

	# def _on_action_update(self, data):
		# print('action_update')

	def _bind_canvas_event(self, name, func):
		try:
			self._canvas_item_events[name].append(self.main_canvas.tag_bind(self.pet_id, name, func))
		except KeyError:
			self._canvas_item_events[name] = [self.main_canvas.tag_bind(self.pet_id, name, func)]

	def _unbind_canvas_event(self):
		for key in self._canvas_item_events.key():
			for event in self._canvas_item_events[key]:
				self.main_canvas.tag_unbind(self.pet_id, key, event)

	# cleanup and release all resources
	def release(self):
		self.pet.release()
		
	# TODO: add canvas's item events
