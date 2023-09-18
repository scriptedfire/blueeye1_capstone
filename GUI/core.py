import sqlite3
from datetime import datetime, timedelta
from threading import Thread, Semaphore, Event
from random import randrange
from time import time
from GUI import App

class Core():
    # Variables for GUI subsystem
    app = None
    app_thread = None

    # Variables for communication between threads
    requests_sem = None
    requests_queue = []

    def __init__(self):
        # initialize in memory and on file db
        self.db_conn = sqlite3.connect(":memory:")
        self.backup_db_conn = sqlite3.connect("state.db")

        # load on file db into memory
        self.backup_db_conn.backup(self.db_conn)

        # initialize requests semaphore
        self.requests_sem = Semaphore(0)

        self.log_to_file("Core", "Core Initialized")

    #####################
    # Startup Functions #
    #####################

    def start_request_loop(self):
        while(True):
            self.requests_sem.acquire()

            # fulfill request
            request = self.requests_queue.pop(0)
            request["retval"].append(request["func"](request["params"]))
            request["event"].set()

    def start_gui(self):
        self.app = App(self)
        self.app.mainloop()

    def start_app_thread(self):
        self.app_thread = Thread(target=self.start_gui)
        self.app_thread.start()

    def run_core(self):
        self.start_app_thread()
        self.start_request_loop()

    ###########################
    # Internal Data Functions #
    ###########################

    def initialize_tables(self):
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
        transaction = self.db_conn.cursor()

        # load entity into db
        transaction.execute("""INSERT INTO Substation(SUB_NUM, GRID_NAME, SUB_LATITUDE, SUB_LONGITUDE)
        VALUES(?,?,?,?)""", [sub_num, grid_name, sub_latitude, sub_longitude])

        lastrowid = transaction.lastrowid

        self.db_conn.commit()

        transaction.close()

        return lastrowid

    def add_bus(self, bus_num, sub_num, grid_name):
        transaction = self.db_conn.cursor()

        # load entity into db
        transaction.execute("""INSERT INTO Bus(BUS_NUM, SUB_NUM, GRID_NAME)
        VALUES(?,?,?)""", [bus_num, sub_num, grid_name])

        self.db_conn.commit()

        transaction.close()

    def add_branch_and_transformer(self, from_bus, to_bus, circuit, has_trans, grid_name):
        transaction = self.db_conn.cursor()

        # load branch entity into db
        transaction.execute("""INSERT INTO Branch(FROM_BUS, TO_BUS, CIRCUIT, GRID_NAME, HAS_TRANSFORMER)
        VALUES(?,?,?,?,?)""", [from_bus, to_bus, circuit, grid_name, has_trans])

        self.db_conn.commit()

        transaction.close()
    
    def save_to_file(self):
        self.db_conn.backup(self.backup_db_conn)

    #########################
    # Requestable Functions #
    #########################

    def save_grid_data(self, params):
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
            self.add_bus(bus_num, bus["sub_num"], grid_name)

        self.log_to_file("Core", "Buses Added")

        for branch in branch_data:
            from_bus_num = branch[0]
            to_bus_num = branch[1]
            circuit_num = branch[2]
            self.add_branch_and_transformer(from_bus_num, to_bus_num, circuit_num, branch_data[branch]["has_trans"], grid_name)

        self.log_to_file("Core", "Branches Added")

        self.save_to_file()

        self.log_to_file("Core", "Loading Grid Took: " + str(time() - start) + " seconds")

    def get_data_for_time(self, params):
        grid_name = params["grid_name"]
        timepoint = params["timepoint"]

        transaction = self.db_conn.cursor()

        transaction.execute("""SELECT * FROM Datapoint WHERE GRID_NAME=? AND DPOINT_TIME=?""", (grid_name, timepoint.strftime("%m/%d/%Y, %H:%M:%S")))

        data = transaction.fetchall()

        transaction.close()

        return data

    def fabricate_hour_of_data(self, params):
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

    def close_application(self, _):
        exit()

    ###################
    # Misc. Functions #
    ###################

    def send_request(self, func, params = None, retval = []):
        request_event = Event()
        request = {"event" : request_event, "func" : func,
                   "params" : params, "retval" : retval}
        self.requests_queue.append(request)
        self.requests_sem.release()
        return request_event

    def log_to_file(self, source, msg):
        with open("log.txt", "a+") as logfile:
            logfile.write("From " + source + ": " + msg + "\n")

if __name__ == "__main__":
    core = Core()
    core.run_core()
