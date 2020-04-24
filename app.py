import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from pathlib import Path
from _sqlite3 import Error
import sqlite3
import datetime as dt


def form_graph(resolution, d=0, timeframe=None):
    """
    Forms the main graph for the main page.

    :param resolution: Units of x-axis as str(Weekday, Hour, Day, Week, Month, Year)
    :param d: if timeframe is not given defaults sets delayed time frame starting from (d) days from today.
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
    timestring = {'Hour': '%Y-%m-%dT%H:00', 'Weekday': '%w', 'Day': '%Y-%m-%d', 'Week': '%Y/%W', 'Month': '%Y-%m', 'Year': '%Y'}

    df = dataparser(f"{Path(__file__).parent.resolve()}/db/energy_consumption.db",
                    f"SELECT "
                    f"strftime('{timestring.get(resolution)}',Aikaväli) as TimeFrame, SUM(Kulutus) as Consumption "
                    f"FROM 'Energy' WHERE Kulutus > 0 AND '{end}' >= Aikaväli AND '{begin}' <= Aikaväli GROUP  BY TimeFrame")

    if resolution == 'Weekday':  # If Weekdays are set as a resolution x-axis values are replaced with weekdays' names
        weekday = {'0': 'Sunday', '1': 'Monday', '2': 'Tuesday', '3': 'Wednesday', '4': 'Thursday', '5': 'Friday', '6': 'Saturday'}
        df['TimeFrame'] = df['TimeFrame'].replace(to_replace=weekday, value=None)

    figure = {
        'data': [{'x': df['TimeFrame'], 'y': df['Consumption'], 'type': 'bar', 'name': 'SF'}],
        'layout': {
            'title': 'Your energy consumption',
            'xaxis': {'title': resolution},
            'yaxis': {'title': 'kWh'}}}

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

        dcc.Graph(id='main-graph', figure=form_graph('Day', 30)),  # Main Graph


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
                        value=30)], className="two columns")]),

        html.Div(children=[
            html.Div(children=[
                html.Label('Resolution:'),
                dcc.RadioItems(id='Resolution',
                    options=[
                        {'label': 'Weekdays', 'value': 'Weekday'},
                        {'label': 'Hourly', 'value': 'Hour'},
                        {'label': 'Daily', 'value': 'Day'},
                        {'label': 'Weekly', 'value': 'Week'},
                        {'label': 'Monthly', 'value': 'Month'},
                        {'label': 'Yearly', 'value': 'Year'}],
                        value='Day')], className="two columns")]),

        html.Div(children=[
            html.Div(children=[
                html.Label('Additional options:'),
                dcc.Checklist(
                    options=[
                        {'label': 'Show temperature', 'value': 't'},
                        {'label': 'Compare two time frames', 'value': 'c'}],
                    value=['t'])], className="three columns")], className="row")])

    @app.callback(  # Main Graph update callback
        Output('main-graph', 'figure'),
        [Input('Resolution', 'value'), Input('Days', 'value')])
    def update_graph(resolution, days):
        figure = form_graph(resolution, days)
        return figure

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
