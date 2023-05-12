import pandas as pd

df = pd.read_csv('../data/fe_data.csv')

df['target'] = (df.home_goals > df.away_goals).astype(int) - (df.away_goals > df.home_goals).astype(int) + 1

df.to_csv('../data/target_data.csv',index=False)
