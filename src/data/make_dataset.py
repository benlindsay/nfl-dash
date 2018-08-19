#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# make_dataset.py
#
# Copyright (c) 2018 Ben Lindsay <benjlindsay@gmail.com>

from dotenv import find_dotenv, load_dotenv
from pathlib2 import Path
import click
import logging
import warnings
with warnings.catch_warnings():
    # ignore warnings that are safe to ignore according to
    # https://github.com/ContinuumIO/anaconda-issues/issues/6678
    # #issuecomment-337276215
    warnings.simplefilter("ignore")
    import pandas as pd

from src.scoring import calc_scores
from src.scoring import get_player_scoring_dict
from src.scoring import get_team_scoring_dict


@click.command()
@click.argument('from_season', type=click.INT)
@click.argument('to_season', type=click.INT)
@click.argument('scoring_method', type=click.STRING)
def main(from_season=2009, to_season=2017, scoring_method='nfl.com'):
    """Combine and score data in <project_dir>/data/raw and output to
    <project_dir>/data/processed/scored-data.csv
    """
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')
    project_dir = Path(__file__).resolve().parents[2]
    scores_csv_path = (
        project_dir / 'data' / 'processed' /
        'scores-summary_{}-to-{}.csv'.format(from_season, to_season)
    )
    raw_dir = project_dir / 'data' / 'raw'
    df_list = []
    for season_year in range(from_season, to_season + 1):
        season_dir = raw_dir / str(season_year)
        for csv_file in season_dir.glob('*.csv'):
            df = pd.read_csv(str(csv_file))
            df['season'] = season_year
            df_list.append(df)
    full_df = pd.concat(df_list, sort=False).reset_index(drop=True)
    team_scoring_dict = get_team_scoring_dict()
    player_scoring_dict = get_player_scoring_dict(method=scoring_method)
    full_df = calc_scores(full_df, team_scoring_dict, player_scoring_dict)
    full_df['week'] = full_df[['season', 'week']].apply(
        lambda x: '{}-{:02d}'.format(x[0], x[1]), axis=1
    )

    summary_df = pd.pivot_table(data=full_df, index='player', columns='week', values='total_score').fillna(0)
    week_cols = summary_df.columns
    summary_df['season_total'] = summary_df[week_cols].sum(axis=1)
    summary_df['week_avg'] = summary_df[week_cols].mean(axis=1)
    summary_df['week_std'] = summary_df[week_cols].std(axis=1)
    summary_df = summary_df.sort_values('season_total', ascending=False)
    summary_df = summary_df.join(
        full_df.groupby('player').first()[['team', 'position']]
    )
    summary_df.to_csv(scores_csv_path)


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    main()
