import tkinter as tk
from tkinter import N,S,E,W
from tkinter import ttk
from tkinter import filedialog as fdialog

class App(tk.Tk):
    # constant: display size of substation squares
    sq_size = 4

    # constant: canvas size for scaling lat/long
    grid_canvas_size = 1800

    # state from file: values for lat/long to canvas x/y conversion
    max_lat = 0
    max_long = 0
    min_lat = 0
    min_long = 0

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
        self.grid_canvas = tk.Canvas(self, scrollregion=(0, 0, self.grid_canvas_size, self.grid_canvas_size), yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set, background="white")
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

    def load_file_process_sections(self, section):
        "Helper to make file data splitting process more readable"
        return list(map(lambda line : line.split('"'), section.split('\n')))

    def load_file(self, *args):
        "Loads grid file in RAW format chosen by the user into state"
        # FIXME: clear canvas/state
        filetypes = (("AUX files", "*.AUX"),)

        # open file
        with fdialog.askopenfile(filetypes=filetypes) as grid_file:
            # split file data into sections, sections into lines, and lines into values
            fdata = list(map(self.load_file_process_sections, grid_file.read().split("\n\n")))

            substationdata = fdata[27][3:-1]

            located_substationsx = []
            located_substationsy = []
            located_ids = []
            for item in substationdata:
                coords = item[4].split(' ')
                if len(coords) == 2:
                    continue
                xcoord = float(coords[2])
                ycoord = float(coords[1])
                located_substationsx.append(xcoord)
                located_substationsy.append(ycoord)
                located_ids.append(int(item[0]))

            self.min_long = min(located_substationsx)
            self.min_lat = min(located_substationsy)
            self.max_long = max(located_substationsx)
            self.max_lat = max(located_substationsy)

            self.generate_axial_labels()

            print(located_substationsx)
            print(located_substationsy)

            for i in range(len(located_substationsx)):
                self.place_sub(located_substationsx[i], located_substationsy[i], located_ids[i])

            # TODO: load data into state

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

    # using https://stackoverflow.com/a/2450158
    # modified to work better for canvas purposes
    def long_to_x(self, long):
        # center in coordinate space
        long -= (self.max_long + self.min_long) / 2

        # scale to ~(-0.49, 0.49)
        # slightly shrunken so ends aren't placed on edge of canvas
        long /= max(self.max_long - self.min_long, self.max_lat - self.min_lat) * 1.02

        # translate to (0.01, 0.99)
        long += 0.5

        # scale to desired canvas size
        long *= self.grid_canvas_size

        return int(long)
    
    # using https://stackoverflow.com/a/2450158
    # modified to work better for canvas purposes
    def lat_to_y(self, lat):
        # center in coordinate space
        lat -= (self.max_lat + self.min_lat) / 2

        # scale to ~(-0.49, 0.49)
        # slightly shrunken so ends aren't placed on edge of canvas
        lat /= max(self.max_long - self.min_long, self.max_lat - self.min_lat) * 1.02

        # invert y axis to adjust for canvas origin location
        # being in top left rather than bottom left
        lat *= -1

        # translate to (0.01, 0.99)
        lat += 0.5

        # scale to desired canvas size
        lat *= self.grid_canvas_size

        return int(lat)

    def place_sub(self, long, lat, bus_num):
        # convert lat/long to x/y
        x_val = self.long_to_x(long)
        y_val = self.lat_to_y(lat)

        # place sub rectangle
        rect_id = self.grid_canvas.create_rectangle((x_val, y_val, x_val + self.sq_size, y_val + self.sq_size), fill="#00ff40", tags=('palette', 'palettered'))
        
        # place sub text
        self.grid_canvas.create_text(x_val + (self.sq_size / 2), y_val + (self.sq_size * 3), text='S' + str(bus_num), anchor='center', font='TkMenuFont', fill='black')

        return rect_id

    def place_wire(self, from_long, from_lat, to_long, to_lat):
        # convert lat/long to x/y
        from_x_val = self.long_to_x(from_long)
        from_y_val = self.lat_to_y(from_lat)
        to_x_val = self.long_to_x(to_long)
        to_y_val = self.lat_to_y(to_lat)

        # connect bus squares at corners
        if from_x_val < to_x_val and from_y_val < to_y_val:
            return self.grid_canvas.create_line(from_x_val + self.sq_size, from_y_val + self.sq_size, to_x_val, to_y_val, fill="red", width=2)
        elif from_x_val > to_x_val and from_y_val > to_y_val:
            return self.grid_canvas.create_line(from_x_val, from_y_val, to_x_val + self.sq_size, to_y_val + self.sq_size, fill="red", width=2)
        elif from_x_val < to_x_val and from_y_val > from_x_val:
            return self.grid_canvas.create_line(from_x_val + self.sq_size, from_y_val, to_x_val, to_y_val + self.sq_size, fill="red", width=2)
        elif from_x_val > to_x_val and from_y_val < from_x_val:
            return self.grid_canvas.create_line(from_x_val, from_y_val + self.sq_size, to_x_val + self.sq_size, to_y_val, fill="red", width=2)
        
        # connect bus squares at sides if on the same axis
        elif from_x_val == to_x_val and from_y_val < from_x_val:
            return self.grid_canvas.create_line(from_x_val + (self.sq_size / 2), from_y_val + self.sq_size, to_x_val + (self.sq_size / 2), to_y_val, fill="red", width=2)
        elif from_x_val == to_x_val and from_y_val > from_x_val:
            return self.grid_canvas.create_line(from_x_val + (self.sq_size / 2), from_y_val, to_x_val + (self.sq_size / 2), to_y_val + self.sq_size, fill="red", width=2)
        elif from_x_val < to_x_val and from_y_val == from_x_val:
            return self.grid_canvas.create_line(from_x_val + self.sq_size, from_y_val + (self.sq_size / 2), to_x_val, to_y_val + (self.sq_size / 2), fill="red", width=2)
        elif from_x_val > to_x_val and from_y_val == from_x_val:
            return self.grid_canvas.create_line(from_x_val, from_y_val + (self.sq_size / 2), to_x_val + self.sq_size, to_y_val + (self.sq_size / 2), fill="red", width=2)
        
    def generate_axial_labels(self):
        # find how many long degrees in display area
        x_label_count = int(self.max_long - self.min_long)

        # add long degree labels
        for i in range(0, x_label_count + 1):
            x_coord = self.long_to_x(i + self.min_long)
            y_coord = self.lat_to_y(self.max_lat)
            self.grid_canvas.create_text(x_coord, y_coord, text=str(int(i + self.min_long)) + 'E', anchor='center', font='TkMenuFont', fill='blue')

        # find how many lat degrees in display area
        y_label_count = int(self.max_lat - self.min_lat)

        # add lat degree labels
        for i in range(0, y_label_count + 1):
            x_coord = self.long_to_x(self.min_long)
            y_coord = self.lat_to_y(i + self.min_lat)
            self.grid_canvas.create_text(x_coord, y_coord, text=str(int(i + self.min_lat)) + 'N', anchor='center', font='TkMenuFont', fill='blue')

if __name__ == "__main__":
    app = App()
    app.mainloop()
