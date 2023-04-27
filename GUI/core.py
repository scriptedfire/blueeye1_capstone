import sqlite3
from datetime import datetime, timedelta
from random import randrange

class Core():
    def __init__(self):
        # initialize in memory and on file db
        self.db_conn = sqlite3.connect(":memory:")
        self.backup_db_conn = sqlite3.connect("state.db")

        # load on file db into memory
        self.backup_db_conn.backup(self.db_conn)

        self.log_to_file("Core", "Core Initialized")

    def save_to_file(self):
        self.db_conn.backup(self.backup_db_conn)

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
        GRID_NAME text NOT NULL,
        HAS_TRANSFORMER boolean NOT NULL,
        PRIMARY KEY (FROM_BUS, TO_BUS, GRID_NAME),
        FOREIGN KEY (FROM_BUS, GRID_NAME) REFERENCES Bus (BUS_NUM, GRID_NAME),
        FOREIGN KEY (TO_BUS, GRID_NAME) REFERENCES Bus (BUS_NUM, GRID_NAME)
        )""")

        transaction.execute("""CREATE TABLE IF NOT EXISTS Datapoint (
        FROM_BUS integer NOT NULL,
        TO_BUS integer NOT NULL,
        GRID_NAME text NOT NULL,
        DPOINT_TIME text NOT NULL,
        DPOINT_GIC real NOT NULL,
        DPOINT_VLEVEL real,
        DPOINT_TTC real,
        PRIMARY KEY (DPOINT_TIME, FROM_BUS, TO_BUS, GRID_NAME),
        FOREIGN KEY (FROM_BUS, TO_BUS, GRID_NAME) REFERENCES Branch (FROM_BUS, TO_BUS, GRID_NAME)
        )""")

        self.db_conn.commit()

        transaction.close()

    ###############################
    # Grid Data Loading Functions #
    ###############################

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

    def add_branch_and_transformer(self, from_bus, to_bus, has_trans, grid_name):
        transaction = self.db_conn.cursor()

        # load branch entity into db
        transaction.execute("""INSERT INTO Branch(FROM_BUS, TO_BUS, GRID_NAME, HAS_TRANSFORMER)
        VALUES(?,?,?,?)""", [from_bus, to_bus, grid_name, has_trans])

        self.db_conn.commit()

        transaction.close()

    def load_grid_data(self, grid_name, substation_data, bus_data, branch_data):
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
            self.add_branch_and_transformer(from_bus_num, to_bus_num, branch_data[branch]["has_trans"], grid_name)

        self.log_to_file("Core", "Branches Added")

        self.save_to_file()

    ###################
    # Misc. Functions #
    ###################

    def log_to_file(self, source, msg):
        with open("log.txt", "a+") as logfile:
            logfile.write("From " + source + ": " + msg + "\n")

    def create_hour_of_data(self, grid_name, start_time):
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
                has_trans = branch[3]
                gic = randrange(0, 999)
                vlevel = None
                ttc = None

                if(has_trans != 0):
                    vlevel = randrange(0, 999)
                    ttc = randrange(0, 999)

                transaction.execute("""INSERT INTO Datapoint(FROM_BUS, TO_BUS, GRID_NAME,
                DPOINT_TIME, DPOINT_GIC, DPOINT_VLEVEL, DPOINT_TTC) VALUES(?,?,?,?,?,?,?)""",
                [from_bus, to_bus, grid_name, dpoint_time, gic, vlevel, ttc])

                self.db_conn.commit()

            start_time += timedelta(minutes=1)

        transaction.close()

        self.save_to_file()

    def get_data_for_time(self, grid_name, timepoint):
        transaction = self.db_conn.cursor()

        transaction.execute("""SELECT * FROM Datapoint WHERE GRID_NAME=? AND DPOINT_TIME=?""", (grid_name, timepoint.strftime("%m/%d/%Y, %H:%M:%S")))

        data = transaction.fetchall()

        transaction.close()

        return data
    
    def close_conns(self):
        self.backup_db_conn.close()
        self.db_conn.close()

    def reopen_conns(self):
        # initialize in memory and on file db
        self.db_conn = sqlite3.connect(":memory:")
        self.backup_db_conn = sqlite3.connect("state.db")

        # load on file db into memory
        self.backup_db_conn.backup(self.db_conn)

if __name__ == "__main__":
    testcore = Core()
    testdate = datetime(2023, 4, 27, 2, 30)
    testcore.create_hour_of_data("/home/esanders/blueeye1_capstone/GUI/Polish_Grid/Polish_grid", testdate)
