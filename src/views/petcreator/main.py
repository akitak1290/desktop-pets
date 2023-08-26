import customtkinter
import tkinter as tk
from PIL import Image, ImageTk

from views.petcreator.assets import Assets

class PetCreator(customtkinter.CTkToplevel):
	'''
	The Pet Creator class
	! A feature: user can drag an asset from the asset view
	to the main canvas. To do this, the class needs to keep
	track of an image object to display that the asset is
	being dragged.
	'''
	def __init__(self, master: any, **kwargs):
		super().__init__(master, **kwargs)

		# Check the note for the class
		self.draggable_label: tk.Label|None = None
		self.draggable_img: customtkinter.CTkImage|None = None

		self.wrapper_canvas = tk.Canvas(master=self, width=1000, height= 600, highlightthickness=0)
		self.wrapper_canvas.pack(fill="both", expand=True, side= tk.TOP)
		self.interior = interior = customtkinter.CTkFrame(self.wrapper_canvas)
		self.interior_id = self.wrapper_canvas.create_window(0, 0, window=interior, anchor="nw")
		self.wrapper_canvas.bind("<Configure>", self._on_wrapper_canvas_resize)

		# 3x3 grid
		interior.grid_columnconfigure((0, 2), weight=1)
		interior.grid_columnconfigure(1, weight=4)

		# tabs
		self.asset_view = Assets(interior)
		self.asset_view.grid(row=0, column=0, padx=(10, 10), sticky="nsew")

		self.frame2 = customtkinter.CTkFrame(interior)
		self.frame2.grid(row=0, column=1, padx=(10, 10), sticky="nsew")

		self.frame3 = customtkinter.CTkFrame(interior)
		self.frame3.grid(row=0, column=2, padx=(10, 10), sticky="nsew")

	def _on_wrapper_canvas_resize(self, event):
		self.wrapper_canvas.itemconfigure(self.interior_id, width=event.width)

	def create_draggable_asset(self, img_path: str, start_pos: list[int]):
		self.remove_draggable_asset()
		img = Image.open(img_path)
		img = img.resize((30, 30))
		# img.putalpha(127)
		self.draggable_img = ImageTk.PhotoImage(img)
		self.draggable_label = tk.Label(self, image=self.draggable_img, highlightthickness=0)
		self.draggable_label.place(x=start_pos[0], y=start_pos[1]-15, anchor="n")

	def drag_asset(self, pos: list[int]):
		if self.draggable_label is not None:
			self.draggable_label.place(x=pos[0], y=pos[1]-15, anchor="n")

	def remove_draggable_asset(self):
		if self.draggable_label is not None:
			self.draggable_label.destroy()
			self.draggable_label = None
			self.draggable_img = None