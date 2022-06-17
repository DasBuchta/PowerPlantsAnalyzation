from flask import Flask, render_template, g
from analysis import *
import pycountry_convert as pcc
import plotly.graph_objects as go
import plotly.express as px
import json
from plotly.utils import PlotlyJSONEncoder


def px_to_json(fig):
    """Change plotly graph to JSON"""
    plot_json = json.dumps(fig, cls=PlotlyJSONEncoder)
    return plot_json


def geo_plotly_graph(lats=None, lons=None, fuels=None, names=None, caps=None, country=None, caps_per=None):
    """PLotly scatter geo graph
    lats, lons: lists of latitudes and longitudes of geo data
    names: name to show
    caps: some numeric data
    country: country in which geodata occurs
    caps_per: additional numeric info (e. g. percentage)"""

    # create plotly graph
    fig = px.scatter_geo(lat=lats,
                         lon=lons,
                         color=fuels,
                         hover_name=names,
                         hover_data=[caps_per],
                         size=caps,
                         labels={'lat': 'Latitude',
                                 'lon': 'Longitude',
                                 'color': 'Primary fuel',
                                 'size': 'Capacity (MW)',
                                 'hover_data_0': 'Percentage of total capacity'}
                         )

    # some adjustments to look of map
    fig.update_geos(
        showcoastlines=True, coastlinecolor="RebeccaPurple",
        showland=True, landcolor="LightGrey",
        showocean=True, oceancolor="LightBlue",
        showlakes=True, lakecolor="LightBlue",
        showrivers=True, rivercolor="LightBlue",
        showcountries=True
    )

    # scope to part of world according to country
    if country == 'United States':
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

    # update labels
    fig.update_layout(
        title=f'Power plants in {country}',
        geo_scope=geoscope,
        width=1000, height=800,
        legend_title_text='Primary fuel',
    )
    return px_to_json(fig)


def plotly_graph(type, x, y, color=None, title="", label_x='x', label_y='y', label_c=None, log_x=False, log_y=False,
                 hidelegend=False, hovermode=None):
    """Returns plotly.express graph in json format
    type: bar, line or scatter
    x, y: axes
    color: data to distinguish by color
    title, label_x, label_y, label_c: title and labels for axes and color legend
    log_x, log_y: logarithmic scales
    hidelegend: used only with color data
    hovermode: adjust hovermode, see: https://plotly.com/python/hover-text-and-formatting/
    """

    labels = {'x': label_x, 'y': label_y}
    if label_c is not None:
        labels['color'] = label_c

    # create graph according to type
    if type == 'bar':
        fig = px.bar(x=x, y=y, color=color, title=title, labels=labels, log_x=log_x, log_y=log_y)
    elif type == 'line':
        fig = px.line(x=x, y=y, color=color, title=title, labels=labels, log_x=log_x, log_y=log_y, markers=True)
    elif type == 'scatter':
        fig = px.scatter(x=x, y=y, color=color, title=title, labels=labels, log_x=log_x, log_y=log_y)
    else:
        raise TypeError(f"{type.capitalize()} graph is not implemented")

    # some axes and layout ajustments
    fig.update_xaxes(type='category')
    if hidelegend:
        fig.update_layout(showlegend=False)
    if hovermode is not None:
        fig.update_layout(hovermode=hovermode)
        # fig.update_traces(hovertemplate=None)

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

    # decide which template to use
    if country[-1] == '1':
        idc += '1'
        country = country[:-1]

    # some basic info about country
    cur = g.db.cursor()
    cur.execute(f"""SELECT count(), primary_fuel, SUM(capacity_mw) FROM powerplants
                    WHERE country_long=? GROUP BY primary_fuel""", (country,))
    pocty = []
    fuely = []
    kapacity = []
    for row in cur:
        pocty.append(row[0])
        fuely.append(row[1])
        kapacity.append(row[2])
    pocet = sum(pocty)
    kapacitA = sum(kapacity)
    kapacity = [round(kap/kapacitA*100, 2) for kap in kapacity]

    # get data to create map
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
    caps_per = [round(cap/kapacitA*100, 2) for cap in caps]

    # create table with different kinds of fuels used in country
    fig_tab = go.Figure(data=[go.Table(header=dict(values=['Primary fuel', 'Number of power plants',
                                                           'Percentage of total capacity'],
                                                   line_color='lightslategray',
                                                   fill_color='lightskyblue'),
                                       cells=dict(values=[fuely, pocty, kapacity],
                                                  line_color='lightgrey',
                                                  fill_color='lightcyan'))
                              ])
    # fig_tab.update_layout(width=500, height=400)

    return render_template(idc+'.html', country=country, pocet=pocet, pocet2=pocet2, ids=ids, iso=iso_alpha_2,
                           map_data=zip(lats, lons, fuels, caps), maxim=round(max(caps), 2),
                           graph=geo_plotly_graph(lats, lons, fuels, names, caps, country_updated, caps_per),
                           fuels_data=px_to_json(fig_tab), max_cap=round(kapacitA, 2))


@app.route('/top10/')
def wat2():
    cur = g.db.cursor()

    # get data for Slovakia to compare with top 10 countries
    cur.execute("""SELECT country_long, SUM(capacity_mw), COUNT(), AVG(capacity_mw), count(distinct primary_fuel)
                            FROM powerplants WHERE country_long='Slovakia' GROUP BY country_long""")
    svk = [row for row in cur][0]

    # function to make bar graph using some info about 10 countries
    def make_fig(query, svk123=1, label_y=''):
        cur.execute(query)
        countries = []
        data = []
        for row in cur:
            countries.append(row[0])
            data.append(row[1])
        countries.append(svk[0])
        data.append(svk[svk123])
        fig = plotly_graph('bar', x=countries, y=data, label_x='Country', label_y=label_y,
                           color=['#636EFA']*10+['#EF553B'], hidelegend=True)
        return fig

    # top 10 countries by capacity_mw
    fig1 = make_fig("""SELECT country_long, SUM(capacity_mw) as capacity_sum
                        FROM powerplants GROUP BY country_long ORDER BY capacity_sum DESC LIMIT 10""",
                    svk123=1, label_y='Total capacity (MW)')

    # top 10 countries by number of power plants
    fig2 = make_fig("""SELECT country_long, count() as pocet
                        FROM powerplants GROUP BY country_long ORDER BY pocet DESC LIMIT 10""",
                    svk123=2, label_y='Number of power plants')

    # top 10 countries by average capacity_mw
    fig3 = make_fig("""SELECT country_long, AVG(capacity_mw) as average
                        FROM powerplants GROUP BY country_long ORDER BY average DESC LIMIT 10""",
                    svk123=3, label_y='Average capacity (MW)')

    # top 10 countries by number of different kinds of power plants
    fig4 = make_fig("""SELECT country_long, count(distinct primary_fuel) as unique_ones
                    FROM powerplants GROUP BY country_long ORDER BY unique_ones DESC LIMIT 10""",
                    svk123=4, label_y='Number of different kinds')

    return render_template('top10.html', fig1=fig1, fig2=fig2, fig3=fig3, fig4=fig4)


@app.route('/')
def home():
    cur = g.db.cursor()
    cur.execute(f"SELECT country_long FROM powerplants GROUP BY country_long")
    names = [row[0] for row in cur]
    # print(names)

    # power plant with maximum capacity_mw
    cur.execute(f"""SELECT id, country_long, name, capacity_mw, primary_fuel 
                    FROM powerplants ORDER BY capacity_mw DESC LIMIT 1""")
    max_cap = [row for row in cur][0]
    max_cap = f"{max_cap[2]} in {max_cap[1]} - {max_cap[4]} power plant, capacity (MW): {max_cap[3]}"

    # create bar plot for fuels data
    def bar_plot(query, title='', label_x='', label_y=''):
        cur.execute(query)

        data = [row for row in cur]  # load output from query to list
        x_data = [row[0] for row in data]
        y_data = [row[1] for row in data]

        fig = plotly_graph('bar', x=x_data, y=y_data, title=title, label_x=label_x, label_y=label_y, log_y=True)
        return fig

    fig1 = bar_plot("""SELECT primary_fuel, SUM(capacity_mw) as capacity_sum
                        FROM powerplants GROUP BY primary_fuel ORDER BY capacity_sum DESC""",
                    title='Total capacity of different kinds of power plants',
                    label_x='Type of power plant', label_y='Total capacity (MW)')
    fig2 = bar_plot("""SELECT primary_fuel, COUNT() as pocet
                        FROM powerplants GROUP BY primary_fuel ORDER BY pocet DESC""",
                    title='Number of different kinds of power plants',
                    label_x='Type of power plant', label_y='Number of power plants')
    fig3 = bar_plot("""SELECT primary_fuel, AVG(capacity_mw) as capacity_avg
                        FROM powerplants GROUP BY primary_fuel ORDER BY capacity_avg DESC""",
                    title='Performance of different kinds of power plants',
                    label_x='Type of power plant', label_y='Average capacity (MW)')

    # scatter plot using generated energy data
    def year_plot(data, category, log_y1=False, log_y2=False, label_y='', label_c=''):
        caps_rep = []
        for i in range(0, 7):
            caps_rep.extend([row[i] for row in data])
        caps_est = []
        for i in range(7, 12):
            caps_est.extend([row[i] for row in data])

        # print(caps_rep)
        years_rep = sorted([2013, 2014, 2015, 2016, 2017, 2018, 2019] * len(category))
        years_est = sorted([2013, 2014, 2015, 2016, 2017] * len(category))

        fig_rep = plotly_graph('line', x=years_rep, y=caps_rep, color=category * 7, log_y=log_y1,
                            title='Change of generated energy over years (reported)', label_x='Year',
                            label_y=label_y, label_c=label_c, hovermode="x")

        fig_est = plotly_graph('line', x=years_est, y=caps_est, color=category * 5, log_y=log_y2,
                            title='Change of generated energy over years (estimated)', label_x='Year',
                            label_y=label_y, label_c=label_c, hovermode="x")

        return fig_rep, fig_est

    # compare generation of electricity by different fuels
    cur.execute("""SELECT primary_fuel, sum(generation_gwh_2013), sum(generation_gwh_2014),
                    sum(generation_gwh_2015), sum(generation_gwh_2016), sum(generation_gwh_2017), 
                    sum(generation_gwh_2018), sum(generation_gwh_2019), sum(estimated_generation_gwh_2013), 
                    sum(estimated_generation_gwh_2014), sum(estimated_generation_gwh_2015), 
                    sum(estimated_generation_gwh_2016), sum(estimated_generation_gwh_2017),
                    avg(generation_gwh_2013), avg(generation_gwh_2014),
                    avg(generation_gwh_2015), avg(generation_gwh_2016), avg(generation_gwh_2017), 
                    avg(generation_gwh_2018), avg(generation_gwh_2019), avg(estimated_generation_gwh_2013), 
                    avg(estimated_generation_gwh_2014), avg(estimated_generation_gwh_2015), 
                    avg(estimated_generation_gwh_2016), avg(estimated_generation_gwh_2017), sum(capacity_mw)
                    FROM powerplants GROUP BY primary_fuel""")

    data2 = [row for row in cur]  # load output from query to list
    total = sum(row[-1] for row in data2)  # total capacity
    fuels = [row[0] for row in data2]

    fig4, fig5 = year_plot([row[1:13] for row in data2], fuels, label_y='Generated energy (GWh)',
                           label_c='Type of power plant')

    fig6, fig7 = year_plot([row[13:25] for row in data2], fuels, label_y='Average generated energy (GWh)',
                           label_c='Type of power plant')

    # compare generation of electricity by different countries
    cur.execute("""SELECT country_long, sum(generation_gwh_2013), sum(generation_gwh_2014),
                    sum(generation_gwh_2015), sum(generation_gwh_2016), sum(generation_gwh_2017), 
                    sum(generation_gwh_2018), sum(generation_gwh_2019), sum(estimated_generation_gwh_2013), 
                    sum(estimated_generation_gwh_2014), sum(estimated_generation_gwh_2015), 
                    sum(estimated_generation_gwh_2016), sum(estimated_generation_gwh_2017)
                    FROM powerplants GROUP BY country_long""")

    data3 = [row for row in cur]  # load output from query to list
    countries = [row[0] for row in data3]

    fig8, fig9 = year_plot([row[1:13] for row in data3], countries, label_y='Generated energy (GWh)',
                           label_c='Country')




    return render_template('main.html', countries=names, graph1=fig1, graph2=fig2, graph3=fig3, total=round(total),
                           graph4=fig4, graph5=fig5, graph6=fig6, graph7=fig7, graph8=fig8, graph9=fig9,
                           plotlies=[f'plotly{i}' for i in range(1, 10)], max_cap=max_cap)
