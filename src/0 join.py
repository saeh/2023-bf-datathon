import pandas as pd

df = pd.read_csv('../data/results.csv')

# Name Fixes
df.loc[df.home_team=='United States','home_team'] = 'USA'
df.loc[df.away_team=='United States','away_team'] = 'USA'
df.loc[df.home_team=='South Korea','home_team'] = 'Korea Republic'
df.loc[df.away_team=='South Korea','away_team'] = 'Korea Republic'

# Rem Friendlies
print(df.shape)
df = df.loc[df.tournament != 'Friendly']
print(df.shape)

# Pick the good comps only
comps = {'FIFA World Cup',"Confederations Cup", "African Cup of Nations", "Copa América", "UEFA Euro", "AFC Asian Cup"}
mask = [True if i in comps or ' cup' in i.lower() or 'qualification' in i.lower() else False for i in df.tournament ]
df = df.loc[mask]
print(df.shape)


fifa = pd.read_csv('../data/dummy_submission_file.csv')
fifa['date'] = '2022-11-20'
fifa = fifa.loc[:,['date','home_team','away_team']]
df2 = pd.concat([df,fifa],axis=0)
df2.to_csv('../data/joined.csv',index=False)
