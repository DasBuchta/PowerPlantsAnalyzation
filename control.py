import pandas as pd
import numpy as np
from netCDF4 import Dataset
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import plotly.io as pio


pio.renderers.default = "notebook"

df = pd.read_csv('global_power_plant_database_v_1_3/global_power_plant_database.csv', dtype=object)
df.rename(columns={'gppd_idnr': 'id'}, inplace=True)
df.set_index('id', inplace=True)

df2 = Dataset('GPED_All_emi_CO2_2010.0.1x0.1_annually.nc', mode='r')
lon = df2.variables['lon'][:].astype('float64').round(2)
lat = df2.variables['lat'][:].astype('float64').round(2)
emi = df2.variables['emi_co2'][:].astype('float64')
df2.close()

emi_coords = np.array(np.meshgrid(lat, lon)).T.reshape(-1, 2)  # https://stackoverflow.com/questions/1208118/using-numpy-to-build-an-array-of-all-combinations-of-two-arrays/35608701#35608701
df2 = pd.DataFrame(emi, index=lat, columns=lon)

# a = [round(float(l),2)==32.35 for l in lat if 32.35>l.round(2)>32.34999]
# ds = xr.open_dataset('GPED_All_emi_CO2_2010.0.1x0.1_annually.nc')
# df = ds.to_dataframe()

# plt.plot(ds['lat'], ds['lon'])
# ds.plot.scatter('lon', 'lat', c=ds['emi_co2'])
# plt.show()


fig = go.Figure(go.Densitymapbox(lat=df2.index, lon=df2.columns, z=df2.values,
                                 radius=10))
fig.update_layout(mapbox_style="stamen-terrain", mapbox_center_lon=180)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()
