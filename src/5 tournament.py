import pandas as pd
import lightgbm as lgb

mod = lgb.Booster(model_file='mod.txt')

fifa = pd.read_csv('../data/fifa.csv')
preds = mod.predict(fifa[mod.feature_name()].values)

fifa.home_team_prob = preds[:,2]
fifa.draw_prob = preds[:,1]
fifa.away_team_prob = preds[:,0]


fifa = fifa.loc[:,['home_team', 'away_team', 'stage', 'home_team_prob', 'draw_prob', 'away_team_prob']]

# Normalise
fifa.loc[fifa.stage=='Knockout','draw_prob']=0
fifa['prob_sum'] = fifa.home_team_prob + fifa.draw_prob + fifa.away_team_prob
fifa.home_team_prob = fifa.home_team_prob / fifa.prob_sum
fifa.draw_prob = fifa.draw_prob / fifa.prob_sum
fifa.away_team_prob = fifa.away_team_prob / fifa.prob_sum
fifa = fifa.drop('prob_sum',axis=1)

fifa.to_csv('../data/elo-ml-tom_submission_file.csv',index=False)
