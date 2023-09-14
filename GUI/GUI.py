import tkinter as tk
from tkinter import N,S,E,W
from tkinter import ttk
from tkinter import filedialog as fdialog
from tkinter import messagebox
from math import sin, cos, radians
from datetime import datetime, timedelta
from threading import Thread
from time import sleep

class App(tk.Tk):
    # constant: display size of substation squares
    sq_size = 6

    # state from user input: canvas size for scaling lat/long
    grid_canvas_size = 1000

    # constant: angle between sub branches placed from a given sub
    placement_angle = 15

    # constant: toss distance percent for approximating sub locations that don't have coords
    toss_percent = 0.02

    # state from file: values for lat/long to canvas x/y conversion
    max_lat = 0
    max_long = 0
    min_lat = 0
    min_long = 0

    # state from file: name of currently loaded grid
    grid_name = ""

    # state from file: keys are substation ids
    # vals are any data attached to a substation
    substation_data = {}

    # state from file: keys are bus ids
    # vals are any data attached to a bus
    bus_data = {}

    # state from file: keys are tuples of (from_bus, to_bus)
    # vals are any data attached to a branch
    branch_data = {}

    # state from grid (re)drawing: keys are tuples of (x_val, y_val)
    # vals are ids of substations touching that pixel
    # load_file also uses this temporarily but then calls redraw_grid which restores it
    # primarily a diagnostic tool for identifying overlapping substations
    substation_pixels = {}

    # state from grid (re)drawing: keys are substation ids
    # vals are sets of substations overlapped by the given substation
    # used for O(1) lookup of substations under a given substation
    substations_overlapped_by_sub = {}

    # state from user input: keeps track of if the grid canvas exists or not
    grid_canvas_active = False

    # state from user input: keeps track of if the sub view exists or not
    sub_view_active = False

    # state from user input: keeps track of if the bus view exists or not and what bus it's on
    bus_view_active = False
    bus_view_bus_num = None

    # state from user input: locations of the horizontal and vertical grid sliders for exiting/reentering grid view
    grid_canvas_saved_x = None
    grid_canvas_saved_y = None

    # state from user input: start of simulation
    start_time = None

    # state from running simulation: is sim running?, current time in simulation, and sim loop object
    sim_running = False
    sim_time = datetime(1970, 1, 1, 1, 1)

    # state from running simulation: for pause/play to work if grid is switched
    grid_name_at_sim_start = ""

    def __init__(self, core):
        super().__init__()
        
        self.core = core

        self.title("Space Weather Analysis Tool")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # set up closing function for killing sim on the way out
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_body_frame()

    #####################################
    # UI Creation/Destruction Functions #
    #####################################

    def create_body_frame(self):
        self.body = ttk.Frame(self, padding="3 3 12 12")

        # buttons
        self.load_btn = ttk.Button(self.body, text="Load Grid File", command=self.load_file)
        self.play_btn = ttk.Button(self.body, text="Play/Pause Simulation", command=self.play_or_pause_sim)
        self.date_label = ttk.Label(self.body, text="Solar Storm Date:")

        # enter date
        self.dmonth_val = tk.StringVar()
        self.dmonth_input = ttk.Combobox(self.body, textvariable=self.dmonth_val, width=3, state="readonly")
        self.slash1_label = ttk.Label(self.body, text="/")
        self.dday_val = tk.StringVar()
        self.dday_input = ttk.Combobox(self.body, textvariable=self.dday_val, width=3, state="readonly")
        self.slash2_label = ttk.Label(self.body, text="/")
        self.dyear_val = tk.StringVar()
        self.dyear_input = ttk.Combobox(self.body, textvariable=self.dyear_val, width=5, state="readonly")

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

        # button configuration
        self.play_btn.state(["disabled"])

        # enter zoom
        self.zoom_label = tk.Label(self.body, text="Zoom: ")
        self.zoom_val = tk.StringVar()
        self.zoom_input = ttk.Combobox(self.body, textvariable=self.zoom_val, width=5, state="readonly")

        # date input configuration
        self.dmonth_input.set("01")
        self.dmonth_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1,13))))
        self.dmonth_input.bind('<<ComboboxSelected>>', self.set_days_for_month)
        self.dday_input.set("01")
        self.dday_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1,32))))
        self.dyear_input.set("2023")
        self.dyear_input["values"] = list(map(lambda val : str(val), list(range(1970, 2038))))
        self.dyear_input.bind('<<ComboboxSelected>>', self.check_for_leap_year)

        # time input configuration
        self.hour_input.set("01")
        self.hour_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1,13))))
        self.minute_input.set("00")
        self.minute_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(0,60))))
        self.ampm_input.set("AM")
        self.ampm_input["values"] = ["AM", "PM"]

        # zoom configuration
        self.zoom_input.set("10%")
        self.zoom_input["values"] = list(map(lambda val : str(val * 10) + '%', list(range(1, 21))))
        self.zoom_input.bind('<<ComboboxSelected>>', self.execute_zoom)
        self.zoom_input.state(["disabled"])

        # widget placement
        self.body.grid(column=0, row=0, sticky=(N,W,E,S))

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

    def create_grid_canvas(self):
        # canvas initialization
        self.h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.grid_canvas = tk.Canvas(self, scrollregion=(0, 0, self.grid_canvas_size, self.grid_canvas_size), yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set, background="white")
        self.h_scroll['command'] = self.grid_canvas.xview
        self.v_scroll['command'] = self.grid_canvas.yview

        # canvas placement
        self.h_scroll.grid(column=0, row=2, columnspan=15, sticky=(W,S,E))
        self.v_scroll.grid(column=15,row=1, rowspan=2, sticky=(N,S,E))
        self.grid_canvas.grid(column=0, row=1, columnspan=5, sticky=(N,W,E,S))

        # load slider positions if positions have been saved
        if(self.grid_canvas_saved_x != None and self.grid_canvas_saved_y != None):
            self.grid_canvas.xview_moveto(self.grid_canvas_saved_x)
            self.grid_canvas.yview_moveto(self.grid_canvas_saved_y)

        # enable zooming
        self.zoom_input.state(["!disabled"])

        # declare canvas as active
        self.grid_canvas_active = True

    def destroy_grid_canvas(self, save_slider_positions=True):
        # save slider positions if set to
        if(save_slider_positions):
            self.grid_canvas_saved_x = self.grid_canvas.xview()[0]
            self.grid_canvas_saved_y = self.grid_canvas.yview()[0]
        else:
            self.grid_canvas_saved_x = None
            self.grid_canvas_saved_y = None

        # canvas destruction
        self.h_scroll.destroy()
        self.v_scroll.destroy()
        self.grid_canvas.destroy()

        # disable zooming
        self.zoom_input.state(["disabled"])

        # declare canvas as inactive
        self.grid_canvas_active = False

    def create_sub_view(self, sub_nums):
        # create internal sub frame
        self.sub_frame = ttk.Frame(self.body)
        self.sub_frame.grid(column=0, row=1, sticky=(N,W), columnspan=15)

        # dynamically build bus buttons
        current_row = 1
        self.sub_labels = []
        self.bus_btn_frames = []
        self.bus_btn_sets = []
        for sub_num in sub_nums:
            # create label for substations
            sub_label = ttk.Label(self.sub_frame, text="Substation " + str(sub_num) + ":")
            sub_label.grid(column=0, row=current_row, sticky=(N,W), pady=8)
            self.sub_labels.append(sub_label)
            current_row += 1

            # create frame to contain bus buttons
            bus_btn_frame = ttk.Frame(self.sub_frame)
            bus_btn_frame.grid(column=0, row=current_row, sticky=(N,W), columnspan=15)
            self.bus_btn_frames.append(bus_btn_frame)

            # create bus buttons
            current_column = 0
            buses = self.get_buses_for_sub(sub_num)
            bus_btns = []
            for bus_num in buses:
                bus_btn = ttk.Button(bus_btn_frame, text="Bus " + str(bus_num), command=self.bus_btn_click(sub_nums, bus_num))
                bus_btn.grid(column=current_column, row=current_row)
                bus_btns.append(bus_btn)
                current_column += 1

            self.bus_btn_sets.append(bus_btns)
            current_row += 1

        # back button
        self.back_to_grid_btn = ttk.Button(self.sub_frame, text="Back", command=self.back_to_grid)
        self.back_to_grid_btn.grid(column=0, row=current_row, sticky=(N,W), pady=16)

        # declare view as active
        self.sub_view_active = True

    def destroy_sub_view(self):
        self.sub_frame.destroy()
        self.sub_labels = []
        self.bus_btn_frames = []
        self.bus_btn_sets = []
        self.sub_view_active = False

    def create_bus_view(self, sub_nums, bus_num):
        branches = self.get_branches_for_bus(bus_num)
        
        to_buses = []
        for branch in branches:
            if(branch[0] != bus_num):
                to_buses.append(branch[0])
            else:
                to_buses.append(branch[1])

        # create bus label
        self.bus_label = ttk.Label(self.body, text="Bus " + str(bus_num) + ":")
        self.bus_label.grid(column=0, row=1, sticky=(N,W), padx=4, pady=8)

        # create bus frame
        self.bus_frame = ttk.Frame(self.body)
        self.bus_frame.grid(column=0, row=2, sticky=(N,W), columnspan=15)

        self.branch_display_vals = {}
        current_column = 0
        for i in range(len(branches)):
            current_row = 2

            # create branch label
            branch_label = ttk.Label(self.bus_frame, text="To Bus " + str(to_buses[i]) + " at Sub " + str(self.bus_data[to_buses[i]]["sub_num"]) + ":")
            branch_label.grid(column=current_column, row=current_row, sticky=(N,W), padx=4)
            self.branch_display_vals[branches[i]] = {"branch_label":branch_label}
            current_row += 1

            # create GIC label
            GIC_label = ttk.Label(self.bus_frame, text="GIC: XXX.X")
            GIC_label.grid(column=current_column, row=current_row, sticky=(N,W), padx=4)
            self.branch_display_vals[branches[i]]["GIC_label"] = GIC_label
            current_row += 1

            # create VLEVEL and TTC labels
            if(self.branch_data[branches[i]]["has_trans"]):
                VLEVEL_label = ttk.Label(self.bus_frame, text="VLEVEL: XXX.X")
                VLEVEL_label.grid(column=current_column, row=current_row, sticky=(N,W), padx=4)
                self.branch_display_vals[branches[i]]["VLEVEL_label"] = VLEVEL_label
                current_row += 1

                TTC_label = ttk.Label(self.bus_frame, text="TTC: XXX.X")
                TTC_label.grid(column=current_column, row=current_row, sticky=(N,W), padx=4)
                self.branch_display_vals[branches[i]]["TTC_label"] = TTC_label

            current_column += 1

        # create back button
        self.back_to_sub_btn = ttk.Button(self.body, text="Back", command=self.back_to_sub(sub_nums))
        self.back_to_sub_btn.grid(column=0, row=6, sticky=(N,W), pady=16, padx=4)

        # put bus_num in state for sim
        self.bus_view_bus_num = bus_num

        # declare view as active
        self.bus_view_active = True

    def destroy_bus_view(self):
        self.bus_label.destroy()
        self.bus_frame.destroy()
        self.branch_labels = []
        self.bus_view_active = False
        self.back_to_sub_btn.destroy()

    ###########################
    # State Loading Functions #
    ###########################

    def load_file(self, *args):
        "Loads grid file in aux format (legacy variable names, older file headers) chosen by the user into state"
        filetypes = (("aux files", "*.aux"),("AUX files", "*.AUX"),)

        # open file
        try:
            with fdialog.askopenfile(filetypes=filetypes) as grid_file:
                f_str = grid_file.read()

                # detect whether or not legacy headers are in use
                # TODO: support legacy headers
                legacy_headers = False
                if "DATA (" in f_str:
                    legacy_headers = True

                f_data = {}

                # parse the data into a dictionary structure
                if not legacy_headers:
                    # initialize and run through state machine that parses a PowerWorld aux file
                    # into a dictionary of sections, each containing a list of items within
                    # that section, the states are:
                    # waiting, section_header, waiting_data_headers,
                    # data_headers, waiting_data, data, datapoint, quoted
                    # ignore_line, ignore_block
                    # TODO: ignore line in waiting state
                    # TODO: improve ignore block
                    parser_state = "waiting"
                    accumulator = ""
                    section_header = None
                    branch_section = 0
                    data_headers = []
                    cur_data = 0
                    data_line = {}
                    for c in f_str:
                        if(parser_state == "waiting"):
                            # section header not yet reached
                            if(c.isspace()):
                                continue

                            # section header reached, begin building
                            accumulator += c
                            parser_state = "section_header"
                        elif(parser_state == "section_header"):
                            # end of section header reached
                            if(c.isspace()):
                                # handle two "Branch" sections
                                if(accumulator == "Branch"):
                                    accumulator += str(branch_section)
                                    branch_section += 1

                                section_header = accumulator
                                accumulator = ""
                                f_data[section_header] = []
                                parser_state = "waiting_data_headers"
                                continue

                            # accumulate section header
                            accumulator += c
                        elif(parser_state == "waiting_data_headers"):
                            if(c == '('):
                                parser_state = "data_headers"
                                continue

                            if not(c.isspace()):
                                messagebox.showerror("file load error", "Unexpected character before data headers in " + section_header + " section")
                                return
                        elif(parser_state == "data_headers"):
                            # push a data header and change states
                            if(c == ')'):
                                data_headers.append(accumulator)
                                accumulator = ""
                                parser_state = "waiting_data"
                                continue
                            # push a data header
                            if(c == ','):
                                data_headers.append(accumulator)
                                accumulator = ""
                                continue

                            # accumulate a data header
                            accumulator += c
                        elif(parser_state == "waiting_data"):
                            if(c == '{'):
                                parser_state = "data"
                                continue

                            if not(c.isspace()):
                                messagebox.showerror("file load error", "Unexpected character before data in " + section_header + " section")
                                return
                        elif(parser_state == "data"):
                            if(c == '}'):
                                if(cur_data != 0):
                                    messagebox.showerror("file load error", "Malformed data in " + section_header + " section")
                                    return
                                section_header = None
                                data_headers = []
                                parser_state = "waiting"
                                continue
                            if(c == '\"'):
                                parser_state = "quoted"
                                continue
                            if(c == '/'):
                                accumulator += c
                                if(accumulator == "//"):
                                    accumulator = ""
                                    parser_state = "ignore_line"
                                continue
                            if(c == '<'):
                                parser_state = "ignore_block"
                                continue
                            if(c.isspace()):
                                continue

                            # datapoint hit
                            accumulator += c
                            parser_state = "datapoint"
                        elif(parser_state == "datapoint"):
                            if(c.isspace()):
                                try:
                                    data_line[data_headers[cur_data]] = accumulator
                                except:
                                    print(data_line)
                                    print(data_headers)
                                    print(cur_data)
                                    break
                                cur_data += 1
                                if(cur_data == len(data_headers)):
                                    f_data[section_header].append(data_line)
                                    data_line = {}
                                    cur_data = 0
                                accumulator = ""
                                parser_state = "data"
                                continue

                            # accumulate datapoint
                            accumulator += c
                        elif(parser_state == "quoted"):
                            if(c == '\"'):
                                data_line[data_headers[cur_data]] = accumulator
                                cur_data += 1
                                if(cur_data == len(data_headers)):
                                    f_data[section_header].append(data_line)
                                    data_line = {}
                                    cur_data = 0
                                accumulator = ""
                                parser_state = "data"
                                continue

                            # accumulate quoted datapoint
                            accumulator += c
                        elif(parser_state == "ignore_line"):
                            if(c == '\n'):
                                parser_state = "data"
                        elif(parser_state == "ignore_block"):
                            if(c == '>'):
                                parser_state = "data"

                    # find line and transformer sections
                    branch_to_type = {}
                    for section in f_data:
                        if(section[:6] == "Branch"):
                            if(f_data[section][0]["BranchDeviceType"] == "Line"):
                                branch_to_type[section] = "Line"
                            elif(f_data[section][0]["BranchDeviceType"] == "Transformer"):
                                branch_to_type[section] = "Transformer"

                    # move line and transformer sections
                    for section in branch_to_type:
                        f_data[branch_to_type[section]] = f_data.pop(section)
                
                # clear any active views other than grid
                if(self.sub_view_active):
                    self.destroy_sub_view()
                if(self.bus_view_active):
                    self.destroy_bus_view()

                # perform mapping calculations at 20% graph size
                # at 10% is possible but overkill for getting a legible graph at 100%
                self.grid_canvas_size = 2000

                # get substation data
                # TODO: handle missing latitude or longitude data
                self.substation_data = {}
                self.substation_pixels = {}
                sub_lats = []
                sub_longs = []
                try:
                    for sub in f_data["Substation"]:
                        self.substation_data[int(sub["Number"])] = {
                            "name" : sub["Name"],
                            "lat" : float(sub["Latitude"]),
                            "long" : float(sub["Longitude"])}
                        sub_lats.append(float(sub["Latitude"]))
                        sub_longs.append(float(sub["Longitude"]))
                except KeyError:
                    messagebox.showerror("file load error", "Substation data missing")
                    return
                
                # load limits into state
                self.min_long = min(sub_longs)
                self.min_lat = min(sub_lats)
                self.max_long = max(sub_longs)
                self.max_lat = max(sub_lats)

                # get bus data
                self.bus_data = {}
                try:
                    for bus in f_data["Bus"]:
                        self.bus_data[int(bus["Number"])] = {
                            "name" : bus["Name"],
                            "sub_num" : int(bus["SubNumber"])
                        }
                except KeyError:
                    messagebox.showerror("file load error", "Bus data missing")
                    return
                
                # get line and transformer data
                self.branch_data = {}
                try:
                    for line in f_data["Line"]:
                        self.branch_data[(int(line["BusNumFrom"]), int(line["BusNumTo"]), int(line["Circuit"]))] = {
                            "has_trans" : False
                        }
                except KeyError:
                    messagebox.showerror("file load error", "Transformer data missing")
                    return
                
                try:
                    for trans in f_data["Transformer"]:
                        self.branch_data[(int(trans["BusNumFrom"]), int(trans["BusNumTo"]), int(trans["Circuit"]))] = {
                            "has_trans" : True
                        }
                except KeyError:
                    messagebox.showerror("file load error", "Transformer data missing")
                    return

                self.grid_name = grid_file.name[:-4]

                self.core.save_grid_data(self.grid_name, self.substation_data, self.bus_data, self.branch_data)

                # reset grid size back to user-defined value before displaying
                self.grid_canvas_size = int(self.zoom_val.get()[:-1]) * 0.01 * 10000

                self.redraw_grid()
                self.title("Space Weather Analysis Tool: " + self.grid_name)

                # enable simulating
                self.play_btn.state(["!disabled"])
        
        # ignore cancel hit on filedialog
        except AttributeError:
            None

    ###############################
    # Grid Canvas Input Functions #
    ###############################

    def execute_zoom(self, *args):
        # update grid_canvas_size
        self.grid_canvas_size = int(self.zoom_val.get()[:-1]) * 0.01 * 10000

        # carry out change
        if(self.grid_canvas_active):
            self.redraw_grid()

    def grid_canvas_sub_click(self, sub_num):
        def event_handler(event):
            # get any subs under clicked sub and pass them all to sub view
            subs_in_click = [sub_num]
            try:
                for sub in self.substations_overlapped_by_sub[sub_num]:
                    subs_in_click.append(sub)
            except KeyError:
                None

            self.destroy_grid_canvas()
            self.create_sub_view(subs_in_click)

        return event_handler
    
    #########################
    # Other Input Functions #
    #########################

    def test_fn(self, *args):
        print("Button pressed.")

    def set_days_for_month(self, *args):
        val = int(self.dmonth_val.get())
        days_in_month = 0
        if(val in [1, 3, 5, 7, 8, 10, 12]):
            days_in_month = 31
        elif(val in [4, 6, 9, 11]):
            days_in_month = 30
        elif(val == 2):
            # leap year condition
            year_val = int(self.dyear_input.get())
            if((((year_val % 4) == 0) and not ((year_val % 100) == 0)) or ((year_val % 400) == 0)):
                days_in_month = 29
            else:
                days_in_month = 28

        self.dday_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1, days_in_month + 1))))

        # if on an invalid day, set back to a valid one
        if(int(self.dday_val.get()) > days_in_month):
            self.dday_input.set(str(days_in_month).rjust(2, "0"))

    def check_for_leap_year(self, *args):
        val = int(self.dyear_val.get())

        # leap year condition
        month_val = int(self.dmonth_val.get())
        if(month_val == 2):
            days_in_month = 28
            if((((val % 4) == 0) and not ((val % 100) == 0)) or ((val % 400) == 0)):
                days_in_month = 29
            
            self.dday_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1, days_in_month + 1))))

            # if on an invalid day, set back to a valid one
            if(int(self.dday_val.get()) > days_in_month):
                self.dday_input.set(str(days_in_month).rjust(2, "0"))

    def back_to_grid(self, *args):
        self.destroy_sub_view()
        self.create_grid_canvas()
        self.redraw_grid()

    def bus_btn_click(self, sub_nums, bus_num):
        def event_handler(*args):
            self.destroy_sub_view()
            self.create_bus_view(sub_nums, bus_num)

        return event_handler
    
    def back_to_sub(self, sub_nums):
        def event_handler(*args):
            self.destroy_bus_view()
            self.create_sub_view(sub_nums)

        return event_handler

    ########################
    # Simulation Functions #
    ########################

    # TODO: fix simulation functionality

    # https://pythonguides.com/python-tkinter-colors/
    def rgb_hack(self, rgb):
        return "#%02x%02x%02x" % rgb  

    def simulation_loop(self):
        """Loop that runs in a thread and carries out simulation playback.
        The simulation runs at a scale of roughly 1 second per minute and loops after
        it reaches an hour from start time."""
        local_core = Core()
        local_core.log_to_file("GUI", "Local Core Online")
        while(self.sim_running):
            # update time label
            self.time_label["text"] = "Time In Simulation: " + self.sim_time.strftime("%I:%M %p")

            # load data for minute
            time_data = local_core.get_data_for_time(self.grid_name, self.sim_time)

            gics = []
            for point in time_data:
                gics.append(point[4])

            max_gic = max(gics)
            min_gic = min(gics)

            if(self.grid_canvas_active):
                # update all branch colors
                for point in time_data:
                    try:
                        branch_ids = (point[0], point[1])
                        branch = self.branch_data[branch_ids]
                        try:
                            line_id = branch["line_id"]
                            gic = point[4]

                            # normalize gic
                            normalized = (gic - min_gic) / (max_gic - min_gic)

                            # red is max gic, blue is min gic
                            self.grid_canvas.itemconfig(line_id, fill=self.rgb_hack((int(255 * normalized), 0, int(255 * (1 - normalized)))))
                        except KeyError:
                            continue
                    except:
                        break

            elif(self.bus_view_active):
                # update all labels
                try:
                    branches = self.get_branches_for_bus(self.bus_view_bus_num)
                    for point in time_data:
                        branch_ids = (point[0], point[1])
                        if(branch_ids in branches):
                            labels = self.branch_display_vals[branch_ids]
                            labels["GIC_label"]["text"] = "GIC: " + str(point[4])
                            if(self.branch_data[branch_ids]["has_trans"]):
                                labels["VLEVEL_label"]["text"] = "VLEVEL: " + str(point[5])
                                labels["TTC_label"]["text"] = "TTC: " + str(point[6])
                except:
                    continue

            # update sim time
            sleep(1)
            self.sim_time += timedelta(minutes=1)
            if(self.sim_time == (self.start_time + timedelta(minutes=60))):
                self.sim_time = self.start_time

    def play_or_pause_sim(self, *args):
        if(self.sim_running == False):
            # lock inputs
            self.dmonth_input.state(["disabled"])
            self.dday_input.state(["disabled"])
            self.dyear_input.state(["disabled"])
            self.hour_input.state(["disabled"])
            self.minute_input.state(["disabled"])
            self.ampm_input.state(["disabled"])
            self.load_btn.state(["disabled"])

            # load date and time
            month = int(self.dmonth_val.get())
            day = int(self.dday_val.get())
            year = int(self.dyear_val.get())
            hour = int(self.hour_val.get())
            minute = int(self.minute_input.get())
            ampm = self.ampm_input.get()

            # convert from 12hr to 24hr
            if(ampm == "PM"):
                if(hour != 12):
                    hour += 12

            if(ampm == "AM" and hour == 12):
                hour = 0

            # create start datetime
            set_start_time = datetime(year, month, day, hour, minute)

            # set sim_time if out of range, otherwise use existing value
            if(self.sim_time < set_start_time or self.sim_time > (set_start_time + timedelta(minutes=59))):
                self.sim_time = set_start_time

            # load hour into database
            if(self.start_time != set_start_time or self.grid_name != self.grid_name_at_sim_start):
                self.start_time = set_start_time
                self.grid_name_at_sim_start = self.grid_name
                self.core.create_hour_of_data(self.grid_name, self.start_time)
                messagebox.showinfo("Loaded!", "Simulation has been loaded!")

            # close database here so sim thread can connect
            self.core.close_conns()

            # start simulation loop
            self.sim_running = True
            self.sim_thread = Thread(target=self.simulation_loop)
            self.sim_thread.start()
        else:
            # kill simulation loop
            self.sim_running = False
            self.sim_thread.join(0.5)

            # reopen database
            self.core.reopen_conns()

            # unlock inputs
            self.dmonth_input.state(["!disabled"])
            self.dday_input.state(["!disabled"])
            self.dyear_input.state(["!disabled"])
            self.hour_input.state(["!disabled"])
            self.minute_input.state(["!disabled"])
            self.ampm_input.state(["!disabled"])
            self.load_btn.state(["!disabled"])

    def on_closing(self):
        if(self.sim_running):
            self.sim_running = False
            self.sim_thread.join(0.5)

        self.destroy()

    ########################
    # Conversion Functions #
    ########################

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
    
    ####################
    # Getter Functions #
    ####################

    def get_branches_btwn_subs(self):
        """Finds all the branches in the grid that run between subs and returns
        the subs and buses connected in each branch"""
        branches_btwn_subs = []
        for ids in self.branch_data:
            # get data from state
            from_bus = self.bus_data[ids[0]]
            to_bus = self.bus_data[ids[1]]
            from_sub_num = from_bus["sub_num"]
            to_sub_num = to_bus["sub_num"]

            # filter branches within substations
            if(from_sub_num != to_sub_num):
                branches_btwn_subs.append([from_sub_num, to_sub_num, ids[0], ids[1], ids[2]])

        return branches_btwn_subs
    
    def get_buses_for_sub(self, sub_num):
        bus_nums = []
        for bus_num in self.bus_data:
            if(self.bus_data[bus_num]["sub_num"] == sub_num):
                bus_nums.append(bus_num)

        return bus_nums
    
    def get_branches_for_bus(self, bus_num):
        branch_tuples = []
        for branch_tuple in self.branch_data:
            if(branch_tuple[0] == bus_num or branch_tuple[1] == bus_num):
                branch_tuples.append(branch_tuple)

        return branch_tuples
    
    ##########################
    # Grid Drawing Functions #
    ##########################

    def place_sub(self, long, lat, sub_num):
        # convert lat/long to x/y
        x_val = self.long_to_x(long)
        y_val = self.lat_to_y(lat)

        # add pixels to grid mapping
        self.check_and_update_substation_pixels(sub_num, x_val, y_val, append_overlaps=True)

        # place sub rectangle and bind events
        rect_id = self.grid_canvas.create_rectangle((x_val, y_val, x_val + self.sq_size, y_val + self.sq_size), fill="#00ff40", tags=('palette', 'palettered'))
        self.grid_canvas.tag_bind(rect_id, "<Button-1>", self.grid_canvas_sub_click(sub_num))
        
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
            return self.grid_canvas.create_line(from_x_val + self.sq_size, from_y_val + self.sq_size, to_x_val, to_y_val, fill="blue", width=2)
        elif from_x_val > to_x_val and from_y_val > to_y_val:
            return self.grid_canvas.create_line(from_x_val, from_y_val, to_x_val + self.sq_size, to_y_val + self.sq_size, fill="blue", width=2)
        elif from_x_val < to_x_val and from_y_val > to_y_val:
            return self.grid_canvas.create_line(from_x_val + self.sq_size, from_y_val, to_x_val, to_y_val + self.sq_size, fill="blue", width=2)
        elif from_x_val > to_x_val and from_y_val < to_y_val:
            return self.grid_canvas.create_line(from_x_val, from_y_val + self.sq_size, to_x_val + self.sq_size, to_y_val, fill="blue", width=2)
        
        # connect bus squares at sides if on the same axis
        elif from_x_val == to_x_val and from_y_val < to_y_val:
            return self.grid_canvas.create_line(from_x_val + (self.sq_size / 2), from_y_val + self.sq_size, to_x_val + (self.sq_size / 2), to_y_val, fill="blue", width=2)
        elif from_x_val == to_x_val and from_y_val > to_y_val:
            return self.grid_canvas.create_line(from_x_val + (self.sq_size / 2), from_y_val, to_x_val + (self.sq_size / 2), to_y_val + self.sq_size, fill="blue", width=2)
        elif from_x_val < to_x_val and from_y_val == to_y_val:
            return self.grid_canvas.create_line(from_x_val + self.sq_size, from_y_val + (self.sq_size / 2), to_x_val, to_y_val + (self.sq_size / 2), fill="blue", width=2)
        elif from_x_val > to_x_val and from_y_val == to_y_val:
            return self.grid_canvas.create_line(from_x_val, from_y_val + (self.sq_size / 2), to_x_val + self.sq_size, to_y_val + (self.sq_size / 2), fill="blue", width=2)
        
        else:
            self.core.log_to_file("GUI", "Strange values in place wire: " + str(from_x_val) + " " + str(to_x_val) + " "
                                  + str(from_y_val) + " " +  str(to_y_val))
        
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
        # print message to log
        self.core.log_to_file("GUI", "Drawing Grid at: " + self.zoom_val.get())

        # check if grid canvas is active, update if so, create if not
        if(self.grid_canvas_active):
            # clear canvas
            self.grid_canvas.delete("all")

            # resize canvas
            self.grid_canvas.itemconfigure("inner", width=self.grid_canvas_size, height=self.grid_canvas_size)
            self.grid_canvas.configure(scrollregion=(0, 0, self.grid_canvas_size, self.grid_canvas_size))
        else:
            self.create_grid_canvas()

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
            line_id = self.place_wire(from_sub_long, from_sub_lat, to_sub_long, to_sub_lat)

            # store lines in state so they can be colored during simulation
            self.branch_data[(ids[2], ids[3], ids[4])]["line_id"] = line_id

        # clear grid mapping state
        self.substation_pixels = {}
        self.substations_overlapped_by_sub = {}

        # draw all substations
        for i in self.substation_data:
            sub_to_place = self.substation_data[i]
            self.place_sub(sub_to_place["long"], sub_to_place["lat"], i)

        # get overlapped substations
        for i in self.substation_pixels:
            subs = self.substation_pixels[i]

            # ignore pixels with only one sub
            if(len(subs) < 2):
                continue

            # for pixels with multiple subs, add those subs to each set of subs overlapped by each sub
            for i in range(len(subs)):
                # don't add self to set
                subs_without_sub = []
                for j in range(len(subs)):
                    if j != i:
                        subs_without_sub.append(subs[j])

                # if sub hasn't been entered, create new set, otherwise unite new overlaps with existing set
                try:
                    self.substations_overlapped_by_sub[subs[i]] |= set(subs_without_sub)
                except KeyError:
                    self.substations_overlapped_by_sub[subs[i]] = set(subs_without_sub)

        # check how many of the overlapped subs started with coords
        overlapped_subs_that_started_w_coords = 0
        for sub_num in self.substations_overlapped_by_sub:
            if(self.substation_data[sub_num]["started_w_coords"]):
                overlapped_subs_that_started_w_coords += 1

        # get rest of diagnostic information
        overlaps_list = []
        overlaps_count = 0
        for i in self.substation_pixels:
            overlaps_list.append(len(self.substation_pixels[i]))
            if(len(self.substation_pixels[i]) > 1):
                overlaps_count += 1

        # log diagnostic information
        self.core.log_to_file("GUI", "Substations with overlap: " + str(len(self.substations_overlapped_by_sub)))
        self.core.log_to_file("GUI", "Substations with overlap that started with coordinates: " + str(overlapped_subs_that_started_w_coords))
        self.core.log_to_file("GUI", "Pixels with overlap: " + str(overlaps_count))
        if(len(overlaps_list) > 0):
            self.core.log_to_file("GUI", "Worst overlap: " + str(max(overlaps_list)))

        # draw grid labels
        self.generate_axial_labels()
