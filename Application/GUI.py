import tkinter as tk
from tkinter import N,S,E,W
from tkinter import ttk
from tkinter import filedialog as fdialog
from tkinter import messagebox
from datetime import datetime, timedelta, date, timezone
from threading import Thread, Semaphore, Event
from time import sleep

class App(tk.Tk):
    #############
    # Constants #
    #############

    # Constant: Display size of substation squares
    sq_size = 6

    # Constant: How many branches to display per row in bus view
    branches_per_row = 3

    #########
    # State #
    #########

    # State from user input: Canvas size for scaling lat/long
    grid_canvas_size = 1000

    # State from file: Values for lat/long to canvas x/y conversion
    max_lat = 0
    max_long = 0
    min_lat = 0
    min_long = 0

    # State from file: Name of currently loaded grid
    grid_name = ""

    # State from file: Keys are substation ids, and
    # values are any data attached to a substation
    substation_data = {}

    # State from file: Keys are bus ids, and
    # values are any data attached to a bus
    bus_data = {}

    # State from file: Keys are tuples of (from_bus, to_bus, circuit), and
    # values are any data attached to a branch
    branch_data = {}

    # State from grid (re)drawing: Keys are tuples of (x_val, y_val), and
    # values are ids of substations touching that pixel.
    # load_file also uses this temporarily but then calls redraw_grid which restores it.
    # Primarily a diagnostic tool for identifying overlapping substations.
    substation_pixels = {}

    # State from grid (re)drawing: Keys are substation ids, and
    # values are sets of substations overlapped by the given substation.
    # Used for O(1) lookup of substations under a given substation.
    substations_overlapped_by_sub = {}

    # State from user input: Keeps track of if the grid canvas is loaded or not
    grid_canvas_active = False

    # State from user input: Keeps track of if the sub view is loaded or not
    sub_view_active = False

    # State from user input: Keeps track of if the bus view is loaded or not and what bus it's on
    bus_view_active = False
    bus_view_bus_num = None

    # State from user input: Locations of the horizontal and vertical grid sliders for exiting/reentering grid view
    grid_canvas_saved_x = None
    grid_canvas_saved_y = None

    # State from user input: Start time in simulation
    start_time = None

    # State from running simulation: Is sim running?, has sim been cancelled?, current time in simulation, is the sim paused?, and sim thread object
    sim_running = False
    sim_cancelled = False
    sim_time = datetime(1970, 1, 1, 1, 1)
    sim_pause = None
    sim_thread = None

    def __init__(self, core):
        super().__init__()
        
        self.core = core

        self.title("Space Weather Analysis Tool")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.geometry("1200x1000")

        # set up on closing function so that program exits correctly
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_body_frame()

    def on_closing(self):
        """ This method ensures that the application closes gracefully by
            ensuring that the simulation thread terminates, starting its own
            closing process, and queueing the Core's close method
        """
        if(self.sim_running):
            self.sim_running = False
            self.sim_thread.join(0.5)

        self.quit()
        self.core.send_request(self.core.close_application)

    #####################################
    # UI Creation/Destruction Functions #
    #####################################

    # - These functions are for creating and destroying sections of the UI
    # - They facilitate initializing the UI and switching between different views

    def create_body_frame(self):
        """ This method initializes the UI's body and user inputs
        """
        self.body = ttk.Frame(self, padding="3 3 12 12")

        # buttons
        self.load_btn = ttk.Button(self.body, text="Load Grid File", command=self.load_file)
        self.start_btn = ttk.Button(self.body, text="Start Simulation", command=self.configure_sim)

        # play button initial state
        self.start_btn.state(["disabled"])

        # zoom input field
        self.zoom_label = tk.Label(self.body, text="Zoom: ")
        self.zoom_val = tk.StringVar()
        self.zoom_input = ttk.Combobox(self.body, textvariable=self.zoom_val, width=5, state="readonly")

        # get current date
        date_today = date.today()

        # zoom configuration
        self.zoom_input.set("10%")
        self.zoom_input["values"] = list(map(lambda val : str(val * 10) + '%', list(range(1, 21))))
        self.zoom_input.bind('<<ComboboxSelected>>', self.execute_zoom)
        self.zoom_input.state(["disabled"])

        # widget placement
        self.body.grid(column=0, row=0, sticky=(N,W,E,S))

        self.load_btn.grid(column=0, row=0, sticky=(N,W))
        self.start_btn.grid(column=1, row=0, sticky=(N,W))

        self.zoom_label.grid(column=2, row=0, sticky=(W,E), padx=2)
        self.zoom_input.grid(column=3, row=0, sticky=(W,E))

    def switch_to_sim_active_ui(self):
        self.load_btn.destroy()
        self.start_btn.destroy()

        self.exit_btn = ttk.Button(self.body, text="Exit", command=self.stop_sim)
        self.play_btn = ttk.Button(self.body, text="Play", command=self.resume_sim)
        self.pause_btn = ttk.Button(self.body, text="Pause", command=self.pause_sim)

        self.time_label = ttk.Label(self.body, text=self.sim_time.strftime("%m/%d/%Y, %H:%M:%S"))

        self.exit_btn.grid(column=0, row=0, sticky=(N,W))
        self.play_btn.grid(column=1, row=0, sticky=(N,W))
        self.pause_btn.grid(column=2, row=0, sticky=(N,W))

        self.zoom_label.grid(column=3, row=0, sticky=(W,E), padx=2)
        self.zoom_input.grid(column=4, row=0, sticky=(W,E))

        self.time_label.grid(column=5, row=0, sticky=(W,E), padx=2)

    def switch_to_sim_not_active_ui(self):
        self.exit_btn.destroy()
        self.play_btn.destroy()
        self.pause_btn.destroy()
        self.time_label.destroy()

        self.load_btn = ttk.Button(self.body, text="Load Grid File", command=self.load_file)
        self.start_btn = ttk.Button(self.body, text="Start Simulation", command=self.configure_sim)

        self.load_btn.grid(column=0, row=0, sticky=(N,W))
        self.start_btn.grid(column=1, row=0, sticky=(N,W))

        self.zoom_label.grid(column=2, row=0, sticky=(W,E), padx=2)
        self.zoom_input.grid(column=3, row=0, sticky=(W,E))        

    def create_grid_canvas(self):
        """ This method creates the grid view, which is initially empty
        """
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
        """ This method destroys the grid vew
            @param: save_slider_positions: Boolean determining whether to save or reset the positions of the grid view sliders
        """
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

    def create_sim_menu_body(self):
        self.sim_menu.protocol("WM_DELETE_WINDOW", self.cancel_sim_config)

        self.sim_body = ttk.Frame(self.sim_menu, padding="3 3 12 12")

        self.noaa_section_label = ttk.Label(self.sim_body, text="Use Data From NOAA")

        self.date_label = ttk.Label(self.sim_body, text="Solar Storm Date:")

        # date input fields
        self.dmonth_val = tk.StringVar()
        self.dmonth_input = ttk.Combobox(self.sim_body, textvariable=self.dmonth_val, width=3, state="readonly")
        self.slash1_label = ttk.Label(self.sim_body, text="/")
        self.dday_val = tk.StringVar()
        self.dday_input = ttk.Combobox(self.sim_body, textvariable=self.dday_val, width=3, state="readonly")
        self.slash2_label = ttk.Label(self.sim_body, text="/")
        self.dyear_val = tk.StringVar()
        self.dyear_input = ttk.Combobox(self.sim_body, textvariable=self.dyear_val, width=5, state="readonly")

        # time input fields
        self.time_in_label = ttk.Label(self.sim_body, text="Solar Storm Time:")
        self.hour_val = tk.StringVar()
        self.hour_input = ttk.Combobox(self.sim_body, textvariable=self.hour_val, width=3, state="readonly")
        self.minute_val = tk.StringVar()
        self.minute_input = ttk.Combobox(self.sim_body, textvariable=self.minute_val, width=3, state="readonly")
        self.ampm_val = tk.StringVar()
        self.ampm_input = ttk.Combobox(self.sim_body, textvariable=self.ampm_val, width=3, state="readonly")

        self.confirm_btn = ttk.Button(self.sim_body, text="Confirm", command=self.play_sim_noaa)

        # load storm file input
        self.file_section_label = ttk.Label(self.sim_body, text="Load Historic Storm Data File")
        self.load_storm_btn = ttk.Button(self.sim_body, text="Load File", command=self.play_sim_file)

        # cancel out input
        self.cancel_section_label = ttk.Label(self.sim_body, text="Cancel Simulation Configuration")
        self.cancel_storm_btn = ttk.Button(self.sim_body, text="Cancel", command=self.cancel_sim_config)

        # get current date
        date_today = date.today()

        # date input configuration with current date as initial value
        self.dmonth_input.set(str(date_today.month))
        self.dmonth_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1,13))))
        self.dmonth_input.bind('<<ComboboxSelected>>', self.set_days_for_month)
        self.dday_input.set(str(date_today.day))
        self.dday_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1,32))))
        self.dyear_input.set(str(date_today.year))
        self.dyear_input["values"] = list(map(lambda val : str(val), list(range(1970, 2038))))
        self.dyear_input.bind('<<ComboboxSelected>>', self.check_for_leap_year)

        # time input configuration
        self.hour_input.set("01")
        self.hour_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(1,13))))
        self.minute_input.set("00")
        self.minute_input["values"] = list(map(lambda val : str(val).rjust(2, "0"), list(range(0,60))))
        self.ampm_input.set("AM")
        self.ampm_input["values"] = ["AM", "PM"]

        self.sim_body.grid(column=0, row=0, sticky=(N,W,E,S))

        self.noaa_section_label.grid(column=0, row=0, sticky=(W,E), pady=5, columnspan=2)
        
        # date placement
        self.date_label.grid(column=0, row=1, sticky=(W,E), padx=5)
        self.dmonth_input.grid(column=1, row=1, sticky=(W,E))
        self.slash1_label.grid(column=2, row=1, sticky=(W,E))
        self.dday_input.grid(column=3, row=1, sticky=(W,E))
        self.slash2_label.grid(column=4, row=1, sticky=(W,E))
        self.dyear_input.grid(column=5, row=1, sticky=(W,E))

        # time placement
        self.time_in_label.grid(column=6, row=1, sticky=(W,E), padx=5)
        self.hour_input.grid(column=7, row=1, sticky=(W,E))
        self.minute_input.grid(column=8, row=1, sticky=(W,E))
        self.ampm_input.grid(column=9, row=1, sticky=(W,E))
        self.confirm_btn.grid(column=10, row=1, sticky=(W,E), padx=5)

        # load placement
        self.file_section_label.grid(column=0, row=2, sticky=(W,E), pady=5, columnspan=6)
        self.load_storm_btn.grid(column=0, row=3, sticky=(W), columnspan=2)

        # cancel placement
        self.cancel_section_label.grid(column=0, row=4, sticky=(W,E), pady=5, columnspan=6)
        self.cancel_storm_btn.grid(column=0, row=5, sticky=(W), columnspan=2)

    def switch_sim_menu_to_loading_view(self):
        self.sim_menu.protocol("WM_DELETE_WINDOW", self.quit_sim_loading)

        self.sim_body.destroy()

        # initialize loading widgets
        self.loading_frame = ttk.Frame(self.sim_menu, padding="3 3 12 12")
        self.loading_header = ttk.Label(self.loading_frame, text="Preparing Simulation:")
        self.loading_progress = ttk.Progressbar(self.loading_frame, orient=tk.HORIZONTAL, length=100, mode="determinate")
        self.loading_text = ttk.Label(self.loading_frame, text="Retrieving Storm Data from NOAA")
        self.loading_cancel_btn = ttk.Button(self.loading_frame, text="Cancel", command=self.cancel_simulation_calculations)

        # place loading widgets
        self.loading_frame.grid(column=0, row=0, sticky=(N,W,E,S), columnspan=15)
        self.loading_header.grid(column=0, row=0, columnspan=15)
        self.loading_progress.grid(column=0, row=1, columnspan=15)
        self.loading_text.grid(column=0, row=2, columnspan=15)
        self.loading_cancel_btn.grid(column=0, row=3, columnspan=15)

    def destroy_loading_view(self):
        """ This method destroys the simulation loading view
        """
        self.loading_frame.destroy()

    def close_sim_config(self):
        self.sim_menu.destroy()

    def create_sub_view(self, sub_nums):
        """ This method creates the substation view
            @param: sub_nums: The substation ids to display in the view
        """
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
            sub_name = self.substation_data[sub_num]["name"]
            sub_label_text = "Substation " + (sub_name if not(sub_name == "") else str(sub_num)) + ":"
            sub_label = ttk.Label(self.sub_frame, text=sub_label_text)
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
                bus_name = self.bus_data[bus_num]["name"]
                bus_btn_text = "Bus " + (bus_name if not(bus_name == "") else str(bus_num))
                bus_btn = ttk.Button(bus_btn_frame, text=bus_btn_text, command=self.bus_btn_click(sub_nums, bus_num))
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
        """ This method destroys the substation view
        """
        self.sub_frame.destroy()
        self.sub_view_active = False

    def create_bus_view(self, sub_nums, bus_num):
        """ This method creates the bus view
            @param: sub_nums: The substation ids from substation view for going back
            @param: bus_num: The bus id for the bus that will be displayed
        """
        # get branches
        branches = self.get_branches_for_bus(bus_num)
        
        # get bus on other end of each branch
        to_buses = []
        for branch in branches:
            if(branch[0] != bus_num):
                to_buses.append(branch[0])
            else:
                to_buses.append(branch[1])

        # create bus frame
        self.bus_frame = ttk.Frame(self.body)
        self.bus_frame.grid(column=0, row=2, sticky=(N,W), columnspan=15)

        # create bus label
        bus_name = self.bus_data[bus_num]["name"]
        bus_label_text = bus_name if not(bus_name == "") else str(bus_num)
        self.bus_label = ttk.Label(self.bus_frame, text="Bus " + bus_label_text + ":")
        self.bus_label.grid(column=0, row=1, sticky=(N,W), padx=4, pady=8)

        self.branch_display_vals = {}
        current_column = 0
        row_base = 2
        for i in range(len(branches)):
            # go to a new row after a given number of branches and reset column
            current_row = row_base + (5 * (i // self.branches_per_row))
            if((i % self.branches_per_row) == 0):
                current_column = 0

            # get bus label
            bus_name = self.bus_data[to_buses[i]]["name"]
            bus_label_text = bus_name if not(bus_name == "") else str(to_buses[i])

            # get sub label
            sub_num = self.bus_data[to_buses[i]]["sub_num"]
            sub_name = self.substation_data[sub_num]["name"]
            sub_label_text = sub_name if not(sub_name == "") else str(sub_num)

            # create branch label
            branch_label = ttk.Label(self.bus_frame, text="To Bus " + bus_label_text + " at Sub " + sub_label_text + ":")
            branch_label.grid(column=current_column, row=current_row, sticky=(N,W), padx=4)
            self.branch_display_vals[branches[i]] = {"branch_label":branch_label}
            current_row += 1

            # TODO: Load initial values for these labels from state to handle simulation pausing
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
        """ This method destroys the bus view
        """
        self.bus_frame.destroy()
        self.bus_view_active = False
        self.back_to_sub_btn.destroy()

    ##########################
    # File Loading Functions #
    ##########################

    # - These functions are for loading state from files into the application

    def load_file(self, *args):
        """ This method loads a grid file in aux format (legacy variable names, older file headers) 
            chosen by the user into state
        """
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

                # get substation data
                # TODO: handle missing latitude or longitude data
                # TODO: substation grounding resistance
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
                # TODO: transformer type and data for W1, W2
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

                # save grid data in database
                core_event = self.core.send_request(self.core.save_grid_data, {
                    "grid_name" : self.grid_name, "substation_data" : self.substation_data,
                    "bus_data" : self.bus_data, "branch_data" : self.branch_data
                })

                core_event.wait()

                self.redraw_grid()
                self.title("Space Weather Analysis Tool: " + self.grid_name)

                # enable simulating
                self.start_btn.state(["!disabled"])
        
        # ignore cancel hit on filedialog
        except AttributeError:
            None
    
    ###########################
    # General Input Functions #
    ###########################

    # - These functions handle general UI inputs

    def set_days_for_month(self, *args):
        """ This method ensures that the days combobox input has the correct amount of days after a month has been chosen
        """
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
        """ This method ensures that the days combobox input has the correct amount of days after a year has been chosen
        """
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
        """ This method exits the substation view and loads the grid view
        """
        self.destroy_sub_view()
        self.create_grid_canvas()
        self.redraw_grid()

    def bus_btn_click(self, sub_nums, bus_num):
        """ This method creates a method that when called will exit the substation view and load
            the bus view for the given bus
            @param: sub_nums: The substation ids for the substation view that will be exited
            @param: bus_num: The bus id for the bus that will be displayed in the bus view
            return: event_handler: The resulting method
        """
        def event_handler(*args):
            self.destroy_sub_view()
            self.create_bus_view(sub_nums, bus_num)

        return event_handler
    
    def back_to_sub(self, sub_nums):
        """ This method creates a method that when called will exit the bus view and
            load the substation view for the given substations
            @param: sub_nums: The substation ids for the substation view that will be loaded
            return: event_handler: The resulting method
        """
        def event_handler(*args):
            self.destroy_bus_view()
            self.create_sub_view(sub_nums)

        return event_handler

    def test_fn(self, *args):
        """ This method is for UI testing
        """
        print("Button pressed.")

    ###############################
    # Grid Canvas Input Functions #
    ###############################

    # - These functions handle user inputs that are specific to the grid canvas

    def execute_zoom(self, *args):
        """ This method redraws the grid view when a new zoom value has been set
        """
        # update grid_canvas_size
        self.grid_canvas_size = int(self.zoom_val.get()[:-1]) * 0.01 * 10000

        # carry out change
        if(self.grid_canvas_active):
            self.redraw_grid()

    def grid_canvas_sub_click(self, sub_num):
        """ This method creates a new method that will exit the grid view and
            load the substation view for a given substation and any substations
            overlapped by it
            @param: sub_num: The substation id for the substation that the substation view will be loaded for
            return: event_handler: The resulting method
        """
        def event_handler(event):
            # get any subs under the clicked sub and pass them all to sub view
            subs_in_click = [sub_num]
            try:
                for sub in self.substations_overlapped_by_sub[sub_num]:
                    subs_in_click.append(sub)
            except KeyError:
                None

            self.destroy_grid_canvas()
            self.create_sub_view(subs_in_click)

        return event_handler

    ##############################
    # Simulation Input Functions #
    ##############################

    # - These functions handle user inputs that are specific to solar storm simulation

    def configure_sim(self, *args):
        """ This method creates the simulation configuration window
        """
        self.sim_menu = tk.Toplevel(self)

        self.sim_menu.title("Simulation Configuration")

        self.sim_body = ttk.Frame(self.sim_menu, padding="3 3 12 12")

        self.create_sim_menu_body()

        # grey out main window inputs
        self.load_btn.state(["disabled"])
        self.start_btn.state(["disabled"])
        self.zoom_input.state(["disabled"])

        # lock off main window
        self.sim_menu.transient(self)
        self.sim_menu.grab_set()
        self.wait_window(self.sim_menu)

    def cancel_sim_config(self, *args):
        # unlock inputs
        self.load_btn.state(["!disabled"])
        self.start_btn.state(["!disabled"])
        self.zoom_input.state(["!disabled"])

        # close window
        self.sim_menu.destroy()

    def play_sim_noaa(self, *args):
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
        local_timezone = datetime.now().astimezone().tzinfo
        set_start_time = datetime(year, month, day, hour, minute).replace(tzinfo=local_timezone)

        self.start_time = set_start_time
        self.sim_time = set_start_time

        # initialize simulation pause event
        self.sim_pause = Event()

        # start simulation loop
        self.sim_running = True
        self.sim_thread = Thread(target=self.simulation_loop)
        self.sim_thread.start()

    def play_sim_file(self, *args):
        # ask for storm file
        try:
            filetypes = (("storm data csv files", "*.csv"),)
            storm_file = fdialog.askopenfilename(filetypes=filetypes)
        # stop on cancel hit on filedialog
        except AttributeError:
            return

        # initialize simulation pause event
        self.sim_pause = Event()

        # start simulation loop
        self.sim_running = True
        self.sim_thread = Thread(target=self.simulation_loop, args=(storm_file,))
        self.sim_thread.start()

    def quit_sim_loading(self, *args):
        # kill simulation loop
        self.sim_running = False
        self.sim_thread.join(0.5)

        self.cancel_sim_config()

    def stop_sim(self, *args):
        # kill simulation loop
        self.sim_running = False
        self.sim_thread.join(0.5)

        self.switch_to_sim_not_active_ui()
        self.destroy_grid_canvas()
        self.create_grid_canvas()
        self.redraw_grid()

    def pause_sim(self, *args):
        self.sim_pause.set()

    def resume_sim(self, *args):
        self.sim_pause.clear()

    def cancel_simulation_calculations(self, *args):
        """ This method cancels currently running simulation
            calculations
        """
        self.sim_cancelled = True

    ########################
    # Simulation Functions #
    ########################

    # https://pythonguides.com/python-tkinter-colors/#Python_Tkinter_Colors_RGB
    def rgb_hack(self, rgb):
        """ This method converts a tuple of rgb integer values into a string
            that Tkinter will accept, as Tkinter doesn't accept rgb by default
            @param: rgb: A tuple of integers in the form (r, g, b)
            return: Tkinter color string
        """
        return "#%02x%02x%02x" % rgb  

    def simulation_loop(self, storm_file = None):
        """ This method is a loop that runs in a thread and carries out simulation playback.
            The simulation runs at a scale of roughly 1 second per minute and loops after
            it reaches an hour from start time.
        """
        self.switch_sim_menu_to_loading_view()
        loading_sem = Semaphore(value=0)
        terminate_event = Event()
        retval = []
        core_event = None
        if(storm_file == None):
            core_event = self.core.send_request(self.core.calculate_simulation_noaa, {
                "grid_name" : self.grid_name, "start_time" : self.start_time,
                "progress_sem" : loading_sem, "terminate_event" : terminate_event
            }, retval)
        else:
            core_event = self.core.send_request(self.core.calculate_simulation_file, {
                "grid_name" : self.grid_name, "storm_file" : storm_file,
                "progress_sem" : loading_sem, "terminate_event" : terminate_event
            }, retval)
        for i in range(1,5):
            if(i == 2):
                self.loading_text["text"] = "Calculating Electric Field"
            elif(i == 3):
                self.loading_text["text"] = "Calculating GICS"
            elif(i == 4):
                self.loading_text["text"] = "Calculating TTCs"
            while not loading_sem.acquire(blocking=False):
                if self.sim_cancelled:
                    # calculations canceled
                    self.sim_cancelled = False
                    self.core.log_to_file("GUI", "Attempting to terminate calculations")
                    terminate_event.set()
                    core_event.wait()

                    # switch views
                    self.destroy_loading_view()
                    self.create_sim_menu_body()
                    self.sim_running = False
                    return
                if not self.sim_running:
                    # terminate calculations and return to grid view
                    self.core.log_to_file("GUI", "Attempting to terminate calculations")
                    terminate_event.set()
                    core_event.wait()
                    return
                if core_event.is_set():
                    # calculations failed
                    messagebox.showinfo("Simulation Error", retval[0])

                    # switch views
                    self.destroy_loading_view()
                    self.create_sim_menu_body()
                    self.sim_running = False
                    return
            self.loading_progress["value"] = i * 25
        self.loading_cancel_btn.state(["disabled"])
        self.loading_text["text"] = "Saving to Database"
        core_event.wait()
        messagebox.showinfo("Loaded!", "Simulation has been loaded!")
        self.switch_to_sim_active_ui()
        self.close_sim_config()

        while(self.sim_running):
            if(self.sim_pause.is_set()):
                continue
            
            # update time label
            self.time_label["text"] = "Time In Simulation: " + self.sim_time.strftime("%m/%d/%Y, %H:%M:%S")

            # load data for minute
            retval = []
            core_event = self.core.send_request(self.core.get_data_for_time, {
                "grid_name" : self.grid_name, "timepoint" : self.sim_time
            }, retval)
            core_event.wait()
            time_data = retval[0]

            gics = []
            for point in time_data:
                gics.append(point[5])

            max_gic = max(gics)
            min_gic = min(gics)

            if(self.grid_canvas_active):
                # update all branch colors
                for point in time_data:
                    try:
                        branch_ids = (point[0], point[1], point[2])
                        branch = self.branch_data[branch_ids]
                        try:
                            line_id = branch["line_id"]
                            gic = point[5]

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
                        branch_ids = (point[0], point[1], point[2])
                        if(branch_ids in branches):
                            labels = self.branch_display_vals[branch_ids]
                            labels["GIC_label"]["text"] = "GIC: " + str(point[5])
                            if(self.branch_data[branch_ids]["has_trans"]):
                                labels["VLEVEL_label"]["text"] = "VLEVEL: " + str(point[6])
                                labels["TTC_label"]["text"] = "TTC: " + str(point[7])
                except:
                    continue

            # update sim time
            sleep(1)
            self.sim_time += timedelta(minutes=1)
            # TODO: Roll over at sim end time rather than 1 hour constant
            if(self.sim_time >= (self.start_time + timedelta(minutes=60))):
                self.sim_time = self.start_time

    ########################
    # Conversion Functions #
    ########################

    # - These functions handle coordinate conversions

    # using https://stackoverflow.com/a/2450158
    # modified to work better for canvas purposes
    def long_to_x(self, long):
        """ This method does the conversion from longitude coordinates
            to UI grid canvas coordinates on the x axis
            @param: long: A longitude coordinate
            return: A corresponding x coordinate on the grid canvas
        """
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
        """ This method does the conversion from latitude coordinates
            to UI grid canvas coordinates on the y axis
            @param: lat: A latitude coordinate
            return: A corresponding y coordinate on the grid canvas
        """
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

    # - These functions assist with retrieving data for grid elements

    def get_branches_btwn_subs(self):
        """ This method finds all the branches in the grid that run between substations and returns
            the substations and buses connected in each branch
            return: branches_btwn_subs: All the branches that run between substations
        """
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
        """ This method gets all the bus ids for a given substation
            @param: sub_num: The substation for which to get ids
            return: bus_nums: The bus ids for the given substation
        """
        bus_nums = []
        for bus_num in self.bus_data:
            if(self.bus_data[bus_num]["sub_num"] == sub_num):
                bus_nums.append(bus_num)

        return bus_nums
    
    def get_branches_for_bus(self, bus_num):
        """ This method gets all the branches for a given bus
            @param: bus_num: The bus for which to get branches
            return: branch_tuples: List of tuples that represent the branches attached to the given bus
        """
        branch_tuples = []
        for branch_tuple in self.branch_data:
            if(branch_tuple[0] == bus_num or branch_tuple[1] == bus_num):
                branch_tuples.append(branch_tuple)

        return branch_tuples
    
    ##########################
    # Grid Drawing Functions #
    ##########################

    def place_sub(self, long, lat, sub_num, sub_name):
        # convert lat/long to x/y
        x_val = self.long_to_x(long)
        y_val = self.lat_to_y(lat)

        # add pixels to grid mapping
        self.check_and_update_substation_pixels(sub_num, x_val, y_val, append_overlaps=True)

        # place sub rectangle and bind events
        rect_id = self.grid_canvas.create_rectangle((x_val, y_val, x_val + self.sq_size, y_val + self.sq_size), fill="#00ff40", tags=('palette', 'palettered'))
        self.grid_canvas.tag_bind(rect_id, "<Button-1>", self.grid_canvas_sub_click(sub_num))
        
        # place sub text
        self.grid_canvas.create_text(x_val + (self.sq_size / 2), y_val + (self.sq_size * 3), text=sub_name if not(sub_name == "") else 'S' + str(sub_num), 
        anchor='center', font=("Helvetica", 8), fill='black')

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
            self.place_sub(sub_to_place["long"], sub_to_place["lat"], i, sub_to_place["name"])

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
