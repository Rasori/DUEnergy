from flask import Flask, render_template, request
import plotly
import plotly.graph_objs as go
import sqlite3
from _sqlite3 import Error
from pathlib import Path
import pandas as pd
import numpy as np
import json

app = Flask(__name__)

DB_FILE = f"{Path(__file__).parent.resolve()}/db/energy_consumption.db"

@app.route('/')
def index():
    bar = create_plot(DB_FILE)
    return render_template('index.html', plot=bar)


def create_plot(db_file):
    db = connect_db(db_file)
    df = pd.read_sql_query("SELECT * FROM Energy", db)
    db.close()

    data = [go.Bar(y=df['Kulutus'], x=df['Aikaväli'], orientation='v')]



    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


@app.route('/bar', methods=['GET', 'POST'])
def change_features():

    feature = request.args['selected']
    graphJSON = create_plot(feature)

    return graphJSON





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
