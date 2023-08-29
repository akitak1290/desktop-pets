import os
import customtkinter
import tkinter as tk
from PIL import Image, ImageTk

from utils import ASSETS_DIR, AssetT

class EditCanvas(customtkinter.CTkFrame):
	def __init__(self, master, **kwargs):
		super().__init__(master, **kwargs)
		
		FULL_WIDTH = 1000
		FULL_HEIGHT = 1000

		self.canvas = customtkinter.CTkCanvas(self)
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)
		self.canvas.grid(column=0, row=0, padx=12, pady=12, sticky="news")

		# data
		self.data = {}

		# set background
		bg_img_path = os.path.join(ASSETS_DIR, "images", "grid.png")
		img = Image.open(bg_img_path)
		img = img.resize((FULL_WIDTH, FULL_HEIGHT))
		self.canvas_bg = ImageTk.PhotoImage(img)
		self.canvas.create_image( 0, 0, image = self.canvas_bg, anchor = "nw")

		# add scrollable
		self.hscrollbar = tk.Scrollbar(
			self, orient="horizontal", command=self.canvas.xview)
		self.vscrollbar = tk.Scrollbar(
			self, orient="vertical", command=self.canvas.yview)
		self.canvas.configure(
			yscrollcommand=self.vscrollbar.set, xscrollcommand=self.hscrollbar.set)
		self.canvas.configure(scrollregion=(0, 0, FULL_WIDTH, FULL_HEIGHT))

		# ! Show v-scrollbar and h-scrollbar
		# self.hscrollbar.grid(row=1, column=0, sticky="we")
		# self.vscrollbar.grid(row=0, column=1, sticky="ns")

		self.c_scroll_begin_cb = self.canvas.bind("<ButtonPress-1>", self._c_scroll_begin)
		self.c_scroll_move_cb = self.canvas.bind("<B1-Motion>", self._c_scroll_move)
		# self.c_hover_cb = self.canvas.bind("<Motion>", self._c_hover)
		# self.c_leave_cb = self.canvas.bind("<Leave>", self.leave_canvas)

	def _c_scroll_begin(self, event):
		self.canvas.scan_mark(event.x, event.y)

	def _c_scroll_move(self, event) -> None:
		# if self.canvas_state == CanvasState.SCROLLABLE:
		self.canvas.scan_dragto(event.x, event.y, gain=1)

	# def refac(self) -> None:

	# 	self._c_reset()

	# 	file_list = filedialog.askopenfilenames(
	# 		filetypes=[("Gif files", "*.gif")])

	# 	if not file_list:
	# 		return

	# 	self.object_id = [-1]*(len(file_list))
	# 	self.action_files_names_list = []

	# 	for idx, file in enumerate(file_list):
	# 		# setup canvas's items
	# 		x = random.randint(0, 400)
	# 		y = random.randint(0, 400)
	# 		file_name = ntpath.basename(os.path.splitext(file)[0])

	# 		self.action_files_names_list.append(file_name)
	# 		# img = (Image.open(file))
	# 		# resized_img = img.resize((100, 100), Image)
	# 		self.object_id[idx] = tk.PhotoImage(file=file)
	# 		img_id = self.canvas.create_image(
	# 			x, y, anchor="nw", image=self.object_id[idx])
	# 		text_id = self.canvas.create_text(x, y+100, anchor="nw",
	# 											text=file_name)
	# 		add_id = self.canvas.create_image(
	# 			x+100, y+50, anchor="nw", image=self.add_icon_pht_obj)
	# 		self.canvas.itemconfigure(add_id, state='hidden')

	# 		self.canvas_item_dict[img_id] = {
	# 			"text_id": text_id,
	# 			"add_id": add_id,
	# 			"lines_ids_list": []
	# 		}

	# 		# setup config per img item
	# 		self.config_dict[img_id] = {
	# 			"file_name": file_name,
	# 			"m_speed_x": 0,
	# 			"m_speed_y": 0,
	# 			"p_speed": 100,
	# 			"can_repeat": 0,
	# 			"chance": self.chance_options[0],
	# 			"format": os.path.splitext(file)[1],
	# 			"abs_path": file
	# 		}

	# 		# canvas's items' event listeners
	# 		self.canvas.tag_bind(img_id, '<Button-1>', lambda event,
	# 								img_id=img_id: self.click_action_item(event, img_id=img_id))
	# 		self.canvas.tag_bind(img_id, '<ButtonRelease-1>', self.release_img)
	# 		self.canvas.tag_bind(img_id, '<Motion>', lambda event,
	# 								add_id=add_id: self.hover(event, add_id=add_id))
	# 		self.canvas.tag_bind(img_id, '<Leave>', lambda event,
	# 								add_id=add_id: self.leave(event, add_id=add_id))
	# 		self.canvas.tag_bind(
	# 			img_id, '<B1-Motion>',
	# 			lambda event, img_id=img_id, text_id=text_id, add_id=add_id: self.drag(event, img_id=img_id, text_id=text_id, add_id=add_id))

	# 		self.canvas.tag_bind(add_id, '<Motion>', lambda event,
	# 								add_id=add_id: self.hover(event, add_id=add_id))
	# 		self.canvas.tag_bind(add_id, '<Leave>', lambda event,
	# 								add_id=add_id: self.leave(event, add_id=add_id))
	# 		self.canvas.tag_bind(
	# 			add_id, '<Button-1>',
	# 			lambda event, img_id=img_id: self.create_connection(event, img_id=img_id))

	# 	# update dropdown menu
	# 	falling_menu = self.falling_action_entry["menu"]
	# 	dragging_menu = self.dragging_action_entry["menu"]
	# 	falling_menu.delete(0, "end")
	# 	dragging_menu.delete(0, "end")
	# 	for name in self.action_files_names_list:
	# 		falling_menu.add_command(label=name,
	# 									command=lambda value=name: self.falling_action_name.set(value))
	# 		dragging_menu.add_command(label=name,
	# 									command=lambda value=name: self.dragging_action_name.set(value))

	def c_add_asset(self, file_path, pos: list[int]):
		# create new photoimage
		img = Image.open(file_path)
		img = img.resize((100, 100))
		img = ImageTk.PhotoImage(img)
		img_id = self.canvas.create_image(self.canvas.canvasx(pos[0])-50,
				    					  self.canvas.canvasy(pos[1])-50,
										  anchor="nw", image=img)
		self.data[img_id] = img

	# def _c_reset(self):
	# 	items_ids = []
	# 	for key in self.canvas_item_dict.keys():
	# 		items_ids.append(key)
	# 		items_ids.append(self.canvas_item_dict[key]["text_id"])
	# 		items_ids.append(self.canvas_item_dict[key]["add_id"])
	# 		items_ids += self.canvas_item_dict[key]["lines_ids_list"]

	# 	for item_id in items_ids:
	# 		self.canvas.delete(item_id)

	# 	self.canvas_item_dict = OrderedDict()
	# 	self.connection_dict = {}

	# 	self.object_id = None