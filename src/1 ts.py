import numpy as np
import pandas as pd
import trueskill._trueskill as ts
from datetime import datetime, timedelta
import json

class Player(object):
  pass

def load_data():
  df = pd.read_csv('../data/joined.csv')
  df.date = pd.to_datetime(df.date)
  df['goals'] = df.home_score + df.away_score
  df['home_rating'] = df.goals - df.home_score
  df['away_rating'] = df.goals - df.away_score
  return df.sort_values('date')

def init_ratings(df):
  teams = set(list(df.home_team.unique()) + list(df.away_team.unique()))
  ratings = {}
  for t in teams:
    ratings[t] = Player()
    ratings[t].skill = (50,8.333)
  return ratings

# Load and Init
df = load_data()
ratings = init_ratings(df)

# Run Updates (pre-comp)
skillsList = []
for match in df.loc[~df.home_score.isna()].to_dict('rows'):
  print(match['date'])
  t1 = ratings[match['home_team']]
  t2 = ratings[match['away_team']]
  skillRow = [t1.skill[0],t1.skill[1],t2.skill[0],t2.skill[1]]
  newTs = ts.adjust_players([t1.skill+(match['home_rating'],),t2.skill+(match['away_rating'],)])
  t1.skill = newTs[0]
  t2.skill = newTs[1]
  skillsList.append(skillRow)
  
skills = pd.DataFrame(skillsList,columns = ['home_s_b','home_v_b','away_s_b','away_v_b'])
df2 = pd.concat([df.loc[~df.home_score.isna()].reset_index(drop=True),skills],axis=1)

# Cut off first ~5k rows while skills adjust
df2 = df2.sort_values('date')
df2 = df2.loc[df2.date >= '1977-01-01',:]


# Save Files
df2.to_csv('../data/ts_data.csv',index=False)
ratingsDict = {i: ratings[i].skill for i in ratings.keys()}
json.dump(ratingsDict,open('ratings.json','w'))

