from typing import Optional, Tuple, Union
import customtkinter
import tkinter as tk

from views.petcreator.assets import Assets

class PetCreator(customtkinter.CTkToplevel):
	def __init__(self, master: any, **kwargs):
		super().__init__(master, **kwargs)

		self.wrapper_canvas = tk.Canvas(master=self, width=1000, height= 600, highlightthickness=0)
		self.wrapper_canvas.pack(fill="both", expand=True)
		self.interior = interior = customtkinter.CTkFrame(self.wrapper_canvas)
		self.interior_id = self.wrapper_canvas.create_window(0, 0, window=interior, anchor="nw")
		self.wrapper_canvas.bind("<Configure>", self._on_wrapper_canvas_resize)

		# 3x3 grid
		interior.grid_columnconfigure((0, 2), weight=1)
		interior.grid_columnconfigure(1, weight=4)

		# tabs
		self.frame1 = Assets(interior)
		self.frame1.grid(row=0, column=0, padx=(10, 10), sticky="nsew")

		self.frame2 = customtkinter.CTkFrame(interior)
		self.frame2.grid(row=0, column=1, padx=(10, 10), sticky="nsew")

		self.frame3 = customtkinter.CTkFrame(interior)
		self.frame3.grid(row=0, column=2, padx=(10, 10), sticky="nsew")

	def _on_wrapper_canvas_resize(self, event):
		self.wrapper_canvas.itemconfigure(self.interior_id, width=event.width)

	def __del__(self):
		print('destroy')