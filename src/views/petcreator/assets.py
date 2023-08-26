import os
from typing import TypedDict, Any
import customtkinter
from PIL import Image
import logging
import ntpath

from utils import ASSETS_DIR

class AssetT(TypedDict):
	file_path: str
	file_name: str
	file_format: str
	image: customtkinter.CTkImage
	widget: customtkinter.CTkButton

class Assets(customtkinter.CTkFrame):
	def __init__(self, master, **kwargs):
		super().__init__(master, **kwargs)

		self._observers = {}
		logger = logging.getLogger(__name__)

		self.assets: list[AssetT] = []

		self.grid_columnconfigure((0, 1), weight=1)

		folder_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(ASSETS_DIR, "gear.png")),
											  dark_image=Image.open(os.path.join(ASSETS_DIR, "gear.png")), size=(24, 24))
	
		self.name_label = customtkinter.CTkLabel(self, text="Assets", font=customtkinter.CTkFont(size=20, weight="bold"))
		self.name_label.grid(row=0, column=0, padx=(30, 30), pady=(15, 0), sticky="w")
		self.folder_button = customtkinter.CTkButton(self, text="", fg_color="transparent", hover_color=("gray70", "gray30"),
													 image=folder_image, width=24, command=self._openFileExplorer)
		self.folder_button.grid(row=0, column=1, padx=(20, 20), pady=(15, 0), sticky="e")

		self.scrollable_frame = customtkinter.CTkScrollableFrame(self)
		self.scrollable_frame.grid(row=1, column=0, padx=(20, 20), pady=(20, 20), sticky="nsew", columnspan=2)
		
	def _openFileExplorer(self):
		file_list = customtkinter.filedialog.askopenfilenames(filetypes=[("Gif files", "*.gif")])

		if not file_list:
			return
		
		self._clear_asset_list()

		for file in file_list:
			file_name = ntpath.basename(os.path.splitext(file)[0])
			file_format = os.path.splitext(file)[1]
			image = customtkinter.CTkImage(light_image=Image.open(file), dark_image=Image.open(file), size=(20, 20))

			self.assets.append({
				"file_path": file,
				"file_name": file_name,
				"file_format": file_format,
				"image": image,
				"widget": None
			})
		
		self._update_asset_list()
	
	def _update_asset_list(self):
		for idx, asset in enumerate(self.assets):
			self.assets[idx]["widget"] = customtkinter.CTkButton(self.scrollable_frame,
																 text=f'{asset["file_name"]}{asset["file_format"]}',
																 fg_color="transparent", hover_color=("gray70", "gray30"),
																 image=asset["image"], width=24)
			self.assets[idx]["widget"].grid(row=idx, sticky="w")
		self._trigger_event("new_assets")

	def _clear_asset_list(self):
		if len(self.assets) != 0:
			self._trigger_event("clear_assets")
			for asset in self.assets:
				asset["widget"].destroy()
			self.assets = []
	
	def _trigger_event(self, event):
		if event not in self._observers.keys():
			return
		
		for func in self._observers[event]:
			func(self.assets)

	def bind_to(self, event, func):
		try:
			self._observers[event].append(func)
		except KeyError:
			self._observers[event] = [func]

		return lambda: self._observers[event].remove(func)
		# return lambda: print(self._observers, event, func)
	
	def destroy(self):
		for asset in self.assets:
			asset["widget"].destroy()
		return super().destroy()