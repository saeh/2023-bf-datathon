import pandas as pd
from sklearn.metrics import log_loss

preds = pd.read_csv('data/elo-ml-tom_submission_file.csv')
results = pd.read_csv('data/results_file.csv')

full = preds.merge(results)
full = full.loc[~full.home_team_result.isna()]
print(full)

ll = (log_loss(full.home_team_result,full.home_team_prob) + log_loss(full.draw_result,full.draw_prob) + log_loss(full.away_team_result,full.away_team_prob))/3
print(ll)
