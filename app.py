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


def form_graph(resolution, d=0, temperature=False, timeframe=None):
    """
    Forms the main graph for the main page.

    :param resolution: Units of x-axis as str(Weekday, Hour, Day, Week, Month, Year)
    :param d: if timeframe is not given defaults sets delayed time frame starting from (d) days from today.
    :param temperature: Boolean argument stating whether or not to show temperature trace
    :param timeframe: Set custom time frame as str according to ISO-8601
    :return: Figure data and styling as a dict
    """

    if timeframe:
        end = timeframe[1]
        begin = timeframe[0]
    else:
        end = dt.date.today()
        begin = (end - dt.timedelta(days=d)).strftime('%Y-%m-%d')

    # resolution parameter is searched from timestring
    timestring = {'Hour': '%Y-%m-%dT%H:00',
                  'Day hours': '%H',
                  'Weekday': '%w',
                  'Day': '%Y-%m-%d',
                  'Week': '%Y-W%W',
                  'Month': '%Y-%m',
                  'Year': '%Y'}

    df = dataparser(f"{Path(__file__).parent.resolve()}/db/energy_consumption.db",
                    f"SELECT "
                    f"strftime('{timestring.get(resolution)}',Aikaväli) as Date, SUM(Kulutus) as Consumption "
                    f"FROM 'Energy' WHERE Kulutus > 0 AND '{end}' >= Aikaväli AND '{begin}' <= Aikaväli GROUP  BY Date")

    dfT = dataparser(f"{Path(__file__).parent.resolve()}/db/energy_consumption.db",
                    f"SELECT "
                    f"strftime('{timestring.get('Day')}',Aikaväli) as Date, SUM(Lämpötila) as Temperature "
                    f"From 'Energy' WHERE '{end}' >= Aikaväli AND '{begin}' <= Aikaväli GROUP  BY Date")

    if resolution == 'Weekday':  # If Weekdays are set as a resolution x-axis values are replaced with weekdays' names
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
            'title': 'Your energy consumption',
            'clickmode': 'event',
            'uirevision': 'no reset of zoom',
            'xaxis': {'title': 'Date',
                      'rangeselector': dict(
                          buttons=list([
                            dict(count=1,
                                 label="D",
                                 step="day",
                                 stepmode="backward"),
                            dict(count=7,
                                 label="W",
                                 step="day",
                                 stepmode="backward"),
                            dict(count=1,
                                 label="M",
                                 step="month",
                                 stepmode="backward"),
                            dict(count=6,
                                 label="6 M",
                                 step="month",
                                 stepmode="backward"),
                            dict(count=1,
                                 label="Y",
                                 step="year",
                                 stepmode="backward"),
                            dict(step="all")])),
                      'type': 'date'},
            'yaxis': {'title': 'Consumption [kWh]'}}}

    if temperature and resolution == 'Hour' or temperature and resolution == 'Day':  # checks the conditions for temperature trace
        figure.get('data').append(go.Scatter(x=dfT['Date'], y=dfT['Temperature'], name='Temperature'))
    return figure


def main():
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    app.title = 'DUEnergy'

    # Start of the page layout
    app.layout = html.Div(children=[  # Main frame
        html.Div(children=[
                html.H1(children='DUEnergy', style={'textAlign': 'center'}),
                html.H3('For those that are interested in their energy consumption habits', style={'textAlign': 'center'})]),

        dcc.Graph(id='main-graph', figure=form_graph('Day', 30), ),  # Main Graph


        #  Radio items ETC.
        html.Div(children=[
            html.Div(children=[
                html.Label('Time frame:'),
                dcc.RadioItems(id='Days',
                               options=[
                                    {'label': 'Last day', 'value': 1},
                                    {'label': 'Last week', 'value': 7},
                                    {'label': 'Last month', 'value': 30},
                                    {'label': 'Last year', 'value': 365},
                                    {'label': 'Everything', 'value': 10*365}],
                               value=10*365)], className="two columns")]),

        html.Div(children=[
            html.Div(children=[
                html.Label('Resolution:'),
                dcc.RadioItems(id='Resolution',
                               options=[
                                    {'label': 'Weekdays', 'value': 'Weekday'},
                                    {'label': 'Day hours', 'value': 'Day hours'},
                                    {'label': 'Hourly', 'value': 'Hour'},
                                    {'label': 'Daily', 'value': 'Day'},
                                    {'label': 'Weekly', 'value': 'Week'},
                                    {'label': 'Monthly', 'value': 'Month'},
                                    {'label': 'Yearly', 'value': 'Year'}],
                               value='Day')], className="two columns")]),

        html.Div(children=[
            html.Div(children=[
                html.Label('Additional options:'),
                dcc.Checklist(id='Options',
                              options=[
                                {'label': 'Show temperature', 'value': 'Temp'},
                                {'label': 'Compare two time frames', 'value': 'c'}],
                              value=[])], className="three columns")], className="row")])

    @app.callback(  # Main Graph update callback
        Output('main-graph', 'figure'),
        [Input('Resolution', 'value'), Input('Days', 'value'), Input('Options', 'value'), Input('main-graph', 'relayoutData')])
    def update_graph(resolution, days, options, relayoutData):

        if 'Temp' in options:  # Sets temperature plotting True if check box is checked
            temperature = True
        else:
            temperature = False

        # Handels the resolution change when zoomed
        if type(relayoutData) == dict:
            if 'autosize' not in relayoutData and 'xaxis.autorange' not in relayoutData:
                fmt = '%Y-%m-%d %H'
                timeframe = dt.datetime.strptime(relayoutData['xaxis.range[1]'].split(':')[0], fmt) - dt.datetime.strptime(
                    relayoutData['xaxis.range[0]'].split(':')[0], fmt)

                if timeframe.days < 2*365:
                    resolution = 'Year'
                if timeframe.days < 765:
                    resolution = 'Month'
                #if timeframe.days < 7*6:
                #    resolution = 'Week'
                if timeframe.days <= 62:
                    resolution = 'Day'
                if timeframe.days <= 7:
                    resolution = 'Hour'
        else:
            resolution = 'Day'

        figure = form_graph(resolution, days, temperature=temperature)
        return figure

    app.run_server(host='0.0.0.0', port=8000, debug=True)  # Starts the flask server


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
