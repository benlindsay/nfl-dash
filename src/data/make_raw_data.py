#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# make_raw_data.py
#
# Copyright (c) 2018 Ben Lindsay <benjlindsay@gmail.com>
#

from collections import Counter
from dotenv import find_dotenv, load_dotenv
from pathlib2 import Path
from subprocess import check_output
import click
import logging
import nflgame
import warnings
with warnings.catch_warnings():
    # ignore warnings that are safe to ignore according to
    # https://github.com/ContinuumIO/anaconda-issues/issues/6678
    # #issuecomment-337276215
    warnings.simplefilter("ignore")
    import pandas as pd

from src.scoring import get_player_scoring_dict
from src.scoring import get_team_scoring_dict


@click.command()
@click.argument('year', type=click.INT)
@click.argument('ppr', type=click.BOOL)
def main(year=2017, ppr=True):
    """Compiles player and team stats relevant to fantasy scoring in
    <project_dir>/data/raw/<year>/<year>_week-<week>.csv
    """
    # Update schedule so 2017 data can be used
    python_path = Path(check_output(['which', 'python']).strip())
    update_sched_path = (
        python_path.parents[1] / 'lib' / 'python2.7' / 'site-packages' /
        'nflgame' / 'update_sched.py'
    )
    print(check_output(
        ['python', str(update_sched_path), '--year', str(year)]))

    logger = logging.getLogger(__name__)
    logger.info('setting up csv files')

    project_dir = Path(__file__).resolve().parents[2]
    year_data_dir = project_dir / 'data' / 'raw' / str(year)
    year_data_dir.mkdir(parents=True, exist_ok=True)

    # For every week in the weeks list, grab the player game logs and create a
    # csv file for each week
    weeks = list(range(1, 18))
    for week in weeks:
        df_week = get_player_and_team_data(year, week)
        filename = year_data_dir / '{}_week-{:02d}.csv'.format(year, week)
        df_week.to_csv(filename, index=False)


def get_player_and_team_data(year, week, ppr=True):
    """Returns a dataframe of stats for all teams and players (with nonzero
    useful stats) for a given week in a given season.

    If ppr is True, uses point-per-reception scoring. Otherwise uses 1/2 point
    per reception.
    """
    df = pd.DataFrame()
    defense_two_pt_returns_dict = get_defense_two_pt_returns(year, week)
    player_scoring_dict = get_player_scoring_dict(ppr=ppr)
    team_scoring_dict = get_team_scoring_dict()
    for game in nflgame.games(year, week):
        for team, opp_score in zip([game.home, game.away],
                                   [game.score_away, game.score_home]):
            i_row = len(df)
            team = team
            df.loc[i_row, 'week'] = week
            df.loc[i_row, 'player'] = 'DEFENSE'
            df.loc[i_row, 'team'] = team
            df.loc[i_row, 'position'] = 'DEFENSE'
            for team_stat in team_scoring_dict:
                if team_stat == 'team_defense_two_pt_return':
                    df.loc[i_row, team_stat] = (
                        defense_two_pt_returns_dict['teams'][team]
                    )
                elif team_stat == 'team_points_allowed':
                    df.loc[i_row, team_stat] = opp_score
                else:
                    stat = team_stat.replace('team_', '')
                    df.loc[i_row, team_stat] = get_team_defense_stat(
                        game, team, stat
                    )
    players = nflgame.combine_max_stats(nflgame.games(year, week))
    for player in players:
        i_row = len(df)
        df.loc[i_row, 'week'] = week
        df.loc[i_row, 'player'] = player
        df.loc[i_row, 'team'] = player.team
        df.loc[i_row, 'position'] = player.guess_position
        for stat in player._stats:
            if stat in player_scoring_dict:
                df.loc[i_row, stat] = getattr(player, stat)
    return df


def get_defense_two_pt_returns(year, week):
    """Returns a dictionary of `players` and `teams` Counters, which store the
    number of defensive 2 point returns awarded to any player and team for a
    given week of play. This function is necessary because there don't seem to
    be easy ways to get this stat otherwise.
    """
    defense_two_pt_returns_dict = {
        'players': Counter(),
        'teams': Counter(),
    }
    for game in nflgame.games(year, week):
        home_team, away_team = game.home, game.away
        for play in nflgame.combine_plays([game]):
            if ('DEFENSIVE TWO-POINT ATTEMPT' in str(play) and
                    'ATTEMPT SUCCEEDS' in str(play)):
                # Determine scoring team
                if play.team == home_team:
                    team = away_team
                else:
                    team = home_team
                # Guess scoring player. Can't find any stats for this, but the
                # scoring player is usually listed at the beginning of the
                # sentence before "ATTEMPT SUCCEEDS" in the play description.
                sentences = str(play).split('. ')
                i = -1
                while 'ATTEMPT SUCCEEDS' not in sentences[i+1]:
                    i += 1
                player = sentences[i].split()[0]
                # Add to counters for player and team
                defense_two_pt_returns_dict['players'][player] += 1
                defense_two_pt_returns_dict['teams'][team] += 1
    return defense_two_pt_returns_dict


def get_team_defense_stat(game, team, stat):
    """Returns the count of a particular stat awarded to a team on a given week
    of play.

    Code modified from https://github.com/BurntSushi/nflgame/wiki/Cookbook
    #calculate-number-of-sacks-for-a-team
    Filter part of modification comes from last comment of
    https://github.com/BurntSushi/nflgame/issues/48
    """
    plays = nflgame.combine_plays([game])

    count = 0
    if stat == 'defense_frec':
        for play in plays.filter(defense_frec__gt=0):
            if (play.punting_tot == 0) and (play.kicking_tot == 0):
                # defensive fumble recoveries go to the team that doesn't start
                # with the ball if it's not a punting/kicking play
                if play.team != team:
                    count += getattr(play, stat)
            else:
                # defensive fumble recoveries go to the team that starts with
                # the ball if it's a punting/kicking play
                if play.team == team:
                    count += getattr(play, stat)
    elif stat == 'defense_two_pt_return':
        raise ValueError("defense_two_pt_return should be handled outside of "
                         "get_team_defense_stat()!")
    else:
        for play in plays.filter(team__ne=team):
            count += getattr(play, stat)
    return count


if __name__ == '__main__':

    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
