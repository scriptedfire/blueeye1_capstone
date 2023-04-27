import sqlite3

class Core():
    def __init__(self):
        # initialize in memory and on file db
        self.db_conn = sqlite3.connect(":memory:")
        self.backup_db_conn = sqlite3.connect("state.db")

        # load on file db into memory
        self.backup_db_conn.backup(self.db_conn)

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

        transaction.execute("""CREATE TABLE IF NOT EXISTS Simulation (
        SIM_ID integer PRIMARY KEY,
        GRID_NAME text NOT NULL,
        START_TIME text NOT NULL,
        FOREIGN KEY (GRID_NAME) REFERENCES Grid (GRID_NAME)
        )""")

        transaction.execute("""CREATE TABLE IF NOT EXISTS Datapoint (
        DPOINT_ID integer PRIMARY KEY,
        SIM_ID integer NOT NULL,
        FROM_BUS integer NOT NULL,
        TO_BUS integer NOT NULL,
        GRID_NAME text NOT NULL,
        DPOINT_TIME text NOT NULL,
        DPOINT_GIC real NOT NULL,
        DPOINT_VLEVEL real,
        DPOINT_TTC real,
        FOREIGN KEY (FROM_BUS, TO_BUS, GRID_NAME) REFERENCES Branch (FROM_BUS, TO_BUS, GRID_NAME)
        )""")

        self.db_conn.commit()

        transaction.close()

    ############################
    # Basic Grid Add Functions #
    ############################

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

    # FIXME: log prints to file
    def load_grid_data(self, grid_name, substation_data, bus_data, branch_data):
        self.initialize_tables()

        # ignore if grid already exists
        if(self.add_grid_if_not_exists(grid_name) == None):
            print("Grid Already Exists")
            return
        
        print("Grid Added")
        
        for sub_num in substation_data:
            sub = substation_data[sub_num]
            self.add_substation(grid_name, sub_num, sub["lat"], sub["long"])

        print("Substations Added")

        for bus_num in bus_data:
            bus = bus_data[bus_num]
            self.add_bus(bus_num, bus["sub_num"], grid_name)

        print("Buses Added")

        for branch in branch_data:
            from_bus_num = branch[0]
            to_bus_num = branch[1]
            self.add_branch_and_transformer(from_bus_num, to_bus_num, branch_data[branch]["has_trans"], grid_name)

        print("Branches Added")

        self.save_to_file()
