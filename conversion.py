import sqlite3
from _sqlite3 import Error
from pathlib import Path
import pandas


def convert(csvfile, conn):
    data = pandas.read_csv(csvfile, encoding='latin-1', sep=';', decimal=',', skipfooter=1,
                           dtype={'Aikaväli': str, 'Kulutus': float, 'Lämpötila': float}).fillna(value=0)

    daytime = data['Aikaväli'].str.split(' ', n=1, expand=True)  # Split daytime cell to time and date
    daytime[0] = daytime[0]+year(csvfile)  # Add year to date
    daytime[0] = pandas.to_datetime(daytime[0])  # Reformatting date

    data['Time'] = daytime[1]  # Updating dataframe
    data['Date'] = daytime[0]
    data = data.drop(columns=['Aikaväli'])
    data = data.reindex(columns=['Date', 'Time', 'Kulutus', 'Lämpötila'])

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
        return

    conn.close()


if __name__ == '__main__':
    csvfile = f"{Path(__file__).parent.resolve()}/test-data/consumption_20200224_20210101.csv"
    db_file = f"{Path(__file__).parent.resolve()}/db/energy_consumption.db"
    main(csvfile, db_file)
