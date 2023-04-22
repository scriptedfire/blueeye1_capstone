import sqlite3

class Core():
    def __init__(self):
        self.db_conn = sqlite3.connect("state.db")

    def initialize_tables(self):
        transaction = self.db_conn.cursor()

        # FIXME: Name must be unique
        transaction.execute("""CREATE TABLE IF NOT EXISTS Grid (
        GRID_ID integer PRIMARY KEY,
        GRID_NAME text NOT NULL
        )""")

        transaction.execute("""CREATE TABLE IF NOT EXISTS Substation (
        SUB_NUM integer PRIMARY KEY,
        GRID_ID integer NOT NULL,
        SUB_LATITUDE real NOT NULL,
        SUB_LONGITUDE real NOT NULL,
        FOREIGN KEY (GRID_ID) REFERENCES Grid (GRID_ID)
        )""")

        transaction.execute("""CREATE TABLE IF NOT EXISTS Bus (
        BUS_NUM integer PRIMARY KEY,
        SUB_NUM integer NOT NULL,
        FOREIGN KEY (SUB_NUM) REFERENCES Substation (SUB_NUM)
        )""")

        transaction.execute("""CREATE TABLE IF NOT EXISTS Branch (
        BRANCH_ID integer PRIMARY KEY,
        FROM_BUS integer NOT NULL,
        TO_BUS integer NOT NULL,
        HAS_TRANSFORMER boolean NOT NULL,
        FOREIGN KEY (FROM_BUS) REFERENCES Bus (BUS_NUM),
        FOREIGN KEY (TO_BUS) REFERENCES Bus (BUS_NUM)
        )""")

        transaction.execute("""CREATE TABLE IF NOT EXISTS Transformer (
        TRANS_ID integer PRIMARY KEY,
        BRANCH_ID integer NOT NULL,
        FOREIGN KEY (BRANCH_ID) REFERENCES Branch (BRANCH_ID)
        )""")

        transaction.execute("""CREATE TABLE IF NOT EXISTS Simulation (
        SIM_ID integer PRIMARY KEY,
        GRID_ID integer NOT NULL,
        START_TIME text NOT NULL,
        FOREIGN KEY (GRID_ID) REFERENCES Grid (GRID_ID)
        )""")

        transaction.execute("""CREATE TABLE IF NOT EXISTS Datapoint (
        DPOINT_ID integer PRIMARY KEY,
        SIM_ID integer NOT NULL,
        BRANCH_ID integer NOT NULL,
        TRANS_ID integer,
        DPOINT_TIME text NOT NULL,
        DPOINT_GIC real NOT NULL,
        DPOINT_VLEVEL real,
        DPOINT_TTC real,
        FOREIGN KEY (SIM_ID) REFERENCES Simulation (SIM_ID),
        FOREIGN KEY (BRANCH_ID) REFERENCES Branch (BRANCH_ID),
        FOREIGN KEY (TRANS_ID) REFERENCES Transformer (TRANS_ID)
        )""")

        self.db_conn.commit()

        transaction.close()

    def add_grid(self, grid_name):
        transaction = self.db_conn.cursor()

        transaction.execute("""INSERT INTO Grid(GRID_NAME)
        VALUES(?)""", [grid_name])

        self.db_conn.commit()

        transaction.close()

    # FIXME: complete and verify
    def add_substation(self, grid_name, sub_num, sub_latitude, sub_longitude):
        transaction = self.db_conn.cursor()

        transaction.execute("""SELECT * FROM Grid WHERE GRID_NAME=?""",(grid_name,))

        print(transaction.fetchall())

if __name__ == "__main__":
    testcore = Core()
    testcore.initialize_tables()
    testcore.add_grid("test_grid")
    testcore.add_substation("test_grid", 1, 1, 1)