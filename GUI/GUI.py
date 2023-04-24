import tkinter as tk
from tkinter import N,S,E,W
from tkinter import ttk
from tkinter import filedialog as fdialog
from math import sin, cos, radians

class App(tk.Tk):
    # constant: display size of substation squares
    sq_size = 4

    # state from user input: canvas size for scaling lat/long
    grid_canvas_size = 10000

    # constant: toss distance percent for approximating sub locations that don't have coords
    toss_percent = 0.02

    # state from file: values for lat/long to canvas x/y conversion
    max_lat = 0
    max_long = 0
    min_lat = 0
    min_long = 0

    # state from file: grid data
    substation_data = {}
    bus_data = {}
    branch_data = []

    # FIXME: view state
    # FIXME: sub_boxes

    # state from grid (re)drawing: keys are tuples of (x, y)
    # vals are ids of substations touching that pixel
    # load_file also uses this temporarily but then calls redraw_grid which restores it
    substation_pixels = {}

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

        # enter zoom
        self.zoom_label = tk.Label(self.body, text="Zoom: ")
        self.zoom_val = tk.StringVar()
        self.zoom_input = ttk.Combobox(self.body, textvariable=self.zoom_val, width=5, state="readonly")

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

        # zoom configuration
        self.zoom_input.set("10%")
        self.zoom_input["values"] = list(map(lambda val : str(val * 10) + '%', list(range(1, 21))))
        self.zoom_input.bind('<<ComboboxSelected>>', self.execute_zoom)

        # widget placement
        self.body.grid(column=0, row=0, sticky=(N,W,E,S))

        self.h_scroll.grid(column=0, row=2, columnspan=15, sticky=(W,S,E))
        self.v_scroll.grid(column=15,row=1, rowspan=2, sticky=(N,S,E))
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

        self.zoom_label.grid(column=13, row=0, sticky=(W,E))
        self.zoom_input.grid(column=14, row=0, sticky=(W,E))

    ###########################
    # State Loading Functions #
    ###########################

    def load_file_process_sections(self, section):
        "Helper to make file data splitting process more readable"
        return list(map(lambda line : (' '.join(line.split())).split('"'), section.split('\n')))
    
    # FIXME: write locate substation helper function to organize loading process better

    def load_file(self, *args):
        "Loads grid file in RAW format chosen by the user into state"
        # FIXME: clear cached state
        filetypes = (("AUX files", "*.AUX"),)

        # open file
        with fdialog.askopenfile(filetypes=filetypes) as grid_file:
            # split file data into sections, sections into lines, and lines into values
            fdata = list(map(self.load_file_process_sections, grid_file.read().split("\n\n")))

            # get substation data
            substation_fdata = fdata[27][3:-1]

            # extract relevant data and load into state
            located_substations_lat = []
            located_substations_long = []
            next_angle = 15
            for item in substation_fdata:
                id = int(item[0])
                coords = item[4].split(' ')

                # substation w/o coordinates
                if len(coords) == 2:
                    self.substation_data[id] = {"lat": None, "long": None, "next_angle": next_angle}
                    next_angle += 15
                    next_angle %= 360
                    continue

                # get coordinates
                lat = float(coords[1])
                long = float(coords[2])
                located_substations_lat.append(lat)
                located_substations_long.append(long)

                # give substations different angles for connecting substations w/o coordinates
                self.substation_data[id] = {"lat": lat, "long": long, "next_angle": next_angle}
                next_angle += 15
                next_angle %= 360

            # load limits into state
            self.min_long = min(located_substations_long)
            self.min_lat = min(located_substations_lat)
            self.max_long = max(located_substations_long)
            self.max_lat = max(located_substations_lat)

            # get bus data
            bus_fdata = fdata[19][11:-1]

            # load buses into state
            for item in bus_fdata:
                id = int(item[0])
                sub_num = int((item[2].split())[8])
                self.bus_data[id] = {"sub_num" : sub_num}

            # get branch data
            branch_fdata = fdata[23][12:-1]

            # load branches into state
            for item in branch_fdata:
                ids = item[0].split()
                self.branch_data.append([int(ids[0]), int(ids[1])])

            # get branches between substations
            branches_btwn_subs = self.get_branches_btwn_subs()

            # loop through branches until all substations have locations
            shift_count = 0
            ultrashift_count = 0
            while(len(branches_btwn_subs) != 0):
                still_unlocated = []
                for i in range(len(branches_btwn_subs)):
                    # get data from state
                    ids = branches_btwn_subs[i]
                    from_sub = self.substation_data[ids[0]]
                    to_sub = self.substation_data[ids[1]]

                    # get coords
                    from_sub_lat = from_sub["lat"]
                    from_sub_long = from_sub["long"]
                    to_sub_lat = to_sub["lat"]
                    to_sub_long = to_sub["long"]

                    # completely ignore branches where both subs have coords
                    # FIXME: add both subs to pixel structure to mitigate overlaps?
                    if(from_sub_lat != None and to_sub_lat):
                        self.check_and_update_substation_pixels(ids[0], self.long_to_x(from_sub_long), self.lat_to_y(from_sub_lat))
                        self.check_and_update_substation_pixels(ids[1], self.long_to_x(to_sub_long), self.lat_to_y(to_sub_lat))
                        continue

                    # if both subs have no coords, skip for now
                    if(from_sub_lat == None and to_sub_lat == None):
                        still_unlocated.append(ids)
                        continue

                    # remaining branches must have one sub with coords and one without
                    # calculate initial vector for tossing sub
                    toss_angle = from_sub["next_angle"]
                    toss_magnitude = (self.max_long - self.min_long) * self.toss_percent

                    # toss sub from one end or the other
                    if(from_sub_lat != None and to_sub_lat == None):
                        toss_angle = from_sub["next_angle"]
                        # recursively look for an unoccupied space to locate the sub (at 100% zoom)
                        iterations = 0
                        while(True):
                            # toss sub
                            to_sub_lat = from_sub_lat + toss_magnitude * sin(radians(toss_angle))
                            to_sub_long = from_sub_long + toss_magnitude * cos(radians(toss_angle))

                            # get location at 100% zoom
                            to_x = self.long_to_x(to_sub_long)
                            to_y = self.lat_to_y(to_sub_lat)

                            # check for overlap
                            pixel_overlap = self.check_and_update_substation_pixels(ids[1], to_x, to_y)

                            # if no overlap, locate substation there, otherwise change to a different vector and recurse
                            if(pixel_overlap == 0):
                                # update sub data
                                to_sub["lat"] = to_sub_lat
                                to_sub["long"] = to_sub_long
                                from_sub["next_angle"] = toss_angle + 45
                                self.substation_pixels[(to_x, to_y)] = [ids[1]]
                                break
                            else:
                                shift_count += 1
                                toss_angle += 15
                                iterations += 1
                                if(iterations > 24):
                                    toss_magnitude = (self.max_long - self.min_long) * (self.toss_percent + 0.01)
                                    print("shifted")
                                    iterations = 0
                                    ultrashift_count += 1

                    elif(from_sub_lat == None and to_sub_lat != None):
                        # recursively look for an unoccupied space to locate the sub (at 100% zoom)
                        toss_angle = to_sub["next_angle"]
                        iterations = 0
                        while(True):
                            # toss sub
                            from_sub_lat = to_sub_lat + toss_magnitude * sin(radians(toss_angle))
                            from_sub_long = to_sub_long + toss_magnitude * cos(radians(toss_angle))

                            # get location at 100% zoom
                            from_x = self.long_to_x(from_sub_long)
                            from_y = self.lat_to_y(from_sub_lat)

                            # check for overlap
                            pixel_overlap = self.check_and_update_substation_pixels(ids[1], from_x, from_y)

                            # if no overlap, locate substation there, otherwise change to a different vector and recurse
                            if(pixel_overlap == 0):
                                # update sub data
                                from_sub["lat"] = from_sub_lat
                                from_sub["long"] = from_sub_long
                                to_sub["next_angle"] = toss_angle + 45
                                self.substation_pixels[(from_x, from_y)] = [ids[0]]
                                break
                            else:
                                shift_count += 1
                                toss_angle += 15
                                iterations += 1
                                if(iterations > 24):
                                    toss_magnitude = (self.max_long - self.min_long) * (self.toss_percent + 0.01)
                                    print("shifted")
                                    iterations = 0
                                    ultrashift_count += 1
                        # toss sub
                        #from_sub_lat = to_sub_lat + toss_magnitude * sin(radians(toss_angle))
                        #from_sub_long = to_sub_long + toss_magnitude * cos(radians(toss_angle))

                        # update sub data
                        #from_sub["lat"] = from_sub_lat
                        #from_sub["long"] = from_sub_long
                        #from_sub["next_angle"] = toss_angle + 45

                # recurse
                branches_btwn_subs = still_unlocated

            print("Shift count:",shift_count)
            print("Ultrashift count:",ultrashift_count)

            # check if a substation failed to be located
            lost_count = 0
            for item in self.substation_data:
                if(self.substation_data[item]["lat"] == None):
                    lost_count += 1

            print("Lost count:", lost_count)

            # FIXME: load data into state

            self.redraw_grid()

    #########################
    # Other Input Functions #
    #########################

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

    def execute_zoom(self, *args):
        # update grid_canvas_size
        self.grid_canvas_size = int(self.zoom_val.get()[:-1]) * 0.01 * 10000

        # FIXME: check if in view that can be zoomed
        self.redraw_grid()

    ##########################
    # Grid Drawing Functions #
    ##########################

    # using https://stackoverflow.com/a/2450158
    # modified to work better for canvas purposes
    def long_to_x(self, long):
        # center in coordinate space
        long -= (self.max_long + self.min_long) / 2

        # scale to ~(-0.48, 0.48)
        # slightly shrunken so ends aren't placed on edge of canvas
        long /= max(self.max_long - self.min_long, self.max_lat - self.min_lat) * 1.05

        # translate to (0.02, 0.98)
        long += 0.5

        # scale to desired canvas size
        long *= self.grid_canvas_size

        return int(long)
    
    # using https://stackoverflow.com/a/2450158
    # modified to work better for canvas purposes
    def lat_to_y(self, lat):
        # center in coordinate space
        lat -= (self.max_lat + self.min_lat) / 2

        # scale to ~(-0.48, 0.48)
        # slightly shrunken so ends aren't placed on edge of canvas
        lat /= max(self.max_long - self.min_long, self.max_lat - self.min_lat) * 1.05

        # invert y axis to adjust for canvas origin location
        # being in top left rather than bottom left
        lat *= -1

        # translate to (0.02, 0.98)
        lat += 0.5

        # scale to desired canvas size
        lat *= self.grid_canvas_size

        return int(lat)

    def place_sub(self, long, lat, sub_num):
        # convert lat/long to x/y
        x_val = self.long_to_x(long)
        y_val = self.lat_to_y(lat)

        # add pixels to grid mapping
        self.check_and_update_substation_pixels(sub_num, x_val, y_val, append_overlaps=True)

        # place sub rectangle
        rect_id = self.grid_canvas.create_rectangle((x_val, y_val, x_val + self.sq_size, y_val + self.sq_size), fill="#00ff40", tags=('palette', 'palettered'))
        
        # place sub text
        self.grid_canvas.create_text(x_val + (self.sq_size / 2), y_val + (self.sq_size * 3), text='S' + str(sub_num), anchor='center', font=("Helvetica", 8), fill='black')

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
        elif from_x_val < to_x_val and from_y_val > to_y_val:
            return self.grid_canvas.create_line(from_x_val + self.sq_size, from_y_val, to_x_val, to_y_val + self.sq_size, fill="red", width=2)
        elif from_x_val > to_x_val and from_y_val < to_y_val:
            return self.grid_canvas.create_line(from_x_val, from_y_val + self.sq_size, to_x_val + self.sq_size, to_y_val, fill="red", width=2)
        
        # connect bus squares at sides if on the same axis
        elif from_x_val == to_x_val and from_y_val < to_y_val:
            return self.grid_canvas.create_line(from_x_val + (self.sq_size / 2), from_y_val + self.sq_size, to_x_val + (self.sq_size / 2), to_y_val, fill="red", width=2)
        elif from_x_val == to_x_val and from_y_val > to_y_val:
            return self.grid_canvas.create_line(from_x_val + (self.sq_size / 2), from_y_val, to_x_val + (self.sq_size / 2), to_y_val + self.sq_size, fill="red", width=2)
        elif from_x_val < to_x_val and from_y_val == to_y_val:
            return self.grid_canvas.create_line(from_x_val + self.sq_size, from_y_val + (self.sq_size / 2), to_x_val, to_y_val + (self.sq_size / 2), fill="red", width=2)
        elif from_x_val > to_x_val and from_y_val == to_y_val:
            return self.grid_canvas.create_line(from_x_val, from_y_val + (self.sq_size / 2), to_x_val + self.sq_size, to_y_val + (self.sq_size / 2), fill="red", width=2)
        
        else:
            print("strange values in place wire:")
            print(from_x_val, to_x_val, from_y_val, to_y_val)
        
    def generate_axial_labels(self):
        # find how many long degrees in display area
        x_label_count = int(self.max_long - self.min_long)

        # add long degree labels
        for i in range(0, x_label_count + 1):
            x_coord = self.long_to_x(i + self.min_long)
            y_coord = self.lat_to_y(self.max_lat)
            self.grid_canvas.create_text(x_coord, y_coord, text=str(int(i + self.min_long)) + 'E', anchor='center', font=("Helvetica", 12, "bold"), fill='blue')

        # find how many lat degrees in display area
        y_label_count = int(self.max_lat - self.min_lat)

        # add lat degree labels
        for i in range(0, y_label_count + 1):
            x_coord = self.long_to_x(self.min_long)
            y_coord = self.lat_to_y(i + self.min_lat)
            self.grid_canvas.create_text(x_coord, y_coord, text=str(int(i + self.min_lat)) + 'N', anchor='center', font=("Helvetica", 12, "bold"), fill='blue')

    def get_branches_btwn_subs(self):
        branches_btwn_subs = []
        for i in range(len(self.branch_data)):
            # get data from state
            ids = self.branch_data[i]
            from_bus = self.bus_data[ids[0]]
            to_bus = self.bus_data[ids[1]]
            from_sub_num = from_bus["sub_num"]
            to_sub_num = to_bus["sub_num"]

            # filter branches within substations
            if(from_sub_num != to_sub_num):
                branches_btwn_subs.append([from_sub_num, to_sub_num])

        return branches_btwn_subs
    
    def check_and_update_substation_pixels(self, sub_num, x_val, y_val, append_overlaps=False):
        overlapped_pixels = 0
        for i in range(self.sq_size):
            for j in range(self.sq_size):
                # form tuple
                coords = (x_val + i, y_val + j)

                # see if data exists at those coordinates
                # if so append, otherwise create new list
                try:
                    pixel = self.substation_pixels[coords]
                    overlapped_pixels += 1
                    if(append_overlaps):
                        (self.substation_pixels[coords]).append(sub_num)
                except KeyError:
                    self.substation_pixels[coords] = [sub_num]

        return overlapped_pixels


    def redraw_grid(self):
        # clear canvas
        self.grid_canvas.delete("all")

        # resize canvas
        self.grid_canvas.itemconfigure("inner", width=self.grid_canvas_size, height=self.grid_canvas_size)
        self.grid_canvas.configure(scrollregion=(0, 0, self.grid_canvas_size, self.grid_canvas_size))

        # get branches between substations
        branches_btwn_subs = self.get_branches_btwn_subs()

        # place branches
        for i in range(len(branches_btwn_subs)):
            # get data from state
            ids = branches_btwn_subs[i]
            from_sub = self.substation_data[ids[0]]
            to_sub = self.substation_data[ids[1]]

            # get coords
            from_sub_lat = from_sub["lat"]
            from_sub_long = from_sub["long"]
            to_sub_lat = to_sub["lat"]
            to_sub_long = to_sub["long"]

            # draw
            self.place_wire(from_sub_long, from_sub_lat, to_sub_long, to_sub_lat)

        # clear grid mapping state
        self.substation_pixels = {}

        # draw all substations
        for i in self.substation_data:
            sub_to_place = self.substation_data[i]
            self.place_sub(sub_to_place["long"], sub_to_place["lat"], i)

        # get diagnostic information
        overlaps_list = []
        overlaps_count = 0
        for item in self.substation_pixels:
            overlaps_list.append(len(self.substation_pixels[item]))
            if(len(self.substation_pixels[item]) > 1):
                overlaps_count += 1

        # print diagnostic information to console
        print("Pixels with overlap:", overlaps_count)
        if(len(overlaps_list) > 0):
            print("Worst overlap:", max(overlaps_list))

        # draw grid labels
        self.generate_axial_labels()

if __name__ == "__main__":
    app = App()
    app.mainloop()
