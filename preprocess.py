#%%
import pandas as pd

df = pd.read_csv('global_power_plant_database_v_1_3/global_power_plant_database.csv', dtype=object)
df.rename(columns={'gppd_idnr': 'id'}, inplace=True)
df.set_index('id', inplace=True)

print(df.columns)


#%%
# Remove columns I will not use, so they do not take space in database
df.drop(columns=['owner', 'source', 'commissioning_year', 'url', 'geolocation_source', 'wepp_id',
                 'year_of_capacity_data', 'generation_data_source'], inplace=True)
df = df.loc[:, ~(df.columns.str.startswith('estimated_generation_note_'))]


df.to_csv('global_power_plant_database_adjusted.csv', header=False)


#%%
print("Number of rows and columns of database: ", df.shape)
#%%
# only rows with reported and also estimated generation of electricity
filtered = (df.loc[~(df.estimated_generation_gwh_2013.isna() + df.generation_gwh_2013.isna()), :])

#%%
diffs2013 = (filtered['generation_gwh_2013'].astype('float64') - filtered['estimated_generation_gwh_2013'].astype('float64'))

print(filtered.iloc[diffs2013.argmin(), :])
print(filtered.iloc[diffs2013.argmax(), :])

#%%
