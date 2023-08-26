import customtkinter
import tkinter as tk

from models.main import Model
from views.main import NavPanelsT, View
from views.petcreator.assets import AssetT, Assets
from views.petcreator.main import PetCreator

class PetCreatorController:
	'''
	The Pet Creator panel is dynamically generated so 
	the Pet Creator View is not accessed through
	view.PetCreatorView but rather through an observer
	pattern from view
	'''
	def __init__(self, model: Model, view: View) -> None:
		self.view = view

		self.creator_view: PetCreator|None = None
		# self.wrapper_canvas: tk.Canvas|None = None

		self.remove_creator_panel_events = []

		self.remove_view_events = []
		self.remove_view_events.append(self.view.bind_to('new_creator_panel', self._on_new_creator_panel))
		self.remove_view_events.append(self.view.bind_to('remove_creator_panel', self._on_remove_creator_panel))

	def _on_new_creator_panel(self, const_nav_panels: NavPanelsT):
		self.creator_view = const_nav_panels["creator"]["widget"]

		self.remove_creator_panel_events.append(
			self.creator_view.asset_view.bind_to("new_assets", self._on_new_assets))

	def _on_remove_creator_panel(self, const_nav_panels: NavPanelsT):
		for func in self.remove_creator_panel_events:
			func()

	def _on_new_assets(self, const_assets: list[AssetT]):
		for asset in const_assets:
			asset["widget"].bind("<Button-1>", lambda event, asset=asset: self._on_asset_click(event, asset))

	def _on_asset_click(self, event, const_asset: AssetT):
		x = self.creator_view.winfo_pointerx() - self.creator_view.winfo_rootx()
		y = self.creator_view.winfo_pointery() - self.creator_view.winfo_rooty()
		self.creator_view.create_draggable_asset(const_asset["file_path"], [x, y])

		self.creator_view.bind("<B1-Motion>", self._on_drag_asset)
		self.creator_view.bind("<ButtonRelease-1>", self._on_asset_release)

	def _on_drag_asset(self, event):
		x = self.creator_view.winfo_pointerx() - self.creator_view.winfo_rootx()
		y = self.creator_view.winfo_pointery() - self.creator_view.winfo_rooty()
		self.creator_view.drag_asset([x, y])

	def _on_asset_release(self, event):
		self.creator_view.remove_draggable_asset()