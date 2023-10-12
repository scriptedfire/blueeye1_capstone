import sqlite3
import datetime
from datetime import timedelta, timezone
from threading import Thread, Semaphore, Event
from random import randrange
from time import time
import pandas as pd
from time import sleep
from multiprocessing import Process, Queue
from GUI import App
from NOAASolarStormDataMiner import data_scraper
from ElectricFieldPredictor import ElectricFieldCalculator
import gic_solver as gic
from TransformerThermalCapacity import transformer_thermal_capacity
from grid_approximations import estimate_winding_impedance, get_grounding_resistance

class Core():
    # Variables for GUI subsystem
    app = None
    app_thread = None
    requests_sem = None
    requests_queue = []

    # Variables for logging
    logging_thread = None
    logging_sem = None
    logging_queue = []

    def __init__(self):
        # initialize in memory and on file db
        self.db_conn = sqlite3.connect(":memory:")
        self.backup_db_conn = sqlite3.connect("state.db")

        # load on file db into memory
        self.backup_db_conn.backup(self.db_conn)

        # initialize semaphores
        self.requests_sem = Semaphore(0)
        self.logging_sem = Semaphore(0)

        self.log_to_file("Core", "Core Initialized")

    #####################
    # Startup Functions #
    #####################

    # - These functions facilitate the startup of the Application
    # - All of them are helpers except for run_core, which must be called in __main__ only

    def start_request_loop(self):
        """ This method starts the request loop, allowing Core to process requests from requests_queue
        """
        while(True):
            self.requests_sem.acquire()

            # fulfill request
            request = self.requests_queue.pop(0)
            retval = None
            #try:
            retval = request["func"](request["params"])
            #except Exception as e:
            #    self.log_to_file("Core", "Requested function " + request["func"].__name__ + " exception: " + str(e))
            #   retval = str(e)
            request["retval"].append(retval)
            request["event"].set()

    def start_logging_loop(self):
        """ This method starts the logging loop, which takes strings from a queue
            and writes them to a file. It is intended to be called on its own thread.
        """
        dnow = datetime.datetime.now()
        with open("log_ " + dnow.strftime("%m%d%Y_%H%M%S") + ".txt", "a+") as logfile:
            while(True):
                self.logging_sem.acquire()

                # log message
                msg = self.logging_queue.pop(0)
                if(msg == None):
                    # stop logging loop
                    return
                logfile.write(msg + "\n")

    def start_logging_thread(self):
        """ This method starts logging on a new thread
        """
        self.logging_thread = Thread(target=self.start_logging_loop)
        self.logging_thread.start()

    def start_gui(self):
        """ This method is a helper for starting the GUI in a seperate thread.
            It must only be called in a seperate thread from Core.
        """
        self.app = App(self)
        self.app.mainloop()

    def start_app_thread(self):
        """ This method starts GUI on a new thread
        """
        self.app_thread = Thread(target=self.start_gui)
        self.app_thread.start()

    def run_core(self):
        """ This method starts the application as a whole
        """
        self.start_logging_thread()
        self.log_to_file("Core", "Logging Started!")
        self.start_app_thread()
        self.start_request_loop()

    ###########################
    # Internal Data Functions #
    ###########################

    # - These functions are helpers for managing the database
    # - They should only be called within the Core class

    def initialize_tables(self):
        """ This method initializes the tables for the Core database
        """
        transaction = self.db_conn.cursor()

        transaction.execute("""CREATE TABLE IF NOT EXISTS Grid (
        GRID_NAME text PRIMARY KEY
        )""")

        transaction.execute("""CREATE TABLE IF NOT EXISTS Substation (
        SUB_NUM integer NOT NULL,
        GRID_NAME text NOT NULL,
        SUB_LATITUDE real NOT NULL,
        SUB_LONGITUDE real NOT NULL,
        PRIMARY KEY (SUB_NUM, GRID_NAME),
        FOREIGN KEY (GRID_NAME) REFERENCES Grid (GRID_NAME)
        )""")

        transaction.execute("""CREATE TABLE IF NOT EXISTS Bus (
        BUS_NUM integer NOT NULL,
        SUB_NUM integer NOT NULL,
        GRID_NAME text NOT NULL,
        PRIMARY KEY (BUS_NUM, GRID_NAME),
        FOREIGN KEY (SUB_NUM, GRID_NAME) REFERENCES Substation (SUB_NUM, GRID_NAME)
        )""")

        transaction.execute("""CREATE TABLE IF NOT EXISTS Branch (
        FROM_BUS integer NOT NULL,
        TO_BUS integer NOT NULL,
        CIRCUIT integer NOT NULL,
        GRID_NAME text NOT NULL,
        HAS_TRANSFORMER boolean NOT NULL,
        PRIMARY KEY (FROM_BUS, TO_BUS, CIRCUIT, GRID_NAME),
        FOREIGN KEY (FROM_BUS, GRID_NAME) REFERENCES Bus (BUS_NUM, GRID_NAME),
        FOREIGN KEY (TO_BUS, GRID_NAME) REFERENCES Bus (BUS_NUM, GRID_NAME)
        )""")

        transaction.execute("""CREATE TABLE IF NOT EXISTS Datapoint (
        FROM_BUS integer NOT NULL,
        TO_BUS integer NOT NULL,
        CIRCUIT integer NOT NULL,
        GRID_NAME text NOT NULL,
        DPOINT_TIME text NOT NULL,
        DPOINT_GIC real NOT NULL,
        DPOINT_VLEVEL real,
        DPOINT_TTC real,
        PRIMARY KEY (DPOINT_TIME, FROM_BUS, TO_BUS, CIRCUIT, GRID_NAME),
        FOREIGN KEY (FROM_BUS, TO_BUS, CIRCUIT, GRID_NAME) REFERENCES Branch (FROM_BUS, TO_BUS, CIRCUIT, GRID_NAME)
        )""")

        self.db_conn.commit()

        transaction.close()

    def add_grid_if_not_exists(self, grid_name):
        """ This method adds a new grid entity to the database if one doesn't exist already
            @param: grid_name: The name of a grid to insert if it doesn't exist already
            return: lastrowid: Row id of the grid inserted, or None if grid already exists
        """
        transaction = self.db_conn.cursor()

        # get grid entity for name to check existence
        transaction.execute("""SELECT * FROM Grid WHERE GRID_NAME=? LIMIT 1""",(grid_name,))

        # don't do anything if already exists, return None since nothing inserted
        if(len(transaction.fetchall()) != 0):
            transaction.close()
            return None

        transaction.execute("""INSERT INTO Grid(GRID_NAME)
        VALUES(?)""", [grid_name])

        lastrowid = transaction.lastrowid

        self.db_conn.commit()

        transaction.close()

        return lastrowid

    def add_substation(self, grid_name, sub_num, sub_latitude, sub_longitude):
        """ This method adds a new substation entity to the database
            @param: grid_name: The name of the grid the substation is in
            @param: sub_num: The substation's number within that grid
            @param: sub_latitude: The latitude of the substation's location
            @param: sub_longitude: The longitude of the substation's location
            return: lastrowid: Row id of the substation inserted
        """
        transaction = self.db_conn.cursor()

        # load entity into db
        transaction.execute("""INSERT INTO Substation(SUB_NUM, GRID_NAME, SUB_LATITUDE, SUB_LONGITUDE)
        VALUES(?,?,?,?)""", [sub_num, grid_name, sub_latitude, sub_longitude])

        lastrowid = transaction.lastrowid

        self.db_conn.commit()

        transaction.close()

        return lastrowid

    def add_bus(self, grid_name, sub_num, bus_num):
        """ This method adds a new bus entity to the database
            @param: grid_name: The name of the grid the bus is in
            @param: sub_num: The bus's substation's number within that grid
            @param: bus_num: The bus's number within that grid
        """
        transaction = self.db_conn.cursor()

        # load entity into db
        transaction.execute("""INSERT INTO Bus(BUS_NUM, SUB_NUM, GRID_NAME)
        VALUES(?,?,?)""", [bus_num, sub_num, grid_name])

        self.db_conn.commit()

        transaction.close()

    def add_branch_and_transformer(self, grid_name, from_bus, to_bus, circuit, has_trans):
        """ This method adds a new branch entity to the database
            @param: grid_name: The name of the grid the branch is in
            @param: from_bus: The bus on the from side's number
            @param: to_bus: The bus on the to side's number
            @param: circuit: The circuit number of the branch
            @param: has_trans: Boolean representing whether or not the branch is a transformer
        """
        transaction = self.db_conn.cursor()

        # load branch entity into db
        transaction.execute("""INSERT INTO Branch(FROM_BUS, TO_BUS, CIRCUIT, GRID_NAME, HAS_TRANSFORMER)
        VALUES(?,?,?,?,?)""", [from_bus, to_bus, circuit, grid_name, has_trans])

        self.db_conn.commit()

        transaction.close()
    
    def save_to_file(self):
        """ This method backs up the in-memory database to an on-file database
        """
        self.db_conn.backup(self.backup_db_conn)

    #########################
    # Requestable Functions #
    #########################

    # - These functions allow other threads to call functions on the Core thread via making requests through send_request
    # - The params are sent as a dictionary with the function through send_request
    # - See send_request in Misc. Functions for more information

    def save_grid_data(self, params):
        """ This method saves grid data to the database
            @param: grid_name: The name of the grid
            @param: substation_data: The substation data for the grid in the form of a nested dictionary.
            The keys for the dictionary are substation numbers and the values are dictionaries containing the data
            for each substation.
            @param: bus_data: The bus data for the grid in the form of a nested dictionary.
            Like substation_data the keys are bus numbers and the values are dictionaries containing data.
            @param: branch_data: The branch data for the grid in the form of a nested dictionary.
            The keys are tuples of (from_bus, to_bus, circuit) and the values are dictionaries containing data.
        """
        grid_name = params["grid_name"]
        substation_data = params["substation_data"]
        bus_data = params["bus_data"]
        branch_data = params["branch_data"]

        start = time()

        self.initialize_tables()

        # ignore if grid already exists
        if(self.add_grid_if_not_exists(grid_name) == None):
            self.log_to_file("Core", "Grid Already Exists")
            return
        
        self.log_to_file("Core", "Grid Added")
        
        for sub_num in substation_data:
            sub = substation_data[sub_num]
            self.add_substation(grid_name, sub_num, sub["lat"], sub["long"])

        self.log_to_file("Core", "Substations Added")

        for bus_num in bus_data:
            bus = bus_data[bus_num]
            self.add_bus(grid_name, bus["sub_num"], bus_num)

        self.log_to_file("Core", "Buses Added")

        for branch in branch_data:
            from_bus_num = branch[0]
            to_bus_num = branch[1]
            circuit_num = branch[2]
            self.add_branch_and_transformer(grid_name, from_bus_num, to_bus_num, circuit_num, branch_data[branch]["has_trans"])

        self.log_to_file("Core", "Branches Added")

        self.save_to_file()

        self.log_to_file("Core", "Loading Grid Took: " + str(time() - start) + " seconds")

    def get_data_for_time(self, params):
        """ This method requests all datapoints for a given datetime
            @param: grid_name: The name of the grid for which datapoints are being loaded
            @param: timepoint: The time for which to load datapoints
            return: data: A list containing all the datapoints for the given time
        """
        grid_name = params["grid_name"]
        timepoint = params["timepoint"]
        utc_timepoint = local_to_utc(timepoint)

        transaction = self.db_conn.cursor()

        transaction.execute("""SELECT * FROM Datapoint WHERE GRID_NAME=? AND DPOINT_TIME=?""", (grid_name, utc_timepoint.strftime("%m/%d/%Y, %H:%M:%S")))

        data = transaction.fetchall()

        transaction.close()

        return data
    
    def calculate_simulation_noaa(self, params):
        """ This method calculates an hour of datapoints for simulation display
            @param: grid_name: The name of the grid for which to calculate datapoints
            @param: start_time: The start time (in user's local timezone) 
            to calculate an hour of datapoints from
            @param: progress_sem: The semaphore is released four times for the
            four stages in this method and can be used to keep track of calculation progress
            @param: terminate_event: Setting this event forces this method to terminate any
            ongoing child process and return
            return: True if succeeded, or an error message if failed
        """
        #try:
        grid_name = params["grid_name"]
        start_time = params["start_time"]
        progress_sem = params["progress_sem"]
        terminate_event = params["terminate_event"]

        # TODO: skip all stages if data for given time range is in the database

        # convert start time from local to utc
        local_timezone = datetime.datetime.now().astimezone().tzinfo
        start_time_utc = start_time.replace(tzinfo=local_timezone).astimezone(timezone.utc)

        # log start time
        self.log_to_file("Core", "Preparing simulation for Local Time: " + start_time.strftime("%m/%d/%Y, %H:%M:%S") + 
        ", UTC: " + start_time_utc.strftime("%m/%d/%Y, %H:%M:%S"))

        # get space weather data from NOAA
        results = self.execute_process(wrap_data_scraper, {
            "start_date" : start_time, "file_path" : "."
        }, terminate_event, True)

        # check for termination
        if terminate_event.is_set():
            return "Termination event set"

        # extract data and return error if any
        storm_data = None
        data_invalid = None
        if(len(results["retval"]) == 2):
            storm_data = results["retval"][0]
            data_invalid = results["retval"][1]
        else:
            self.log_to_file("Core", "data_scraper returned an error: " + results["retval"])
            return "data_scraper returned an error: " + results["retval"]

        # return if data is flagged invalid
        if data_invalid:
            return "Invalid data received from NOAA Storm Dataminer"

        # extract time
        time_data = storm_data["time"].to_numpy(dtype=float)

        # check that the range is greater than one hour
        start_time = datetime.datetime.fromtimestamp(time_data[0], tz=timezone.utc)
        end_time = datetime.datetime.fromtimestamp(time_data[-1], tz=timezone.utc)
        if(end_time < (start_time + timedelta(minutes=60))):
            return "Less than one hour of data received from NOAA Storm Dataminer"

        # set times for GUI
        self.app.start_time = utc_to_local(start_time)
        self.app.sim_time = utc_to_local(start_time)

        # notify NOAA stage complete
        progress_sem.release()

        return self.calculate_simulation(grid_name, progress_sem, terminate_event, storm_data)
        #except Exception as e:
        #    self.log_to_file("Core", "Exception encountered in calculate_simulation_noaa: " + str(e))
        #   return str(e)

    def calculate_simulation_file(self, params):
        #try:
        grid_name = params["grid_name"]
        storm_file = params["storm_file"]
        progress_sem = params["progress_sem"]
        terminate_event = params["terminate_event"]

        # TODO: skip all stages if data for given time range is in the database

        # Skip NOAA progress stage
        progress_sem.release()

        storm_data = pd.read_csv(storm_file)

        # validate file shape
        if not (storm_data.columns.values.tolist() == ['Unnamed: 0', 'time', 'speed', 'density', 'Vx', 'Vy', 'Vz', 'Bx', 'By', 'Bz', 'dst']):
            return "File formatted incorrectly"

        # extract time
        time_data = storm_data["time"].to_numpy(dtype=float)

        # check that the range is greater than one hour
        start_time = datetime.datetime.fromtimestamp(time_data[0], tz=timezone.utc)
        end_time = datetime.datetime.fromtimestamp(time_data[-1], tz=timezone.utc)
        if(end_time < (start_time + timedelta(minutes=60))):
            return "File contains less than one hour of data"

        # set times for GUI
        self.app.start_time = utc_to_local(start_time)
        self.app.sim_time = utc_to_local(start_time)

        return self.calculate_simulation(grid_name, progress_sem, terminate_event, storm_data)
        #except Exception as e:
        #    self.log_to_file("Core", "Exception encountered in calculate_simulation_file: " + str(e))
        #    return str(e)

    def fabricate_hour_of_data(self, params):
        """ This method is a diagnostic tool for testing the GUI's ability to load and play a simulation
            @param: grid_name: The name of a grid for which to produce random simulation data
            @param: start_time: The start time from which to produce an hour of random simulation data
        """
        grid_name = params["grid_name"]
        start_time = params["start_time"]

        transaction = self.db_conn.cursor()

        # get buses
        transaction.execute("""SELECT * FROM Branch WHERE GRID_NAME=?""", (grid_name,))
        branches = transaction.fetchall()

        # generate random data for times
        for i in range(60):
            dpoint_time = start_time.strftime("%m/%d/%Y, %H:%M:%S")
            transaction.execute("""SELECT * FROM Datapoint WHERE GRID_NAME=? AND DPOINT_TIME=? LIMIT 1""", (grid_name, dpoint_time))

            if(len(transaction.fetchall()) != 0):
                start_time += timedelta(minutes=1)
                continue

            for branch in branches:
                from_bus = branch[0]
                to_bus = branch[1]
                circuit = branch[2]

                has_trans = branch[4]
                gic = randrange(0, 999)
                vlevel = None
                ttc = None

                if(has_trans != 0):
                    vlevel = randrange(0, 999)
                    ttc = randrange(0, 999)

                transaction.execute("""INSERT INTO Datapoint(FROM_BUS, TO_BUS, CIRCUIT, GRID_NAME,
                DPOINT_TIME, DPOINT_GIC, DPOINT_VLEVEL, DPOINT_TTC) VALUES(?,?,?,?,?,?,?,?)""",
                [from_bus, to_bus, circuit, grid_name, dpoint_time, gic, vlevel, ttc])

                self.db_conn.commit()

            start_time += timedelta(minutes=1)

        transaction.close()

        self.save_to_file()

    def close_application(self, *args):
        """ This method closes the application. It is intended to be called from the closing method of GUI.
        """
        self.logging_queue.append(None)
        self.logging_sem.release()
        self.logging_thread.join(0.5)
        exit()

    ###################
    # Misc. Functions #
    ###################

    def calculate_simulation(self, grid_name, progress_sem, terminate_event, storm_data):
        # Calculate E field values
        resistivity_data = pd.read_csv('Application/Quebec_1D_model.csv')
        E_field = None
        results = self.execute_process(wrap_ElectricFieldCalculator, {
            "resistivity_data" : resistivity_data, "solar_storm" : storm_data,
            "min_longitude" : self.app.min_long, "max_longitude" : self.app.max_long,
            "min_latitude" : self.app.min_lat, "max_latitude" : self.app.max_lat
        }, terminate_event, True)

        # check for termination
        if terminate_event.is_set():
            return "Termination event set"

        # extract data and return error if any
        E_field = results["retval"]
        if isinstance(E_field, str):
            self.log_to_file("Core", "ElectricFieldCalculator returned an error: " + E_field)
            return "ElectricFieldCalculator returned an error: " + E_field

        print(E_field)
        print(E_field.reset_index()[::4])

        E_field = E_field.reset_index()
        times = []
        Ex = []
        Ey = []
        for i in range(len(E_field)):
            if((i % 4) == 0):
                E_row = E_field.iloc[i]
                #print(E_row)
                #print(E_row["Ex"])
                #print(E_row["Ey"])
                times.append(E_row["time"])
                Ex.append(E_row["Ex"])
                Ey.append(E_row["Ey"])
        
        E_field_corner = {
            "time" : times,
            "Ex" : Ex,
            "Ey" : Ey
        }

        E_field_corner = pd.DataFrame(E_field_corner)
        print(E_field_corner)

        # notify E field stage complete
        progress_sem.release()

        # TODO: GIC Solver
        #self.execute_process(sleep, 5, terminate_event)
        gic_df = wrap_gic_solver({"substation_data" : self.app.substation_data, "bus_data" : self.app.bus_data, "branch_data" : self.app.branch_data,
        "E_field" : E_field_corner})
        print(gic_df)
        print(gic_df.shape)
        print(len(self.app.branch_data))

        for branch in self.app.branch_data:
            print(branch)
            self.app.branch_data[branch]["time"] = gic_df["time"]
            if self.app.branch_data[branch]["has_trans"]:
                self.app.branch_data[branch]["GICs"] = gic_df[str(branch) + self.app.branch_data[branch]["type"]]
            else:
                self.app.branch_data[branch]["GICs"] = gic_df[str(branch)]

        if terminate_event.is_set():
            return "Termination event set"

        progress_sem.release()

        # TODO: TTC
        #self.execute_process(sleep, 5, terminate_event)
        updated_branch_data = transformer_thermal_capacity(self.app.branch_data)
        print(updated_branch_data)

        if terminate_event.is_set():
            return "Termination event set"

        progress_sem.release()

        # Store to database
        self.fabricate_hour_of_data({"grid_name" : grid_name, "start_time" : local_to_utc(self.app.start_time)})

    def send_request(self, func, params = None, retval = []):
        """ This method creates a request and sends it down the request queue.
            It can be called from any thread.
            @param: func: The function to run, which must be one of the Requestable Functions
            @param: params: The parameters for the requested function as a dictionary
            @param: retval: This variable will be appended to with the return value of the requested function
            return: request_event: This event will be set when the requested function returns
        """
        request_event = Event()
        request = {"event" : request_event, "func" : func,
                   "params" : params, "retval" : retval}
        self.requests_queue.append(request)
        self.requests_sem.release()
        return request_event

    def log_to_file(self, source, msg):
        """ This method sends a log message down the logging queue.
            It can be called from any thread.
        """
        self.logging_queue.append("From " + source + ": " + msg)
        self.logging_sem.release()

    def execute_process(self, func, params, terminate_event, logging=False):
        """ This method runs a given function as a child process that can be cancelled through an event.
            It must only be called from the main thread due to multiprocessing requirements.
            @param: func: The function to run, which must have only one argument
            @param: params: The parameter(s) for the function to run, passed as the function's single argument
            @param: terminate_event: This method will terminate the child process and return if this
            event is set.
            @param: logging: Boolean for whether or not the function to run supports multiprocess logging
            (takes log_queue as a dictionary parameter and sends log messages down it)
            return: retval: None if the child process is terminated, or the return value from the function ran,
            or an error string if the function encountered an exception
        """
        if not __name__ == "__main__":
            raise "execute_process must only be called from the main thread"

        ret_queue = Queue()

        # initialize multiprocess logging queue if function supports it
        if logging:
            logging_queue = Queue()
            params["log_queue"] = logging_queue

        # start process
        p = Process(target=mp_function_wrapper, args=(ret_queue, func, params))
        p.start()
        self.log_to_file("Core", "Process " + func.__name__ + " started")

        # monitor process
        while ret_queue.empty():
            # pass on log messages if multiprocess logging is being used
            if logging:
                log_queue = params["log_queue"]
                if not log_queue.empty():
                    self.log_to_file(func.__name__, log_queue.get_nowait())

            # terminate process and return if terminate_event is set
            if terminate_event.is_set():
                p.terminate()
                p.join()
                self.log_to_file("Core", "Process " + func.__name__ + " manually terminated")
                return None

        # return process result
        retval = ret_queue.get()
        p.join()
        return retval

######################################
# Multiprocess Calculation Functions #
######################################

# - These functions are helpers for putting long-running calculations on other processes

def wrap_data_scraper(params):
    """ This method is equivalent to data_scraper except it takes its parameters as a dictionary
        rather than individually
    """
    start_date = params["start_date"]
    log_queue = params["log_queue"]
    file_path = params["file_path"]
    return data_scraper(start_date, log_queue, file_path)

def wrap_ElectricFieldCalculator(params):
    """ This method is equivalent to ElectricFieldCalculator except it takes its parameters as a dictionary
        rather than individually
    """
    resistivity_data = params["resistivity_data"]
    solar_storm = params["solar_storm"]
    min_longitude = params["min_longitude"]
    max_longitude = params["max_longitude"]
    min_latitude = params["min_latitude"]
    max_latitude = params["max_latitude"]
    log_queue = params["log_queue"]
    return ElectricFieldCalculator(resistivity_data, solar_storm, min_longitude, max_longitude, min_latitude, max_latitude, log_queue)

def wrap_gic_solver(params):
    substation_data = params["substation_data"]
    bus_data = params["bus_data"]
    branch_data = params["branch_data"]
    E_field = params["E_field"]
    line_list = gic.list_line_data(substation_data, bus_data, branch_data)
    line_length = gic.generate_line_length(line_list)
    IV_df = gic.input_voltage_calculation(line_length, E_field)
    EC_df = gic.equivalent_current_calc(line_length, IV_df)
    nodes = gic.generate_nodes_and_network(branch_data, bus_data, substation_data)
    nodal_index = gic.nodal_indexer(nodes)
    reverse_mapping = gic.reverse_map_nodes(nodes, nodal_index, branch_data)
    cond_mat = gic.cond_mat_generator(nodal_index, reverse_mapping)
    gic_df = gic.ic_mat_generator_gic_df(nodal_index, EC_df, reverse_mapping, cond_mat)
    return gic_df

def mp_function_wrapper(ret_queue, func, params):
    """ This method is a helper for execute_process and wraps functions for being called in a separate process
        @param: ret_queue: A multiprocessing queue to send the function's return value or exception string down
        @param: func: The function being wrapped
        @param: params: The function's parameter(s) as a single argument
    """
    try:
        retval = func(params)
        ret_queue.put({"success": True, "retval" : retval})
    except Exception as e:
        ret_queue.put({"success": False, "retval" : str(e)})

def local_to_utc(time_val):
        local_timezone = datetime.datetime.now().astimezone().tzinfo
        return time_val.replace(tzinfo=local_timezone).astimezone(timezone.utc)

def utc_to_local(time_val):
    local_timezone = datetime.datetime.now().astimezone().tzinfo
    return time_val.replace(tzinfo=timezone.utc).astimezone(local_timezone)

if __name__ == "__main__":
    core = Core()
    core.run_core()
