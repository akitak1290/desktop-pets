import customtkinter
import os
from PIL import Image
import logging
import ntpath

from utils import ASSETS_DIR

class Assets(customtkinter.CTkFrame):
	def __init__(self, master, **kwargs):
		super().__init__(master, **kwargs)

		logger = logging.getLogger(__name__)

		self.assets = []

		self.grid_columnconfigure((0, 1), weight=1)

		folder_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(ASSETS_DIR, "gear.png")),
											  dark_image=Image.open(os.path.join(ASSETS_DIR, "gear.png")), size=(24, 24))
	
		self.name_label = customtkinter.CTkLabel(self, text="Assets", font=customtkinter.CTkFont(size=20, weight="bold"))
		self.name_label.grid(row=0, column=0, padx=(30, 30), pady=(15, 0), sticky="w")
		self.folder_button = customtkinter.CTkButton(self, text="", fg_color="transparent", hover_color=("gray70", "gray30"),
													 image=folder_image, width=24, command=self.openFileExplorer)
		self.folder_button.grid(row=0, column=1, padx=(20, 20), pady=(15, 0), sticky="e")

		self.scrollable_frame = customtkinter.CTkScrollableFrame(self)
		self.scrollable_frame.grid(row=1, column=0, padx=(20, 20), pady=(20, 20), sticky="nsew", columnspan=2)
		
	def openFileExplorer(self):
		file_list = customtkinter.filedialog.askopenfilenames(filetypes=[("Gif files", "*.gif")])

		if not file_list:
			return
		
		for asset in self.assets:
			asset["widget"].destroy()
		self.assets = []

		for file in file_list:
			file_name = ntpath.basename(os.path.splitext(file)[0])
			file_format = os.path.splitext(file)[1]
			image = customtkinter.CTkImage(light_image=Image.open(file), dark_image=Image.open(file), size=(20, 20))

			self.assets.append({
				"file": file,
				"file_name": file_name,
				"file_format": file_format,
				"image": image,
				"widget": None
			})
		
		self.update_asset_list()
	
	def update_asset_list(self):
		for idx, asset in enumerate(self.assets):
			self.assets[idx]["widget"] = customtkinter.CTkButton(self.scrollable_frame,
																 text=f'{asset["file_name"]}{asset["file_format"]}',
																 fg_color="transparent", hover_color=("gray70", "gray30"),
																 image=asset["image"], width=24)
			self.assets[idx]["widget"].grid(row=idx, sticky="w")