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

		self._creator_view: PetCreator|None = None

		# event stuff to unbind/cleanup
		self.remove_creator_panel_events_func = []
		self.remove_view_events_func = []
		self.remove_draggable_asset_events = []

		self.remove_view_events_func.append(self.view.bind_to('new_creator_panel', self._on_new_creator_panel))
		self.remove_view_events_func.append(self.view.bind_to('remove_creator_panel', self._on_remove_creator_panel))

	def _on_new_creator_panel(self, const_nav_panels: NavPanelsT):
		self._creator_view = const_nav_panels["creator"]["widget"]

		self.remove_creator_panel_events_func.append(
			self._creator_view.asset_view.bind_to("new_assets", self._on_new_assets))
		self.remove_creator_panel_events_func.append(
			self._creator_view.asset_view.bind_to("clear_assets", self._on_clear_assets))
		
	def _on_remove_creator_panel(self, const_nav_panels: NavPanelsT):
		for func in self.remove_creator_panel_events_func:
			func()
		self.remove_creator_panel_events_func = []

	def _on_new_assets(self, const_assets: list[AssetT]):
		for asset in const_assets:
			'''
			TODO: customtkinter might have a memory leak as this
			function doesn't return anything. Swap to tk button
			and properly handle this event!
			'''
			asset["widget"].bind("<Button-1>", lambda event, asset=asset: self._on_asset_click(event, asset))

	def _on_clear_assets(self, const_assets: list[AssetT]):
		self._creator_view.remove_draggable_asset()

	def _on_asset_click(self, event, const_asset: AssetT):
		x = self._creator_view.winfo_pointerx() - self._creator_view.winfo_rootx()
		y = self._creator_view.winfo_pointery() - self._creator_view.winfo_rooty()
		file_path = self._creator_view.create_draggable_asset(const_asset, [x, y])

		# ! a proper dict instead of tuple list is more consistent with the rest
		# ! buuuuuut this it easier to manage type wise.... properly won't be a future problem!
		self.remove_draggable_asset_events.append(("<B1-Motion>", self._creator_view.bind("<B1-Motion>", self._on_drag_asset)))
		self.remove_draggable_asset_events.append(("<ButtonRelease-1>",
												   self._creator_view.bind("<ButtonRelease-1>", lambda event, file_path=file_path: self._on_asset_release(event, file_path))))

	def _on_drag_asset(self, event):
		x = self._creator_view.winfo_pointerx() - self._creator_view.winfo_rootx()
		y = self._creator_view.winfo_pointery() - self._creator_view.winfo_rooty()
		self._creator_view.drag_asset([x, y])

	def _on_asset_release(self, event, file_path: str):
		for tuple in self.remove_draggable_asset_events:
			self._creator_view.unbind(tuple[0], tuple[1])
		self.remove_draggable_asset_events = []

		# remove the draggable widget to get the one underneath
		self._creator_view.remove_draggable_asset_widget()

		x,y = event.widget.winfo_pointerxy()
		widget = event.widget.winfo_containing(x, y)
		# if asset is released on top of the editcanvas
		if str(widget) == str(self._creator_view.edit_canvas.canvas):
			self._creator_view.edit_canvas.c_add_asset(file_path, [x-widget.winfo_rootx(), y-widget.winfo_rooty()])

	# call to release all resources when destroying this object
	# meant to be called as destructor
	def release(self):
		for func in self.remove_view_events_func:
			func()
		self.remove_view_events_func = []