from __future__ import print_function
from netCDF4 import Dataset
from wrf import getvar, interpline, CoordPair, ll_to_xy

# Input : bucket_name, folder, spots
# Does the postprocessing for each wrfout file, for each spot

ncfile = Dataset('wrfout_d02_2018-09-07_12:00:00')

[lat, lon] = [44.469223022461, 1.3882482051849]

[x, y] = ll_to_xy(ncfile, lat, lon).values

json_out = {}

two_d_vars = ['PBLH', 'RAINNC', 'ter']
three_d_vars = ['z', 'U', 'V', 'CLDFRA', 'tc', 'td', 'p']

for variable in two_d_vars:
    json_out[variable.lower()] = getvar(ncfile,
                                        variable)[x, y].values.tolist()

for variable in three_d_vars:
    json_out[variable.lower()] = getvar(ncfile,
                                        variable)[:, x, y].values.tolist()

print(json_out)
