import customtkinter
import tkinter as tk
from PIL import Image, ImageTk
from utils import AssetT, DraggableAssetT

from views.petcreator.assets import Assets
from views.petcreator.editcanvas import EditCanvas

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
		self._latest_draggable_asset: DraggableAssetT|None = None

		self.grid_rowconfigure(0, weight=1)
		self.grid_columnconfigure(0, weight=1)

		self.interior = interior = customtkinter.CTkFrame(self)
		self.interior.grid(row=0, column=0, sticky="news")

		# 3x3 grid
		self.interior.grid_columnconfigure((0, 2), weight=1)
		self.interior.grid_columnconfigure(1, weight=4)
		self.interior.grid_rowconfigure((0, 2), weigh=5)
		self.interior.grid_rowconfigure(1, weight=1)

		# tabs
		self.asset_view = Assets(interior)
		self.asset_view.grid(row=0, column=0, padx=(10, 10), sticky="nsew", rowspan=1)

		self.edit_canvas = EditCanvas(interior)
		self.edit_canvas.grid(row=0, column=1, padx=(10, 10), sticky="nsew", rowspan=3)

		self.frame3 = customtkinter.CTkFrame(interior)
		self.frame3.grid(row=0, column=2, padx=(10, 10), sticky="nsew", rowspan=2)

		self.frame4 = customtkinter.CTkFrame(interior)
		self.frame4.grid(row=1, column=0, padx=(10, 10), sticky="nsew", rowspan=2)

	def create_draggable_asset(self, const_asset: AssetT, start_pos: list[int]):
		self.remove_draggable_asset()
		img = Image.open(const_asset["file_path"])
		img = img.resize((30, 30))
		_draggable_img = ImageTk.PhotoImage(img)
		self._latest_draggable_asset = {
			"img": _draggable_img,
			"widget": tk.Label(self, image=_draggable_img, highlightthickness=0),
			"file_path": const_asset["file_path"],
			"file_name": const_asset["file_name"],
			"file_format": const_asset["file_format"]
		}
		self._latest_draggable_asset["widget"].place(x=start_pos[0], y=start_pos[1]-15, anchor="n")

		return const_asset["file_path"]
		
	def drag_asset(self, pos: list[int]):
		if self._latest_draggable_asset is not None:
			if self._latest_draggable_asset["widget"] is not None:
				self._latest_draggable_asset["widget"].place(x=pos[0], y=pos[1]-15, anchor="n")

	def remove_draggable_asset(self):
		if self._latest_draggable_asset is not None:
			if self._latest_draggable_asset["widget"] is not None:
				self._latest_draggable_asset["widget"].destroy()
				self._latest_draggable_asset["widget"] = None

			self._latest_draggable_asset = None
	
	def remove_draggable_asset_widget(self):
		if self._latest_draggable_asset is not None:
			if self._latest_draggable_asset["widget"] is not None:
				self._latest_draggable_asset["widget"].destroy()
				self._latest_draggable_asset["widget"] = None