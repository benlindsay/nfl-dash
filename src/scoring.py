#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# scoring.py
#
# Copyright (c) 2018 Ben Lindsay <benjlindsay@gmail.com>


def team_points_allowed_fn(points_allowed):
    """Return fantasy points scored by a defense based on the number of points
    they allowed. Based on point scale found on
    https://fantasydata.com/developers/fantasy-scoring-system/nfl
    """
    if points_allowed == 0:
        return 10
    elif points_allowed < 7:
        return 7
    elif points_allowed < 14:
        return 4
    elif points_allowed < 21:
        return 1
    elif points_allowed < 28:
        return 0
    elif points_allowed < 35:
        return - 1
    else:
        return -4


def get_player_scoring_dict(method='nfl.com'):
    """Returns a dictionary of scoring rules for each individual player stat.
    All stats in this dictionary are part of the nflgame API except for
    defense_two_pt_return. 

    Modified from
      https://github.com/BurntSushi/nflgame/wiki/Cookbook
      #calculate-the-fantasy-score-of-all-players-for-a-week
    """
    if method == 'nfl.com':
        ppr = True
        player_scoring_dict = {
            # OFFENSE
            #   Passing Yards
            'passing_yds': lambda x: x * .04,
            #   Passing Touchdowns
            'passing_tds': lambda x: x * 4,
            #   Interceptions Thrown
            'passing_ints': lambda x: x * -2,
            #   Rushing Yards
            'rushing_yds': lambda x: x * .1,
            #   Rushing Touchdowns
            'rushing_tds': lambda x: x * 6,
            #   Receptions
            'receiving_rec': lambda x: x * 1 if ppr else x * 0.5,
            #   Receiving Yards
            'receiving_yds': lambda x: x * .1,
            #   Receiving Touchdowns
            'receiving_tds': lambda x: x * 6,
            #   Fumbles Recovered for TD
            'fumbles_rec_tds': lambda x: x * 6,
            #   Fumbles Lost
            'fumbles_lost': lambda x: x * -2,
            #   2-point conversions
            'passing_twoptm': lambda x: x * 2,
            'rushing_twoptm': lambda x: x * 2,
            'receiving_twoptm': lambda x: x * 2,
            # KICKING
            #   PAT Made
            'kicking_xpmade': lambda x: x * 1,
            #   FG Made
            'kicking_fgm_yds': lambda x: 5 if x >= 50 else (3 if x > 0 else 0),
            # INDIVIDUAL DEFENSIVE PLAYERS
            #   Blocked Kick (punt, FG, PAT)
            'defense_puntblk': lambda x: x * 1,
            'defense_fgblk': lambda x: x * 1,
            'defense_xpblk': lambda x: x * 1,
            #   Safety
            'defense_safe': lambda x: x * 2,
            #   Def 2-point Return
            'defense_two_pt_return': lambda x: x * 2,  # This is a custom one
        }
    elif method == 'fantasydata.com':
        # The stats in this dictionary match the order and scoring in
        # https://fantasydata.com/developers/fantasy-scoring-system/nfl
        # for individual players.
        ppr = True
        player_scoring_dict = {
            # OFFENSIVE PLAYERS
            #   Passing
            'passing_yds': lambda x: x * .04,
            'passing_tds': lambda x: x * 4,
            'passing_ints': lambda x: x * -2,
            #   Rushing
            'rushing_yds': lambda x: x * .1,
            'rushing_tds': lambda x: x * 6,
            #   Receiving
            'receiving_rec': lambda x: x * 1 if ppr else x * 0.5,
            'receiving_yds': lambda x: x * .1,
            'receiving_tds': lambda x: x * 6,
            #   2-point conversions
            'passing_twoptm': lambda x: x * 2,
            'rushing_twoptm': lambda x: x * 2,
            'receiving_twoptm': lambda x: x * 2,
            'kickret_tds': lambda x: x * 6,
            #   Fumbles
            'fumbles_lost': lambda x: x * -2,
            'fumbles_rec_tds': lambda x: x * 6,
            # INDIVIDUAL DEFENSIVE PLAYERS
            #   Tackles/Hits
            'defense_tkl': lambda x: x * 1,
            'defense_ast': lambda x: x * 0.5,
            'defense_sk': lambda x: x * 2,
            'defense_sk_yds': lambda x: x * .1,
            'defense_tkl_loss': lambda x: x * 1,
            'defense_qbhit': lambda x: x * 1,
            #   Pass Defense
            'defense_pass_def': lambda x: x * 1,
            'defense_int': lambda x: x * 3,
            #   Run Defense
            'defense_ffum': lambda x: x * 3,
            'defense_frec': lambda x: x * 3,
            #   Scoring on Defense
            'defense_tds': lambda x: x * 6,
            'defense_two_pt_return': lambda x: x * 2,  # This is a custom one
            # KICKING
            'kicking_xpmade': lambda x: x * 1,
            'kicking_fgm_yds': lambda x: 5 if x >= 50 else (3 if x > 0 else 0),
        }
    else:
        raise ValueError("{} is not a valid value for `method`!".format(method))
    return player_scoring_dict


def get_team_scoring_dict():
    """Returns a dictionary of scoring rules for each team stat. All stats in
    this dictionary have the `team_` prefix to differentiate team-level stats
    from individual player stats, which have overlapping stat keys. The stat
    keys after the `team_` prefix (i.e. `defense_sk`) are part of the nflgame
    API except for `defense_two_pt_return` and `points_allowed`. The stats in
    this dictionary match the order and scoring in
    https://fantasydata.com/developers/fantasy-scoring-system/nfl for team
    defense/special teams.
    
    It also matches my NFL.com league's rules
    """
    team_scoring_dict = {
        # TEAM DEFENSE / SPECIAL TEAMS
        'team_defense_sk': lambda x: x * 1,
        'team_defense_int': lambda x: x * 2,
        'team_defense_frec': lambda x: x * 2,
        'team_defense_safe': lambda x: x * 2,
        'team_defense_tds': lambda x: x * 6,
        'team_kickret_tds': lambda x: x * 6,
        'team_puntret_tds': lambda x: x * 6,
        'team_defense_two_pt_return': lambda x: x * 2,  # This is a custom one
        'team_points_allowed': lambda x: team_points_allowed_fn(x)
    }
    return team_scoring_dict


def calc_scores(stats_df, team_scoring_dict, player_scoring_dict):
    """Given a dataframe of stats and dictionaries of scoring rules for teams
    and players, return a dataframe with all the original stats and fantasy
    scoring on those stats.
    """
    scores_df = stats_df.copy().fillna(0)
    first_columns = ['season', 'week', 'team', 'position', 'player']
    team_columns = [c for c in scores_df.columns if c.startswith('team_')]
    player_columns = [c for c in scores_df.columns
                      if c not in first_columns and c not in team_columns]
    team_score_columns = [c + '_score' for c in team_columns]
    player_score_columns = [c + '_score' for c in player_columns]
    final_columns_order = (
        first_columns + team_columns + player_columns + team_score_columns +
        player_score_columns + ['total_score']
    )
    for stat in team_scoring_dict:
        print "Computing {}:".format(stat)
        defense_rows = (scores_df['position'] == 'DEFENSE')
        if stat in scores_df.columns:
            scores_df.loc[defense_rows, stat + '_score'] = (
                scores_df.loc[defense_rows, stat].apply(
                    team_scoring_dict[stat]
                )
            )
        else:
            print("Warning: {} not found in stats_df".format(stat))
    for stat in player_scoring_dict:
        print "Computing {}:".format(stat)
        player_rows = (scores_df['position'] != 'DEFENSE')
        if stat in scores_df.columns:
            scores_df.loc[player_rows, stat + '_score'] = (
                scores_df.loc[player_rows, stat].apply(
                    player_scoring_dict[stat]
                )
            )
        else:
            print("Warning: {} not found in stats_df".format(stat))
    scores_df['total_score'] = (
        scores_df[team_score_columns + player_score_columns].sum(axis=1)
    )
    scores_df = scores_df[final_columns_order]
    scores_df['week'] = scores_df['week'].astype(int)
    return scores_df
