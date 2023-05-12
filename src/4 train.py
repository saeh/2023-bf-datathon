import lightgbm as lgb
import pandas as pd
import numpy as np

df = pd.read_csv('../data/target_data.csv')

target = 'target'

features = [
#       'home_ts', 'home_tv', 'home_ts_L1', 'home_tv_L1', 'home_ts_R5', 'home_tv_R5',
#       'away_ts', 'away_tv', 'away_ts_L1', 'away_tv_L1', 'away_ts_R5', 'away_tv_R5',
       'home_goalsFor_L1', 'home_goalsAgainst_L1',
       'home_goals_L1', 'home_rating_L1', 
       'home_result_L1', 'home_home_L1', 'home_goalsFor_R5',
       'home_goalsAgainst_R5', 'home_goals_R5', 'home_rating_R5', 
       'home_result_R5', 'home_home_R5', 
       'away_goalsFor_L1', 'away_goalsAgainst_L1', 'away_goals_L1',
       'away_rating_L1', 'away_result_L1',
       'away_home_L1', 'away_goalsFor_R5', 'away_goalsAgainst_R5',
       'away_goals_R5', 'away_rating_R5', 
       'away_result_R5', 'away_home_R5','neutral', 
       # 'Qatar', 'Senegal', 'Netherlands', 'Ecuador', 'England', 'USA',
       # 'Wales', 'Iran', 'Argentina', 'Mexico', 'Poland', 'Saudi_Arabia',
       # 'Denmark', 'France', 'Tunisia', 'Australia', 'Germany', 'Spain',
       # 'Japan', 'Costa_Rica', 'Morocco', 'Belgium', 'Croatia', 'Canada',
       # 'Switzerland', 'Brazil', 'Cameroon', 'Serbia', 'Uruguay',
       # 'Portugal', 'Korea_Republic', 'Ghana', 
       'home_e_b','away_e_b',
       'bsl_h_mu', 'bsl_h_s', 'bsl_a_mu', 'bsl_a_s', 'winp',
       'bsl2_h_mu', 'bsl2_h_s', 'bsl2_a_mu', 'bsl2_a_s', 'winp2']


cutoff = '2015-01-01'
train = df.loc[df.date<cutoff,:]
test = df.loc[df.date>=cutoff,:]
print(train.shape)
print(test.shape)

params = {
       'max_depth': 2,
       'num_leaves': 15,
       'learning_rate': 0.03,
       'n_estimators': 1000,
       'colsample_bytree': 0.5,
       'reg_alpha': 0.1,
       'reg_lambda': 0.01,
       'silent': True
}

# Training
mod = lgb.LGBMClassifier(**params)
mod.fit(X = train[features].values,y=train.target.values,eval_set = (test[features].values,test.target.values), early_stopping_rounds=50, feature_name=features)

# Predictions
preds = mod.predict_proba(test[features])
preds = pd.DataFrame(preds,columns=['away_win','draw','home_win'])
test = pd.concat([test.reset_index(drop=True),preds],axis=1)

# Evaluate - Log Loss
ll = np.sum(-np.log(test.loc[test.target==0,'away_win'])) + np.sum(-np.log(test.loc[test.target==1,'draw'])) + np.sum(-np.log(test.loc[test.target==2,'home_win']))
ll = ll / test.shape[0]
print(ll)

params['n_estimators'] = mod.best_iteration_

# Final Training
mod2 = lgb.LGBMClassifier(**params)
mod2.fit(X = df[features].values,y=df.target.values,feature_name=features)
mod2.booster_.save_model('mod.txt')
print(ll)






# Calibration Check




