#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# dash_skeleton.py

"""A demo app that can be used as a skeleton template for bootstrapping the
creation of simple Plotly Dash apps.

"""

from collections import Counter

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, State, Output, Event
from textwrap import dedent

from dashboard.components import Col
from dashboard.components import Container
from dashboard.components import Row


app = dash.Dash(__name__)
app.title = 'Dash Skeleton'

# If you need to run your app locally
#app.scripts.config.serve_locally = True


def generate_table(max_rows=10):
    df = pd.read_csv('data/processed/scored-data_2017-to-2017.csv').fillna(0)
    df = df[['player', 'team', 'position', 'total_score']]
    return html.Table(
        # Header
        [ html.Tr([html.Th(col, scope='col') for col in df.columns]) ]
        +
        # Body
        [html.Tr([
            html.Td(df.iloc[i][col]) for col in df.columns
        ]) for i in range(min(len(df), max_rows))],
        className='table',
    )

app.layout = Container([
    Row([
        Col(
            [ generate_table(100) ],
            bp='sm',
            size=6,
        ),
    ]),
])


if __name__ == '__main__':
    # To make this app publicly available, supply the parameter host='0.0.0.0'.
    # You should also disable debug mode in production.
    app.run_server(debug=True, port=8051)
