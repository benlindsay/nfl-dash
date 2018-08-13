#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# make_dataset.py
#
# Copyright (c) 2018 Ben Lindsay <benjlindsay@gmail.com>

from dotenv import find_dotenv, load_dotenv
from pathlib2 import Path
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


def main():
    """Combine and score data in <project_dir>/data/raw and output to
    <project_dir>/data/processed/scored-data.csv
    """
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')
    project_dir = Path(__file__).resolve().parents[2]
    scores_csv = project_dir / 'data' / 'processed' / 'scored-data.csv'
    raw_dir = project_dir / 'data' / 'raw'
    df_list = []
    for season_dir in raw_dir.glob('????'):
        season_year = int(season_dir.name)
        for csv_file in season_dir.glob('*.csv'):
            df = pd.read_csv(str(csv_file))
            df['season'] = season_year
            df_list.append(df)
    full_df = pd.concat(df_list, sort=False).reset_index(drop=True)
    team_scoring_dict = get_team_scoring_dict()
    player_scoring_dict = get_player_scoring_dict(ppr=True)
    full_df = calc_scores(full_df, team_scoring_dict, player_scoring_dict)
    full_df.to_csv(scores_csv, index=False)


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    main()
