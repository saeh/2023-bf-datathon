# Params
# B - variance of the performance distribution
B = 1
# G - variance of the score (margin) distribution
G = 2
# BG2 = 2 B^2 + G^2
BG2 = 2*B*B + G*G
# Gaussian Distribution Params
# Mean: Mu
# Variance: S^2
# Precision: Pi = S^-2
# Precision Adjusted Mean: Tau = Pi * Mu

# Imports 
import numpy as np
import pandas as pd
from scipy.stats import norm

def load_data():
  df = pd.read_csv('../data/joined.csv')
  df = df.loc[df.date<'2022-11-20']
  return df.sort_values('date')

def init_ratings(df):
  ratings = {}
  teams = list(df.home_team.unique()) + list(df.away_team.unique())
  for t in set(teams):
    ratings[t] = (25, 8.333)
  return ratings

def make_wide(df):
  wide = df.groupby('idx').apply(lambda x: x.sort_values('margin')[['horse','margin']].values)
  wide = wide.reset_index()
  wide = wide.rename(columns={0:'margin_sorted_runners'})
  return wide

def fetch_params(race_pair,ratings):
  horse_i, m_i = race_pair
  Mu_i,S_i = ratings[horse_i]
  return horse_i,m_i,Mu_i,S_i


# @jit
# def loop_race(race,ratings):
  


def run_ts(df,ratings):
  ro = []
  for match in df.to_dict('rows'):
    win_mat = 0
    Mu_i,S_i = ratings[match['home_team']]
    Mu_j,S_j = ratings[match['away_team']]
    m_i = match['home_score']
    m_j = match['away_score']

    Pi_i_new = S_i**(-2) + 1. / (BG2 + S_j**2)
    Pi_j_new = S_j**(-2) + 1. / (BG2 + S_i**2) 
    Tau_i_new = Mu_i / (S_i**2)  +  ((m_i - m_j) + Mu_j) / (BG2 + S_j**2)
    Tau_j_new = Mu_j / (S_j**2)  +  ((m_j - m_i) + Mu_i) / (BG2 + S_i**2)
    Mu_i_new = Tau_i_new / Pi_i_new
    Mu_j_new = Tau_j_new / Pi_j_new
    S_i_new = (1./Pi_i_new)**0.5
    S_j_new = (1./Pi_j_new)**0.5
    ratings[match['home_team']] = [Mu_i_new, S_i_new]
    ratings[match['away_team']] = [Mu_j_new, S_j_new]

    win_mat = (Mu_j - Mu_i) / (S_i**2 + S_j**2 + 2*B*B)
    match['winp'] = 1-norm.cdf(win_mat)
    match['bsl_h_mu'] = Mu_i
    match['bsl_h_s'] = S_i
    match['bsl_a_mu'] = Mu_j
    match['bsl_a_s'] = S_j

    ro.append(match)

  df2 = pd.DataFrame(ro)

  return df2,ratings


# Load
df = load_data()
ratings = init_ratings(df)

# Run
df2,ratings = run_ts(df,ratings)

df2.to_csv('../data/bsl.csv',index=False)
import json
json.dump(ratings,open('ratings_bsl.json','w'))

