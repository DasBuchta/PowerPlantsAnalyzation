CREATE TABLE IF NOT EXISTS powerplants (
id TEXT, country TEXT, country_long TEXT, name TEXT, capacity_mw REAL, latitude REAL, longitude REAL,
primary_fuel TEXT, other_fuel1 TEXT, other_fuel2 TEXT, other_fuel3 TEXT, generation_gwh_2013 REAL,
generation_gwh_2014 REAL, generation_gwh_2015 REAL, generation_gwh_2016 REAL, generation_gwh_2017 REAL,
generation_gwh_2018 REAL, generation_gwh_2019 REAL, estimated_generation_gwh_2013 REAL,
estimated_generation_gwh_2014 REAL, estimated_generation_gwh_2015 REAL, estimated_generation_gwh_2016 REAL,
estimated_generation_gwh_2017 REAL);

.mode csv
.import global_power_plant_database_adjusted.csv powerplants
