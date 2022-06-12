from flask import Flask, render_template, g
from analysis import *
import pycountry_convert as pcc
import plotly.graph_objects as go
import plotly.express as px
import json
from plotly.utils import PlotlyJSONEncoder
import seaborn as sns
import numpy as np


def px_to_json(fig):
    plot_json = json.dumps(fig, cls=PlotlyJSONEncoder)
    return plot_json


def geo_plotly_graph(lats=None, lons=None, fuels=None, names=None, caps=None, country=None):
    fig = px.scatter_geo(lat=lats,
                         lon=lons,
                         color=fuels,
                         hover_name=names,
                         size=caps,
                         labels={'lat': 'Latitude',
                                 'lon': 'Longitude',
                                 'color': 'Primary fuel',
                                 'size': 'Capacity (MW)', }
                         )
    # plotting_data = {fuel: np.array([np.array((lats[i], lons[i]), dtype='float64') for i
    #                                  in range(len(lats)) if fuels[i] == fuel]) for fuel in fuels}
    # cols = sns.color_palette('muted', len(fuels))
    # colors = {fuels[i]: f"hsl{cols[i]}" for i in range(len(fuels))}
    # fig = go.Figure()
    # for f in plotting_data:
    #     fig.add_trace(go.Scattergeo(
    #         lat=plotting_data[f][:, 0],
    #         lon=plotting_data[f][:, 1],
    #         text=f,
    #         mode='markers',
    #         name=f,
    #
    #     )
    #     )
    #
    fig.update_geos(
        showcoastlines=True, coastlinecolor="RebeccaPurple",
        showland=True, landcolor="LightGrey",
        showocean=True, oceancolor="LightBlue",
        showlakes=True, lakecolor="LightBlue",
        showrivers=True, rivercolor="LightBlue",
        showcountries=True
    )
    if country == 'United States of America':
        geoscope = 'usa'
    elif country == 'Russia' or country == 'Antarctica':
        geoscope = 'world'
    elif country == 'Western Sahara':
        geoscope = 'africa'
    else:
        geoscope = pcc.convert_continent_code_to_continent_name(
            pcc.country_alpha2_to_continent_code(pcc.country_name_to_country_alpha2(country))).lower()
    if geoscope == 'oceania':
        geoscope = 'world'
    fig.update_layout(
        title=f'Power plants in {country}',
        geo_scope=geoscope,
        width=1000, height=800,
        legend_title_text='Primary fuel',
    )
    return px_to_json(fig)


def plotly_graph(type, x, y, color=None, title="", label_x='x', label_y='y', label_c=None, log_x=False, log_y=False):
    """Returns plotly.express graph in json format
    type: bar, line or scatter"""

    labels = {'x': label_x, 'y': label_y}
    if label_c is not None:
        labels['color'] = label_c

    if type == 'bar':
        fig = px.bar(x=x, y=y, color=color, title=title, labels=labels, log_x=log_x, log_y=log_y)
    elif type == 'line':
        fig = px.line(x=x, y=y, color=color, title=title, labels=labels, log_x=log_x, log_y=log_y, markers=True)
    elif type == 'scatter':
        fig = px.scatter(x=x, y=y, color=color, title=title, labels=labels, log_x=log_x, log_y=log_y)
    else:
        raise TypeError(f"{type.capitalize()} graph is not implemented")

    return px_to_json(fig)


app = Flask(__name__)


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route('/<country>/')
def wat(country):
    idc = 'country'
    if country[-1] == '1':
        idc += '1'
        country = country[:-1]

    cur = g.db.cursor()
    cur.execute(f"""SELECT count() FROM powerplants WHERE country_long=?""", (country,))
    pocet = [row[0] for row in cur][0]
    cur.execute(f"""SELECT id, country, latitude, longitude, primary_fuel, capacity_mw, name 
    FROM powerplants WHERE country_long=? ORDER BY capacity_mw DESC LIMIT 100""", (country,))
    data = [row for row in cur]
    ids = [row[0] for row in data]
    pocet2 = len(ids)
    if country == 'Kosovo':
        country_updated = 'Serbia'
    else:
        country_updated = pcc.map_country_alpha3_to_country_name()[data[0][1]]
    iso_alpha_2 = pcc.country_name_to_country_alpha2(country_updated)
    lats = [row[2] for row in data]
    lons = [row[3] for row in data]
    fuels = [row[4] for row in data]
    caps = [round(row[5], 2) for row in data]
    names = [row[6] for row in data]

    return render_template(idc+'.html', country=country, pocet=pocet, pocet2=pocet2, ids=ids, iso=iso_alpha_2,
                           map_data=zip(lats, lons, fuels, caps), maxim=max(caps),
                           graph=geo_plotly_graph(lats, lons, fuels, names, caps, country_updated))


@app.route('/top10/')
def wat2():
    cur = g.db.cursor()

    cur.execute("""SELECT country_long, SUM(capacity_mw) as capacity_sum
                        FROM powerplants GROUP BY country_long ORDER BY capacity_sum DESC LIMIT 10""")
    countries1 = []
    data1 = []
    for row in cur:
        countries1.append(row[0])
        data1.append(row[1])
    fig1 = plotly_graph('bar', x=countries1, y=data1, label_x='Country', label_y='Total capacity (MW)')

    cur.execute("""SELECT country_long, count() as pocet
                        FROM powerplants GROUP BY country_long ORDER BY pocet DESC LIMIT 10""")
    countries2 = []
    data2 = []
    for row in cur:
        countries2.append(row[0])
        data2.append(row[1])
    fig2 = plotly_graph('bar', x=countries2, y=data2, label_x='Country', label_y='Number of power plants')

    cur.execute("""SELECT country_long, AVG(capacity_mw) as average
                        FROM powerplants GROUP BY country_long ORDER BY average DESC LIMIT 10""")
    countries3 = []
    data3 = []
    for row in cur:
        countries3.append(row[0])
        data3.append(row[1])
    fig3 = plotly_graph('bar', x=countries3, y=data3, label_x='Country', label_y='Average capacity (MW)')

    return render_template('top10.html', fig1=fig1, fig2=fig2, fig3=fig3)


@app.route('/')
def home():
    cur = g.db.cursor()
    cur.execute(f"SELECT country_long FROM powerplants GROUP BY country_long")
    # countries = [row[0] for row in cur]
    names = [row[0] for row in cur]
    # print(names)

    cur.execute("""SELECT AVG(capacity_mw) as average, primary_fuel, sum(generation_gwh_2013), sum(generation_gwh_2014),
                    sum(generation_gwh_2015), sum(generation_gwh_2016), sum(generation_gwh_2017), 
                    sum(generation_gwh_2018), sum(generation_gwh_2019), sum(estimated_generation_gwh_2013), 
                    sum(estimated_generation_gwh_2014), sum(estimated_generation_gwh_2015), 
                    sum(estimated_generation_gwh_2016), sum(estimated_generation_gwh_2017)
                    FROM powerplants GROUP BY primary_fuel ORDER BY average DESC""")

    data = [row for row in cur]
    vykon = [row[0] for row in data]
    fuels = [row[1] for row in data]

    fig1 = plotly_graph('bar', x=fuels, y=vykon, title='Performance of different kinds of power plants',
                        label_x='Type of power plant', label_y='Average capacity (MW)')

    caps_rep = []
    for i in range(2, 9):
        caps_rep.extend([row[i] for row in data])
    caps_est = []
    for i in range(9, 14):
        caps_est.extend([row[i] for row in data])

    # print(caps_rep)
    years_rep = sorted([2013, 2014, 2015, 2016, 2017, 2018, 2019]*len(fuels))
    years_est = sorted([2013, 2014, 2015, 2016, 2017]*len(fuels))

    fig2 = plotly_graph('line', x=years_rep, y=caps_rep, color=fuels*7, log_y=True,
                        title='Change of generated energy over years (reported)', label_x='Year',
                        label_y='Generated energy (MWh)', label_c='Type of power plant')

    fig3 = plotly_graph('line', x=years_est, y=caps_est, color=fuels*5, log_y=True,
                        title='Change of generated energy over years (estimated)', label_x='Year',
                        label_y='Generated energy (MWh)', label_c='Type of power plant')

    return render_template('main.html', countries=names, graph1=fig1, graph2=fig2, graph3=fig3)
