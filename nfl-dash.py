#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# dash_skeleton.py

"""A demo app that can be used as a skeleton template for bootstrapping the
creation of simple Plotly Dash apps.

"""

from collections import Counter

import warnings
with warnings.catch_warnings():
    # ignore warnings that are safe to ignore according to
    # https://github.com/ContinuumIO/anaconda-issues/issues/6678
    # #issuecomment-337276215
    warnings.simplefilter("ignore")
    import dash
    import dash_core_components as dcc
    import dash_html_components as html
    import pandas as pd
from plotly.colors import DEFAULT_PLOTLY_COLORS
from dash.dependencies import Input, State, Output, Event
import numpy as np

from dashboard.components import Col
from dashboard.components import Container
from dashboard.components import Row


app = dash.Dash(__name__)
app.title = 'Dash Skeleton'
my_css_url = "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"
app.css.append_css({"external_url": my_css_url})
BOOTSTRAP_SCREEN_SIZE='lg'

# If you need to run your app locally
#app.scripts.config.serve_locally = True

scores_summary_csv_path = 'data/processed/scores-summary_2017-to-2017.csv'
FULL_DF = pd.read_csv(scores_summary_csv_path).fillna(0)
ALL_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DEFENSE']
POSITION_COLORS = {p: c for p, c in zip(ALL_POSITIONS, DEFAULT_PLOTLY_COLORS)}


def get_updated_df(positions=ALL_POSITIONS, max_rows=50):
    df = FULL_DF.copy()
    df = df[df['position'].isin(positions)].copy()
    if len(df > max_rows):
        df = df.iloc[:max_rows, :].copy()
    columns = [
        'player', 'team', 'position', 'season_total', 'week_avg', 'week_std'
    ]
    numerical_columns = ['season_total', 'week_avg', 'week_std']
    df = df[columns].copy()
    df.loc[:, numerical_columns] = df[numerical_columns].round(1)
    return df


app.layout = Container([
    Row([
        Col([
            Row([
                Col([
                    dcc.Graph(id='graph_1')
                ], bp=BOOTSTRAP_SCREEN_SIZE, size=12,),
                Col([
                    dcc.Graph(id='graph_2')
                ], bp=BOOTSTRAP_SCREEN_SIZE, size=12,),
            ])
        ], bp=BOOTSTRAP_SCREEN_SIZE, size=6,),
        Col([
            Row([
                Col([
                    html.Label('Positions'),
                    dcc.Checklist(
                        id='positions-checklist',
                        options=[
                            {'label': p, 'value': p} for p in ALL_POSITIONS
                        ],
                        values=[p for p in ALL_POSITIONS],
                        labelStyle={'margin': '5px'}
                    ),
                ], bp=BOOTSTRAP_SCREEN_SIZE, size=12,
                ),
                Col([
                    html.Label('Number of Rows', style={'margin': '5px'}),
                    dcc.Input(id='nrows-input', type='number', value=50)
                ], bp=BOOTSTRAP_SCREEN_SIZE, size=12,
                )
            ]),
            Col(
                id='table',
                bp=BOOTSTRAP_SCREEN_SIZE,
                size=12,
            ),
        ], bp=BOOTSTRAP_SCREEN_SIZE, size=6,),
    ]),
    html.Div(id='hidden-data', style={'display': 'none'}),
])

@app.callback(
    Output('table', 'children'),
    [Input('hidden-data', 'children')],
)
def table_callback(jsonified_cleaned_data):
    df = pd.read_json(jsonified_cleaned_data, orient='split')
    header = html.Thead(
        html.Tr([html.Th(col, scope='col') for col in df.columns])
    )
    rows = []
    for i in range(len(df)):
        cells = []
        for j, col in enumerate(df.columns):
            if j == 0:
                cells.append(html.Th(df.iloc[i][col], scope='row'))
            else:
                cells.append(html.Td(df.iloc[i][col]))
        rows.append(html.Tr(cells))
    body = html.Tbody(rows)
    return html.Table([header, body], className='table table-striped')

@app.callback(
    Output('graph_1', 'figure'),
    [Input('hidden-data', 'children')],
)
def graph_1_callback(jsonified_cleaned_data):
    df = pd.read_json(jsonified_cleaned_data, orient='split')
    return {
        'data': [
            {
                'x': sub_df['week_std'],
                'y': sub_df['week_avg'],
                'type': 'scatter',
                'name': position,
                'mode': 'markers',
                'text': sub_df['player'],
                'marker': {'size': 10, 'color': POSITION_COLORS[position]},
            } for position, sub_df in df.groupby('position')
        ],
        'layout': {
            'title': '2017 Weekly Avg. vs Std.',
            'height': '400',
            'font': {'size': 14},
            'hovermode': 'closest',
            'xaxis': {'title': 'Weekly Std.'},
            'yaxis': {'title': 'Weely Avg.'},
        },
    }


@app.callback(
    Output('graph_2', 'figure'),
    [Input('hidden-data', 'children')],
)
def graph_2_callback(jsonified_cleaned_data):
    df = pd.read_json(jsonified_cleaned_data, orient='split')
    return {
        'data': [
            {
                'x': (
                    ALL_POSITIONS.index(position) +
                    np.random.uniform(-0.2,0.2,len(sub_df))
                ),
                'y': sub_df['week_avg'],
                'type': 'scatter',
                'name': position,
                'mode': 'markers',
                'text': sub_df['player'],
                'marker': {'size': 10, 'color': POSITION_COLORS[position]},
            } for position, sub_df in df.groupby('position')
        ],
        'layout': {
            'title': '2017 Weekly Avg. vs Position',
            'height': '400',
            'font': {'size': 14},
            'hovermode': 'closest',
            'xaxis': {
                'title': 'Position',
                'tickvals': [i for i, _ in enumerate(ALL_POSITIONS)],
                'ticktext': ALL_POSITIONS,
            },
            'yaxis': {'title': 'Weely Avg.'},
        },
    }


@app.callback(
    Output('hidden-data', 'children'),
    [Input('positions-checklist', 'values'), Input('nrows-input', 'value')],
)
def hidden_data_callback(positions, max_rows):
    df = get_updated_df(positions, max_rows)
    return df.to_json(orient='split')


if __name__ == '__main__':
    # To make this app publicly available, supply the parameter host='0.0.0.0'.
    # You should also disable debug mode in production.
    app.run_server(debug=True, port=8051)
