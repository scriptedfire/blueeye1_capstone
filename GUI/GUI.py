import tkinter as tk
from tkinter import N,S,E,W
from tkinter import ttk
from tkinter import filedialog as fdialog

class App(tk.Tk):
    grid_data = {}

    def __init__(self):
        super().__init__()
        
        self.title("Space Weather Analysis Tool")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.create_body_frame()

    def create_body_frame(self):
        self.body = ttk.Frame(self, padding="3 3 12 12")

        # canvas initialization
        self.h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.grid_canvas = tk.Canvas(self, scrollregion=(0, 0, 800, 800), yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set, background="white")
        self.h_scroll['command'] = self.grid_canvas.xview
        self.v_scroll['command'] = self.grid_canvas.yview

        # buttons
        self.load_btn = ttk.Button(self.body, text="Load Grid File", command=self.load_file)
        self.play_btn = ttk.Button(self.body, text="Play/Pause Simulation", command=self.test_fn)
        self.date_label = ttk.Label(self.body, text="Solar Storm Date:")

        # enter date
        self.dmonth_val = tk.StringVar()
        self.dmonth_input = ttk.Combobox(self.body, textvariable=self.dmonth_val, width=3, state="readonly")
        self.slash1_label = ttk.Label(self.body, text="/")
        self.dday_val = tk.StringVar()
        self.dday_input = ttk.Combobox(self.body, textvariable=self.dday_val, width=3, state="readonly")
        self.slash2_label = ttk.Label(self.body, text="/")
        self.dyear_val = tk.StringVar()
        self.dyear_input = ttk.Entry(self.body, textvariable=self.dyear_val, width=5)

        # enter time
        self.time_in_label = ttk.Label(self.body, text="Solar Storm Time:")
        self.hour_val = tk.StringVar()
        self.hour_input = ttk.Combobox(self.body, textvariable=self.hour_val, width=3, state="readonly")
        self.minute_val = tk.StringVar()
        self.minute_input = ttk.Combobox(self.body, textvariable=self.minute_val, width=3, state="readonly")
        self.ampm_val = tk.StringVar()
        self.ampm_input = ttk.Combobox(self.body, textvariable=self.ampm_val, width=3, state="readonly")

        # simulation time
        self.time_label = ttk.Label(self.body, text="Time In Simulation: XX:XX")

        # date input configuration
        self.dmonth_input.set("01")
        self.dmonth_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1,13))))
        self.dday_input.set("01")
        self.dday_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1,32))))
        self.dyear_input.insert(0,"YYYY")
        self.dyear_input.bind("<FocusIn>", self.clear_dyear)
        self.dyear_input.bind("<KeyRelease>", self.validate_dyear)

        # time input configuration
        self.hour_input.set("01")
        self.hour_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1,13))))
        self.minute_input.set("01")
        self.minute_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1,60))))
        self.ampm_input.set("AM")
        self.ampm_input["values"] = ["AM", "PM"]

        # widget placement
        self.body.grid(column=0, row=0, sticky=(N,W,E,S))

        self.h_scroll.grid(column=0, row=2, columnspan=13, sticky=(W,S,E))
        self.v_scroll.grid(column=13,row=1, rowspan=2, sticky=(N,S,E))
        self.grid_canvas.grid(column=0, row=1, columnspan=5, sticky=(N,W,E,S))

        self.load_btn.grid(column=0, row=0, sticky=(N,W))
        self.play_btn.grid(column=1, row=0, sticky=(N,W))
        
        self.date_label.grid(column=2, row=0, sticky=(W,E), padx=5)
        self.dmonth_input.grid(column=3, row=0, sticky=(W,E))
        self.slash1_label.grid(column=4, row=0, sticky=(W,E))
        self.dday_input.grid(column=5, row=0, sticky=(W,E))
        self.slash2_label.grid(column=6, row=0, sticky=(W,E))
        self.dyear_input.grid(column=7, row=0, sticky=(W,E))

        self.time_in_label.grid(column=8, row=0, sticky=(W,E), padx=5)
        self.hour_input.grid(column=9, row=0, sticky=(W,E))
        self.minute_input.grid(column=10, row=0, sticky=(W,E))
        self.ampm_input.grid(column=11, row=0, sticky=(W,E))
        self.time_label.grid(column=12, row=0, sticky=(W,E), padx=5)

        # test code
        self.place_bus(10, 10, 1)
        self.place_bus(400, 400, 2)
        self.place_bus(500, 10, 3)
        self.place_bus(700, 700, 4)

        self.place_wire(10, 10, 500, 10)
        self.place_wire(10, 10, 400, 400)
        self.place_wire(500, 10, 400, 400)
        self.place_wire(500, 10, 700, 700)
        self.place_wire(400, 400, 700, 700)

    def load_file_process_sections(self, section):
        return list(map(lambda line : line.split(','), section.split('\n')))

    def load_file(self, *args):
        filetypes = (("RAW files", "*.RAW"),)

        # open file
        with fdialog.askopenfile(filetypes=filetypes) as grid_file:
            # split file data into sections, sections into lines, and lines into values
            fdata = list(map(self.load_file_process_sections, grid_file.read().split("/")))

            # carve relevant sections from data
            busdata = fdata[1][3:-1]
            branchdata = fdata[5][1:-1]
            transformerdata = fdata[6][1:-1]

    def test_fn(self, *args):
        print("Button pressed.")

    def validate_dyear(self, *args):
        val = self.dyear_val.get()
        if len(val) > 0:
            lastkey = val[len(val) - 1]
        else:
            return

        if not lastkey.isdigit():
            self.dyear_input.delete(len(val) - 1, "end")
        elif len(val) > 4:
            self.dyear_input.delete(4, "end")

    def clear_dyear(self, *args):
        self.dyear_input.delete(0, "end")

    def place_bus(self, x_val, y_val, bus_num):
        rect_id = self.grid_canvas.create_rectangle((x_val, y_val, x_val + 20, y_val + 20), fill="green", tags=('palette', 'palettered'))
        self.grid_canvas.create_text(x_val + 10, y_val + 10, text='B' + str(bus_num), anchor='center', font='TkMenuFont', fill='white')
        return rect_id

    def place_wire(self, from_x_val, from_y_val, to_x_val, to_y_val):
        # connect bus squares at corners
        if from_x_val < to_x_val and from_y_val < to_y_val:
            return self.grid_canvas.create_line(from_x_val + 20, from_y_val + 20, to_x_val, to_y_val, fill="red", width=2)
        elif from_x_val > to_x_val and from_y_val > to_y_val:
            return self.grid_canvas.create_line(from_x_val, from_y_val, to_x_val + 20, to_y_val + 20, fill="red", width=2)
        elif from_x_val < to_x_val and from_y_val > from_x_val:
            return self.grid_canvas.create_line(from_x_val + 20, from_y_val, to_x_val, to_y_val + 20, fill="red", width=2)
        elif from_x_val > to_x_val and from_y_val < from_x_val:
            return self.grid_canvas.create_line(from_x_val, from_y_val + 20, to_x_val + 20, to_y_val, fill="red", width=2)
        # connect bus squares at sides if on the same axis
        elif from_x_val == to_x_val and from_y_val < from_x_val:
            return self.grid_canvas.create_line(from_x_val + 10, from_y_val + 20, to_x_val + 10, to_y_val, fill="red", width=2)
        elif from_x_val == to_x_val and from_y_val > from_x_val:
            return self.grid_canvas.create_line(from_x_val + 10, from_y_val, to_x_val + 10, to_y_val + 20, fill="red", width=2)
        elif from_x_val < to_x_val and from_y_val == from_x_val:
            return self.grid_canvas.create_line(from_x_val + 20, from_y_val + 10, to_x_val, to_y_val + 10, fill="red", width=2)
        elif from_x_val > to_x_val and from_y_val == from_x_val:
            return self.grid_canvas.create_line(from_x_val, from_y_val + 10, to_x_val + 20, to_y_val + 10, fill="red", width=2)

if __name__ == "__main__":
    app = App()
    app.mainloop()
