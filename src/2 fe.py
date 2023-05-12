import pandas as pd
import json
from scipy.stats import norm

df = pd.read_csv('../data/ts_data.csv')

# Reduce to one team per row
home = df.loc[:,['date','home_team','away_team','home_score','away_score','tournament','goals','home_rating','home_s_b','home_v_b']]
home.columns = ['date','team','opponent','goalsFor','goalsAgainst','tournament','goals','rating','ts','tv']
home['result'] = home.goalsFor - home.goalsAgainst
home.loc[home.result>1,'result'] = 1
home.loc[home.result<-1,'result'] = -1
home['home'] = 1

away = df.loc[:,['date','away_team','home_team','away_score','home_score','tournament','goals','away_rating','away_s_b','away_v_b']]
away.columns = ['date','team','opponent','goalsFor','goalsAgainst','tournament','goals','rating','ts','tv']
away['result'] = away.goalsFor - away.goalsAgainst
away.loc[away.result>1,'result'] = 1
away.loc[away.result<-1,'result'] = -1
away['home'] = 0

# all teams
df2 = pd.concat([home,away],axis=0)

# # De Dupe (multi games one day?)
df2 = df2.groupby(['date','team','opponent']).mean().reset_index()
df2 = df2.sort_values('date')

# Add latest point - one row per team
teams = df2.team.unique()
dfNew = pd.DataFrame(teams,columns=['team'])
dfNew['date'] = '2022-11-20'
dfNew = dfNew.loc[:,['date','team']]
df2 = pd.concat([df2,dfNew],axis=0)

# rolling results
df2 = df2.set_index(['date','opponent'])
rolling = df2.groupby('team').rolling(5,closed='left').mean().reset_index()
rolling.columns = ['team','date','opponent','goalsFor_R5','goalsAgainst_R5', 'goals_R5', 'rating_R5', 'ts_R5', 'tv_R5', 'result_R5', 'home_R5']
df2 = df2.reset_index()
df3 = df2.merge(rolling)
df3 = df3.sort_values('date')

# lag results
df3 = df3.set_index(['date','opponent'])
lag = df3.groupby('team')[['goalsFor','goalsAgainst','goals','rating','ts','tv','result','home']].shift(1)
lag.columns = ['goalsFor_L1','goalsAgainst_L1', 'goals_L1', 'rating_L1', 'ts_L1', 'tv_L1', 'result_L1', 'home_L1']
df4 = pd.concat([df3,lag],axis=1).reset_index()

# Change back to one row per match
df4.loc[df4.date=='2022-11-20','home'] = 1
home = df4.loc[df4.home==1,['date', 'opponent', 'team', 'goalsFor', 'goalsAgainst', 'goals',
       'ts', 'tv', 'goalsFor_L1', 'goalsAgainst_L1', 'goals_L1', 'rating_L1', 'ts_L1', 'tv_L1',
       'result_L1', 'home_L1', 'goalsFor_R5', 'goalsAgainst_R5', 'goals_R5', 'rating_R5', 
       'ts_R5', 'tv_R5', 'result_R5', 'home_R5']]

home.columns = ['date','away_team','home_team','home_goals','away_goals','goals',
       'home_ts','home_tv', 'home_goalsFor_L1', 'home_goalsAgainst_L1', 'home_goals_L1', 'home_rating_L1', 'home_ts_L1', 'home_tv_L1',
       'home_result_L1', 'home_home_L1', 'home_goalsFor_R5', 'home_goalsAgainst_R5', 'home_goals_R5', 'home_rating_R5', 
       'home_ts_R5', 'home_tv_R5', 'home_result_R5', 'home_home_R5']

# Change back to one row per match
df4.loc[df4.date=='2022-11-20','home'] = 0
away = df4.loc[df4.home==0,['date', 'opponent', 'team', 'goalsFor', 'goalsAgainst', 'goals',
       'ts', 'tv', 'goalsFor_L1', 'goalsAgainst_L1', 'goals_L1', 'rating_L1', 'ts_L1', 'tv_L1',
       'result_L1', 'home_L1', 'goalsFor_R5', 'goalsAgainst_R5', 'goals_R5', 'rating_R5', 
       'ts_R5', 'tv_R5', 'result_R5', 'home_R5']]

away.columns = ['date','home_team','away_team','away_goals','home_goals','goals',
       'away_ts','away_tv', 'away_goalsFor_L1', 'away_goalsAgainst_L1', 'away_goals_L1', 'away_rating_L1', 'away_ts_L1', 'away_tv_L1',
       'away_result_L1', 'away_home_L1', 'away_goalsFor_R5', 'away_goalsAgainst_R5', 'away_goals_R5', 'away_rating_R5', 
       'away_ts_R5', 'away_tv_R5', 'away_result_R5', 'away_home_R5']


# Add Neutral column back... important
df5 = home.merge(away)
print(df5.shape)
df5 = df5.merge(df.loc[:,['date','home_team','away_team','neutral']])
df5.neutral = df5.neutral.astype(int)
print(df5.shape)


# Add indicator variable for WC team
teams = ['Qatar', 'Senegal', 'Netherlands', 'Ecuador', 'England', 'USA',
       'Wales', 'Iran', 'Argentina', 'Mexico', 'Poland', 'Saudi Arabia',
       'Denmark', 'France', 'Tunisia', 'Australia', 'Germany', 'Spain',
       'Japan', 'Costa Rica', 'Morocco', 'Belgium', 'Croatia', 'Canada',
       'Switzerland', 'Brazil', 'Cameroon', 'Serbia', 'Uruguay',
       'Portugal', 'Korea Republic', 'Ghana']

for t in teams:
       df5[t.replace(' ','_')] = (df5.home_team == t).astype(int) + (df5.away_team == t).astype(int)


# Join ELO hist
elo = pd.read_csv('../data/elo_hist.csv')
elo['home_e_b'] = elo.home_elo - elo.home_update
elo['away_e_b'] = elo.away_elo - elo.away_update
elo2 = elo.loc[:,['home_team','away_team','date','home_e_b','away_e_b']]
df5 = df5.merge(elo2)

# Join BSL hist
bsl = pd.read_csv('../data/bsl.csv')
bsl2 = bsl.loc[:,['date','home_team','away_team','winp','bsl_h_mu','bsl_h_s','bsl_a_mu','bsl_a_s']]
df5 = df5.merge(bsl2)

# Join BSL2 hist
bsl3 = pd.read_csv('../data/bsl2.csv')
bsl4 = bsl3.loc[:,['date','home_team','away_team','winp2','bsl2_h_mu','bsl2_h_s','bsl2_a_mu','bsl2_a_s']]
df5 = df5.merge(bsl4)



# Save to File for training
df5.to_csv('../data/fe_data.csv',index=False)








# Get Fifa Matchups
fifa = pd.read_csv('../data/dummy_submission_file.csv')
fifa = fifa.merge(home.loc[home.date=='2022-11-20',['date', 'home_team', 'home_goals', 'away_goals', 'goals',
       'home_ts', 'home_tv', 'home_goalsFor_L1', 'home_goalsAgainst_L1',
       'home_goals_L1', 'home_rating_L1', 'home_ts_L1', 'home_tv_L1',
       'home_result_L1', 'home_home_L1', 'home_goalsFor_R5',
       'home_goalsAgainst_R5', 'home_goals_R5', 'home_rating_R5', 'home_ts_R5',
       'home_tv_R5', 'home_result_R5', 'home_home_R5']], how='left', on = 'home_team')

fifa = fifa.merge(away.loc[away.date=='2022-11-20',['date', 'away_team',
       'away_ts', 'away_tv', 'away_goalsFor_L1', 'away_goalsAgainst_L1',
       'away_goals_L1', 'away_rating_L1', 'away_ts_L1', 'away_tv_L1',
       'away_result_L1', 'away_home_L1', 'away_goalsFor_R5',
       'away_goalsAgainst_R5', 'away_goals_R5', 'away_rating_R5', 'away_ts_R5',
       'away_tv_R5', 'away_result_R5', 'away_home_R5']], how='left', on = 'away_team')

# Load Ratings
ratings = json.load(open('ratings.json','r'))

fifa['home_ts'] = [ratings[i][0] for i in fifa.home_team]
fifa['home_tv'] = [ratings[i][1] for i in fifa.home_team]

fifa['away_ts'] = [ratings[i][0] for i in fifa.away_team]
fifa['away_tv'] = [ratings[i][1] for i in fifa.away_team]

# Add Neutral
fifa['neutral'] = 1

for t in teams:
       fifa[t.replace(' ','_')] = (fifa.home_team == t).astype(int) + (fifa.away_team == t).astype(int)


fifa = fifa.reset_index()

# Load ELO
elo = pd.read_csv('../data/elos.csv')
elo = elo.loc[:,['team','elo']]
elo.columns = ['home_team','home_e_b']
fifa = fifa.merge(elo)
elo.columns = ['away_team','away_e_b']
fifa = fifa.merge(elo)

fifa = fifa.sort_values('index')

# Load BSL
ratings_bsl = json.load(open('ratings_bsl.json','r'))
fifa['bsl_h_mu'] = [ratings_bsl[i][0] for i in fifa.home_team]
fifa['bsl_h_s'] = [ratings_bsl[i][1] for i in fifa.home_team]
fifa['bsl_a_mu'] = [ratings_bsl[i][0] for i in fifa.away_team]
fifa['bsl_a_s'] = [ratings_bsl[i][1] for i in fifa.away_team]

B = 1
fifa['winp'] = [ 1-norm.cdf((fifa.iloc[i].bsl_a_mu - fifa.iloc[i].bsl_h_mu) / (fifa.iloc[i].bsl_h_s**2 + fifa.iloc[i].bsl_a_s**2 + 2*B*B)) for i in range(fifa.shape[0])]

# Load BSL2
ratings_bsl2 = json.load(open('ratings_bsl2.json','r'))
fifa['bsl2_h_mu'] = [ratings_bsl2[i][0] for i in fifa.home_team]
fifa['bsl2_h_s'] = [ratings_bsl2[i][1] for i in fifa.home_team]
fifa['bsl2_a_mu'] = [ratings_bsl2[i][0] for i in fifa.away_team]
fifa['bsl2_a_s'] = [ratings_bsl2[i][1] for i in fifa.away_team]

B = 1
fifa['winp2'] = [ 1-norm.cdf((fifa.iloc[i].bsl2_a_mu - fifa.iloc[i].bsl2_h_mu) / (fifa.iloc[i].bsl2_h_s**2 + fifa.iloc[i].bsl2_a_s**2 + 2*B*B)) for i in range(fifa.shape[0])]





# Save to File
fifa.to_csv('../data/fifa.csv',index=False)
