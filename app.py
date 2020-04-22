# -*- coding: utf-8 -*-
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from pathlib import Path
from _sqlite3 import Error
import sqlite3


def main():
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    df = dataparser(f"{Path(__file__).parent.resolve()}/db/energy_consumption.db",
                    "SELECT strftime('%W',Aikaväli) as week, SUM(Kulutus) as consumption FROM 'Energy' WHERE Kulutus>0 GROUP BY week")
    app.title = 'DUEnergy'
    app.layout = html.Div(children=[
        html.H1(children='DUEnergy'),

        html.Div(children='''
            For those that are interested in their energy consumption habits.
        '''),
        dcc.Graph(
            id='main-graph',
            figure={
                'data': [
                    {'x': df['week'], 'y': df['consumption'], 'type': 'bar', 'name': 'SF'},
                ],
                'layout': {
                    'title': 'Your energy consumption',
                    'xaxis': {
                        'title': 'Week'
                    },
                    'yaxis': {
                        'title': 'kWh'
                    }
                }
            }
        ),
        html.Div(children=[
            html.Div(children=[
                html.Label('Time frame:'),
                dcc.RadioItems(
                    options=[
                        {'label': 'Last day', 'value': 'lD'},
                        {'label': 'Last month', 'value': 'lM'},
                        {'label': 'Last year', 'value': 'lY'},
                        {'label': 'Everything', 'value': 'A'}
                    ],
                    value='lM'
                )
            ], className="two columns"),
        ]),
        html.Div(children=[
            html.Div(children=[
                html.Label('Resolution:'),
                dcc.RadioItems(
                    options=[
                        {'label': 'Weekdays', 'value': 'w'},
                        {'label': 'Hourly', 'value': 'H'},
                        {'label': 'Daily', 'value': 'D'},
                        {'label': 'Weekly', 'value': 'W'},
                        {'label': 'Monthly', 'value': 'M'},
                        {'label': 'Yearly', 'value': 'Y'}
                    ],
                    value='D'
                )
            ], className="two columns")
        ]),
        html.Div(children=[
            html.Div(children=[
                html.Label('Additional options:'),
                dcc.Checklist(
                    options=[
                        {'label': 'Show temperature', 'value': 't'},
                        {'label': 'Compare two time frames', 'value': 'c'}
                    ],
                    value=['t']
                )
            ], className="three columns")
        ], className="row")
    ])

    app.run_server(host='0.0.0.0', port=8000, debug=True)


def connect_db(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
        raise Error


def dataparser(db_file, query):
    db = connect_db(db_file)
    df = pd.read_sql_query(query, db)
    return df


if __name__ == '__main__':
    main()
