import os
from pathlib import Path
from typing import TypedDict, Any
import tkinter as tk
import customtkinter
from PIL import ImageTk

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
ASSETS_DIR = os.path.join(Path(__file__).absolute().parent.parent, 'assets')

class AssetT(TypedDict):
	file_path: str
	file_name: str
	file_format: str
	image: customtkinter.CTkImage
	widget: customtkinter.CTkButton|None

class DraggableAssetT(TypedDict):
	img: ImageTk.PhotoImage
	widget: tk.Label|None
	file_path: str
	file_name: str
	file_format: str