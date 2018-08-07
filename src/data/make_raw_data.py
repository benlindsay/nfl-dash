#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# make_raw_data.py
# 
# Copyright (c) 2018 Ben Lindsay <benjlindsay@gmail.com>

import click
import logging
import nflgame
import pandas as pd
from glob import glob
from pathlib2 import Path
from dotenv import find_dotenv, load_dotenv
from subprocess import check_output


@click.command()
@click.argument('year', type=click.INT)
def main(year):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    # Update schedule so 2017 data can be used
    python_path = Path(check_output(['which', 'python']).strip())
    update_sched_path = (
        python_path.parents[1] / 'lib' / 'python2.7' / 'site-packages' /
        'nflgame' / 'update_sched.py'
    )
    print(check_output(['python', str(update_sched_path), '--year', str(year)]))

    logger = logging.getLogger(__name__)
    logger.info('setting up csv files')

    project_dir = Path(__file__).resolve().parents[2]
    year_data_dir = project_dir / 'data' / 'raw' / str(year)
    year_data_dir.mkdir(parents=True, exist_ok=True)

    # For every week in the weeks list, grab the player game logs and create a
    # csv file for each week
    weeks = list(range(1, 18))
    for week in weeks:
        filename = year_data_dir / '{}_week-{:02d}.csv'.format(year, week)
        try:
            nflgame.combine(nflgame.games(year, week=week)).csv(str(filename))
        except TypeError:
            print("Failed on week {}".format(week))

    df_list = []
    glob_str = str(year_data_dir / '{}_week-*.csv'.format(year))
    for f in sorted(glob(glob_str)):
        df_list.append(pd.read_csv(f))
    df = pd.concat(df_list)
    df.to_csv(str(year_data_dir / '{}.csv'.format(year)), index=False)


if __name__ == '__main__':

    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
