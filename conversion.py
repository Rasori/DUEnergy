import sqlite3
from _sqlite3 import Error
from pathlib import Path
import pandas


def convert(csvfile, conn):
    data = pandas.read_csv(csvfile, encoding='latin-1', sep=';', decimal=',', skipfooter=1,
                           dtype={'Aikaväli': str, 'Kulutus': float, 'Lämpötila': float}).fillna(value=0)

    daytime = data['Aikaväli'].str.split(' ', n=1, expand=True)  # Split daytime cell to time and date
    daytime[0] = daytime[0]+year(csvfile)+' '+daytime[1]  # Add year to date
    daytime[0] = pandas.to_datetime(daytime[0].astype(str), format='%d.%m.%Y %H:%M:%S')  # Reformatting date

    data['Aikaväli'] = daytime[0]  # Updating the dataframe

    data = data.reindex(columns=['Aikaväli', 'Kulutus', 'Lämpötila'])
    data.to_sql("Energy", conn, index=False, if_exists='replace')  # Saving to SQL


def year(filename):
    """
    Parses the year from the filename provided
    :param filename:
    :return: year (%YYYY) as str
    """

    year = filename.split('_')[1][0:4]
    return year


def main(csvfile, db_file):
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
        return

    try:
        convert(csvfile, conn)
    except Error as e:
        print(e)
        return e

    conn.close()


def update():
    csvfile = f"{Path(__file__).parent.resolve()}/test-data/consumption_20200224_20210101.csv"
    db_file = f"{Path(__file__).parent.resolve()}/db/energy_consumption.db"
    main(csvfile, db_file)
