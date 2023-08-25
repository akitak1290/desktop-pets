import customtkinter

class Root(customtkinter.CTk):
	def __init__(self, tittle, monitor_width, monitor_height, **kwargs):
		super().__init__( **kwargs)
            
		# additional metadata
		transparent_color = '#00ffff'

		# configure window
		self.title(tittle)
		# self.config(highlightbackground=transparent_color)
		# self.config(bg=transparent_color)
		# self.wm_attributes('-transparentcolor', transparent_color)
		# self.overrideredirect(True)
		# self.call("wm", "attributes", ".", "-topmost", "true")
		self.geometry(f"{monitor_width}x{monitor_height}+0+0")