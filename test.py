import ctypes
import tkinter as tk
import random
import os

# x = 100
# root = tk.Tk()
# root.geometry('100x100+'+str(x)+'+1050')
# label = tk.Label(root, bd=0, bg='black')
# label.pack()
# root.mainloop()

# x = 1400
# print('100x100+'+str(x)+'+1050')

# import ctypes
# user32 = ctypes.windll.user32
# screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

# print(screensize)

# DEBUG = False
# def print_debug(*args):
#     if DEBUG:
#         print('hi')

# from PIL import Image

# num_key_frames = 8

# with Image.open('pets/demo_cat/sleeping.gif') as im:
#     print("Number of frames: "+str(im.n_frames))

# user32 = ctypes.windll.user32
# user32.SetProcessDPIAware()
# x = user32.GetSystemMetrics(0)
# y = user32.GetSystemMetrics(1)

# print(x, y)
# print(ctypes.windll.user32.GetSystemMetrics(2))

# from win32api import GetMonitorInfo, MonitorFromPoint

# monitor_info = GetMonitorInfo(MonitorFromPoint((0,0)))
# work_area = monitor_info.get("Work")
# print("The work area size is {}x{}.".format(work_area[2], work_area[3]))

# monitor_area = monitor_info.get("Monitor")
# print("The taskbar height is {}.".format(monitor_area[3]-work_area[3]))

# #Create an instance of Tkinter Frame
# win = tk.Tk()

# #Set the geometry of window
# win.geometry("700x350")

# #Add a background color to the Main Window
# win.config(bg = '#add123')

# #Create a transparent window
# win.wm_attributes('-transparentcolor','#add123')
# win.mainloop()

# count = 0
# def add_line():
#     global count
#     count += 1
#     tk.Label(text='Label %d' % count).pack()
# tk.Button(root, text="Hello World", command=add_line).pack()

import tkinter as tk
root = tk.Tk()
root.attributes('-fullscreen',True)
root.config(bg='black')

dir_path = os.path.dirname(os.path.realpath(__file__))
placeholder_img = os.path.join(dir_path, "pets", "placeholder.png")

canvas = tk.Canvas(root, width=1000, height= 1000, bd=0, highlightthickness=0)
canvas.config(bg='black')
canvas.place(x=0, y=0)

root.wm_attributes('-transparentcolor', 'black')

img = tk.PhotoImage(file=placeholder_img)
canvas.create_image(0,0,anchor=tk.NW,image=img)

img2 = tk.PhotoImage(file=placeholder_img)
canvas.create_image(39,30,anchor=tk.NW,image=img2)

root.mainloop()