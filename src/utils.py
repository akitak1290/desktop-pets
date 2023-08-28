import os
from pathlib import Path
from typing import TypedDict, Any
import customtkinter

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
ASSETS_DIR = os.path.join(Path(__file__).absolute().parent.parent, 'assets')

class AssetT(TypedDict):
	file_path: str
	file_name: str
	file_format: str
	image: customtkinter.CTkImage
	widget: customtkinter.CTkButton