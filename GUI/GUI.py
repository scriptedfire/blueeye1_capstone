from tkinter import *
from tkinter import ttk

def test_fn(*args):
    print("Button pressed.")

def validate_dyear(*args):
    val = dyear_val.get()
    if len(val) > 0:
        lastkey = val[len(val) - 1]
    else:
        return

    if not lastkey.isdigit():
        dyear_input.delete(len(val) - 1, "end")
    elif len(val) > 4:
        dyear_input.delete(4, "end")

def clear_dyear(*args):
    dyear_input.delete(0, "end")

def place_bus(canvas, x_val, y_val, bus_num):
    rect_id = canvas.create_rectangle((x_val, y_val, x_val + 20, y_val + 20), fill="green", tags=('palette', 'palettered'))
    canvas.create_text(x_val + 10, y_val + 10, text='B1', anchor='center', font='TkMenuFont', fill='white')
    return rect_id

root = Tk()
root.title("Space Weather Analysis Tool")

mainframe = ttk.Frame(root, padding="3 3 12 12")

# canvas initialization
h = ttk.Scrollbar(root, orient=HORIZONTAL)
v = ttk.Scrollbar(root, orient=VERTICAL)
canvas = Canvas(root, scrollregion=(0, 0, 800, 800), yscrollcommand=v.set, xscrollcommand=h.set, background="white")
h['command'] = canvas.xview
v['command'] = canvas.yview

# rest of initialization
load_btn = ttk.Button(mainframe, text="Load Grid File", command=test_fn)
play_btn = ttk.Button(mainframe, text="Play/Pause Simulation", command=test_fn)
date_label = ttk.Label(mainframe, text="Solar Storm Date:")
dmonth_val = StringVar()
dmonth_input = ttk.Combobox(mainframe, textvariable=dmonth_val, width=3, state="readonly")
slash1_label = ttk.Label(mainframe, text="/")
dday_val = StringVar()
dday_input = ttk.Combobox(mainframe, textvariable=dday_val, width=3, state="readonly")
slash2_label = ttk.Label(mainframe, text="/")
dyear_val = StringVar()
dyear_input = ttk.Entry(mainframe, textvariable=dyear_val, width=5)
time_in_label = ttk.Label(mainframe, text="Solar Storm Time:")
hour_val = StringVar()
hour_input = ttk.Combobox(mainframe, textvariable=hour_val, width=3, state="readonly")
minute_val = StringVar()
minute_input = ttk.Combobox(mainframe, textvariable=minute_val, width=3, state="readonly")
ampm_val = StringVar()
ampm_input = ttk.Combobox(mainframe, textvariable=ampm_val, width=3, state="readonly")
time_label = ttk.Label(mainframe, text="Time In Simulation: XX:XX:XX")

# date input configuration
dmonth_input.set("01")
dmonth_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1,13))))
dday_input.set("01")
dday_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1,32))))
dyear_input.insert(0,"YYYY")
dyear_input.bind("<FocusIn>", clear_dyear)
dyear_input.bind("<KeyRelease>",validate_dyear)
hour_input.set("01")
hour_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1,13))))
minute_input.set("01")
minute_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1,60))))
ampm_input.set("AM")
ampm_input["values"] = {"AM","PM"}

# widget placement
mainframe.grid(column=0, row=0, sticky=(N,W,E,S))
h.grid(column=0, row=2, columnspan=13, sticky=(W,S,E))
v.grid(column=13,row=1, rowspan=2, sticky=(N,S,E))
canvas.grid(column=0, row=1, columnspan=5, sticky=(N,W,E,S))
load_btn.grid(column=0, row=0, sticky=(N,W))
play_btn.grid(column=1, row=0, sticky=(N,W))
date_label.grid(column=2, row=0, sticky=(W,E), padx=5)
dmonth_input.grid(column=3, row=0, sticky=(W,E))
slash1_label.grid(column=4, row=0, sticky=(W,E))
dday_input.grid(column=5, row=0, sticky=(W,E))
slash2_label.grid(column=6, row=0, sticky=(W,E))
dyear_input.grid(column=7, row=0, sticky=(W,E))
time_in_label.grid(column=8, row=0, sticky=(W,E), padx=5)
hour_input.grid(column=9, row=0, sticky=(W,E))
minute_input.grid(column=10, row=0, sticky=(W,E))
ampm_input.grid(column=11, row=0, sticky=(W,E))
time_label.grid(column=12, row=0, sticky=(W,E), padx=5)

id = canvas.create_rectangle((10, 10, 30, 30), fill="red", tags=('palette', 'palettered'))
#id2 = canvas.create_rectangle((1750, 1750, 1770, 1770), fill="red", tags=('palette', 'palettered'))
id3 = place_bus(canvas, 700, 700, 2)
#canvas.create_text(710, 710, text='B1', anchor='center', font='TkMenuFont', fill='white')

root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

#root.bind("<Return>", test_fn)

root.mainloop()
