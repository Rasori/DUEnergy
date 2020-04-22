import sqlite3
from _sqlite3 import Error
from pathlib import Path
import pandas as pd
import conversion


def connect_db(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
        raise Error


def main():

    db_file = f"{Path(__file__).parent.resolve()}/db/energy_consumption.db"
    conversion.update()
    connect_db(db_file)

