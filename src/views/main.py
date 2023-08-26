from win32api import GetMonitorInfo, MonitorFromPoint
import os
import customtkinter
from PIL import Image
from pathlib import Path
from functools import partial
from typing import Any, TypedDict

from views.root import Root
from views.maincanvas import MainCanvas
from views.petcreator.main import PetCreator

class CreatorPanelT(TypedDict):
	widget: None|PetCreator
	constructor: type[PetCreator]

class NavPanelsT(TypedDict):
	creator: CreatorPanelT

class View():
	def __init__(self) -> None:
		self._observers = {}

		# metadata
		monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0))) # current working monitor
		work_area = monitor_info.get("Work")
		# self.monitor_width = work_area[2]
		# self.monitor_height = work_area[3]
		self.monitor_width = 300
		self.monitor_height = 450

		# a transparent overlay, always on the top most level
		self.root = Root(tittle="+ᓚᘏᗢ", monitor_height=self.monitor_height, monitor_width=self.monitor_width)
		
		self.main_canvas = MainCanvas(master=self.root, height=self.monitor_height, width=self.monitor_width)
		self.main_canvas.place(x=0, y=0)
		
		# nav
		assets_path = os.path.join(os.path.dirname(Path(__file__).absolute().parent.parent), "assets")
		gear_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(assets_path, "images", "gear.png")),
                                            dark_image=Image.open(os.path.join(assets_path, "images", "gear.png")), size=(24, 24))
		self.nav_panels: NavPanelsT = {
			"creator": {
				"widget": None,
				"constructor": PetCreator
			}
		}
		self.creator_panel_button = customtkinter.CTkButton(self.main_canvas, text="", fg_color="transparent",
					     						   			hover_color=("gray70", "gray30"), image=gear_image, width=24)
		self.creator_panel_button.configure(command=partial(self._toggle_panel, "creator"))
		self.creator_panel_button.place(anchor="nw", x=10, y=10)

		self.main_canvas.grid(row=0, column=0)

	def trigger_event(self, event):
		if event not in self._observers.keys():
			return
		
		for func in self._observers[event]:
			func(self.nav_panels)

	def bind_to(self, event, func):
		try:
			self._observers[event].append(func)
		except KeyError:
			self._observers[event] = [func]

		return lambda: self._observers[event].remove(func)

	def _toggle_panel(self, name):
		if not self.nav_panels[name]["widget"]:
			self.nav_panels[name]["widget"] = self.nav_panels[name]["constructor"](self.root)
			self.nav_panels[name]["widget"].protocol("WM_DELETE_WINDOW",
													 partial(self._close_panel, name))
			self.trigger_event('new_creator_panel')
		else:
			self._close_panel(name)

	def _close_panel(self, name):
		if self.nav_panels[name]["widget"]:
			self.trigger_event('remove_creator_panel')
			self.nav_panels[name]["widget"].destroy()
			self.nav_panels[name]["widget"] = None
	
	def start_mainloop(self) -> None:
		self.root.mainloop()