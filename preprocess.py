import pandas as pd

df = pd.read_csv('global_power_plant_database_v_1_3/global_power_plant_database.csv', dtype=object)
df.rename(columns={'gppd_idnr': 'id'}, inplace=True)
df.set_index('id', inplace=True)

print(df.columns)

df.drop(columns=['owner', 'source', 'commissioning_year', 'url', 'geolocation_source', 'wepp_id'], inplace=True)
df = df.loc[:, ~(df.columns.str.startswith('estimated_generation_note_'))]


df.to_csv('global_power_plant_database_adjusted.csv')

print(df.loc[~(df.estimated_generation_gwh_2013.isna() + df.generation_gwh_2013.isna()), :])
