# ! redundant class
class MainCanvasController:
	def __init__(self, model, view) -> None:
		self.model = model
		self.view = view

		self.canvas = self.view.main_canvas
		self._bind()