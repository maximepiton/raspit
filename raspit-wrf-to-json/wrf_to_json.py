from __future__ import print_function
from netCDF4 import Dataset
from wrf import getvar, interpline, CoordPair, xy_to_ll
import click

# Input : bucket_name, folder, spots
# Does the postprocessing for each wrfout file, for each spot


@click.command()
@click.option("--bucket-name", help="Bucket that contains files to process")
@click.option("--folder", help="Folder in the bucket that contains files to process")
@click.option("--spot-list", help="List of spots (name + gps coordinates)")
def wrf_to_json(bucket_name, folder, spot_list):
    dataset = Dataset("20190327_wrfout_d02_2019-03-26_09_00_00")
    [lat, lon] = [44.469223022461, 1.3882482051849]

    # [x, y] = ll_to_xy(dataset, lat, lon).values

    json_out = {}

    # Variables to extract from the raw wrf file
    two_d_vars = ["PBLH", "RAINNC", "ter"]
    three_d_vars = ["z", "U", "V", "CLDFRA", "tc", "td", "p"]

    # Extract all variables first
    extracted_vars = {}
    for variable in two_d_vars:
        extracted_vars[variable] = getvar(dataset, variable)
    for variable in three_d_vars:
        extracted_vars[variable] = getvar(dataset, variable)

    for x in range(getattr(dataset, "WEST-EAST_GRID_DIMENSION") - 1):
        for y in range(getattr(dataset, "SOUTH-NORTH_GRID_DIMENSION") - 1):
            [lat, lon] = xy_to_ll(dataset, x, y)
            json_out = {"lat": lat, "lon": lon}
            for variable in two_d_vars:
                json_out[variable.lower()] = extracted_vars[variable][
                    y, x
                ].values.tolist()

            for variable in three_d_vars:
                json_out[variable.lower()] = extracted_vars[variable][
                    :, y, x
                ].values.tolist()


if __name__ == "__main__":
    wrf_to_json()
