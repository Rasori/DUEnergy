import datetime as dt
import sqlite3
from _sqlite3 import Error
from pathlib import Path
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate


def form_maingraph(resolution, temperature=False):
    """
    Forms the main graph for the main page.

    :param resolution: Units of x-axis as str( Hour, Day, Week, Month, Year)
    :param temperature: Boolean argument stating whether or not to show temperature trace
    :return: Figure data and layout as a dict
    """


    # resolution parameter is searched from timestring
    timestring = {'Hour': '%Y-%m-%dT%H:00',
                  'Day': '%Y-%m-%d',
                  'Week': '%Y-W%W',
                  'Month': '%Y-%m',
                  'Year': '%Y'}

    df = dataparser(f"{Path(__file__).parent.resolve()}/db/energy_consumption.db",
                    f"SELECT "
                    f"strftime('{timestring.get(resolution)}',Aikaväli) as Date, SUM(Kulutus) as Consumption "
                    f"FROM 'Energy' WHERE Kulutus > 0 GROUP  BY Date")

    dfT = dataparser(f"{Path(__file__).parent.resolve()}/db/energy_consumption.db",
                    f"SELECT "
                    f"strftime('{timestring.get('Day')}',Aikaväli) as Date, SUM(Lämpötila) as Temperature "
                    f"From 'Energy' GROUP  BY Date")

    figure = {
        'data': [{
            'x': df['Date'],
            'y': df['Consumption'],
            'type': 'bar',
            'name': 'Consumption'}],
        'layout': {
            'title': 'Your energy consumption',
            'dragmode': 'pan',  # Sets pan as a default tool
            'clickmode': 'event',
            'uirevision': 'no reset of zoom',
            'xaxis': {'title': 'Date',
                      'rangeselector': dict(
                          buttons=list([
                            dict(count=1,
                                 label="D",
                                 step="day",
                                 stepmode="todate"),
                            dict(count=3,
                                 label="3D",
                                 step="day",
                                 stepmode="todate"),
                            dict(count=7,
                                 label="W",
                                 step="day",
                                 stepmode="todate"),
                            dict(count=1,
                                 label="M",
                                 step="month",
                                 stepmode="todate"),
                            dict(count=6,
                                 label="6M",
                                 step="month",
                                 stepmode="todate"),
                            dict(count=1,
                                 label="Y",
                                 step="year",
                                 stepmode="todate"),
                            dict(step="all")])),
                      'type': 'date',
                      'range': [dt.date.today()-dt.timedelta(days=2), dt.date.today()+dt.timedelta(days=1)]},
            'yaxis': {'title': 'Consumption [kWh]',
                      'fixedrange': True}}}  # Locks the y-axis from zooming

    if temperature and resolution == 'Hour' or temperature and resolution == 'Day':  # checks the conditions for temperature trace
        figure.get('data').append(go.Scatter(x=dfT['Date'], y=dfT['Temperature'], name='Temperature'))

    return figure


def form_secondarygraph(type):
    """
    Forms the secondary graphs for the main page.

    :param type: A str describing the type of the graph (Weekday or Day hours)
    :return: Figure data and layout as a dict
    """

    settings = {'Weekday': dict(timestring='%w', factor=24, title='days of the week'),
                'Day hours': dict(timestring='%H', factor=1, title='hours of the day')}

    df = dataparser(f"{Path(__file__).parent.resolve()}/db/energy_consumption.db", f"SELECT "
                                                                                   f"strftime('{settings[type]['timestring']}',Aikaväli) as Date, "
                                                                                   f"AVG(Kulutus)*{settings[type]['factor']} as Consumption "
                                                                                   f"FROM 'Energy' "
                                                                                   f"WHERE Kulutus > 0 "
                                                                                   f"GROUP  BY Date")

    if type == 'weekday':  # If Weekdays are set as a type, The x-axis values are replaced with weekdays' names
        weekday = {'0': 'Sunday',
                   '1': 'Monday',
                   '2': 'Tuesday',
                   '3': 'Wednesday',
                   '4': 'Thursday',
                   '5': 'Friday',
                   '6': 'Saturday'}

        df['Date'] = df['Date'].replace(to_replace=weekday, value=None)

    figure = {
        'data': [{
            'x': df['Date'],
            'y': df['Consumption'],
            'type': 'bar',
            'name': 'Consumption'}],
        'layout': {
            'title': f"Average consumption through <br> the {settings[type]['title']}",
            'xaxis': {'title': type, 'fixedrange': True},
            'yaxis': {'title': 'Consumption [kWh]',
                      'fixedrange': True}}}  # Locks the y-axis from zooming

    return figure


def main():
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    app.title = 'DUEnergy'

    # Start of the page layout
    app.layout = html.Div(children=[  # Main frame
        html.Div(children=[
                html.H1(children='DUEnergy', style={'textAlign': 'center'}),
                html.H3('For those that are interested in their energy consumption habits', style={'textAlign': 'center'})
        ]),

        html.Div(children=[
            html.Div(children=[dcc.Graph(id='main-graph', figure=form_maingraph('Day'))], className='ten columns'),

            html.Div(children=[html.Label('Additional options:'),
                               dcc.Checklist(id='Options', options=[{'label': 'Show temperature', 'value': 'Temp'}], value=[])],
                     className="two columns")]),

        html.Div(children=[html.Div(children=[dcc.Graph(id='weekday-graph', figure=form_secondarygraph('Weekday'))], className='five columns'),
                           html.Div(children=[dcc.Graph(id='dayhour-graph', figure=form_secondarygraph('Day hours'))], className='seven columns')],
                 className="row")
    ])

    @app.callback(  # Main Graph update callback
        Output('main-graph', 'figure'),
        [Input('Options', 'value'), Input('main-graph', 'relayoutData')])
    def update_graph(options, relayoutData):

        if 'Temp' in options:  # Sets temperature plotting True if check box is checked
            temperature = True
        else:
            temperature = False

        # Handels the resolution change when zoomed
        print(relayoutData)
        if type(relayoutData) == dict:
            if 'xaxis.range[0]' in relayoutData:
                frame = []
                for daterange in [relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']]:
                    for fmt in ['%Y-%m-%d %H', '%Y-%m-%d']:
                        try:
                            frame.append(dt.datetime.strptime(daterange.split(':')[0], fmt))
                            break
                        except ValueError:
                            continue
                timeframe = frame[1] - frame[0]

                if timeframe.days > 390:
                    resolution = 'Year'
                if timeframe.days <= 390:
                    resolution = 'Month'
                if timeframe.days <= 69:
                    resolution = 'Day'
                if timeframe.days <= 7:
                    resolution = 'Hour'
            elif 'autosize' in relayoutData or 'xaxis.autorange' in relayoutData:
                resolution = 'Month'
            else:
                raise PreventUpdate()
        else:
            resolution = 'Day'

        figure = form_maingraph(resolution, temperature=temperature)
        return figure

    app.run_server(host='0.0.0.0', port=8000, debug=True, threaded=True)  # Starts the flask server


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
