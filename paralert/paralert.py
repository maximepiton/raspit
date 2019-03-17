import pandas as pd
import json
import math
import yaml
import numpy


def add_windspeed_winddir_to_forecast(forecast_df):
    """
    Add wind speed and wind direction lists to a forecast DataFrame.

    Args:
        forecast_df (DataFrame): Forecast dataframe

    Returns:
        -
    """
    windspeed_column = forecast_df.apply(
        lambda row: [
            3.6 * math.sqrt(u ** 2 + v ** 2) for u, v in zip(row["umet"], row["vmet"])
        ],
        axis=1,
    )
    winddir_column = forecast_df.apply(
        lambda row: [
            math.atan2(u, v) * 180 / math.pi for u, v in zip(row["umet"], row["vmet"])
        ],
        axis=1,
    )
    forecast_df["wspd"] = pd.Series(windspeed_column, index=forecast_df.index)
    forecast_df["wdir"] = pd.Series(winddir_column, index=forecast_df.index)


def filter_out_high_altitude_domain(forecast_df, height_to_keep_over_bl):
    """
    Resize lists of a forecast DataFrame, to keep only altitudes lower than the height
    of the boundary layer, plus height_to_keep_over_bl

    Args:
        forecast_df (DataFrame): Forecast dataframe
        height_to_keep_over_bl (int): Height to keep over the boundary layer (m)

    Returns:
        -
    """
    absolute_height_to_keep = forecast_df.max()["pblh"] + height_to_keep_over_bl

    # Create a list representing how many elements we should keep in each list,
    # by looping over the "z" list
    z_max = forecast_df.apply(
        lambda row: len([z for z in row["z"] if z < absolute_height_to_keep]), axis=1
    )

    # Crop each cell if it's a list
    for col in forecast_df:
        for i, cell in forecast_df[col].iteritems():
            if isinstance(cell, list):
                forecast_df[col][i] = cell[: z_max[i]]


def filter_out_hours(forecast_df, start_hour, end_hour):
    """
    Filter columns of a forecast DataFrame, where the hour is more than end_hour
    (included) and less than start_hour (included)

    Args:
        forecast_df (DataFrame): Forecast dataframe
        start_hour (int): Start hour
        end_hour (int): End hour

    Returns:
        DataFrame: Filtered-out DataFrame
    """
    ok_hours = ["{0:02d}:00".format(h) for h in range(start_hour, end_hour + 1)]
    return forecast_df[forecast_df.index.isin(ok_hours)]


def filter_out_low_cloudbase(forecast_df, min_bl_thickness):
    """
    Filter columns of a forecast DataFrame, where the boundary
    layer thickness is less than min_bl_thickness.

    Args:
        forecast_df (DataFrame): Forecast dataframe
        min_bl_thickness (int): Minimum thickness of the boundary layer (m)

    Returns:
        DataFrame: Filtered-out DataFrame
    """
    return forecast_df[forecast_df["pblh"] > (forecast_df["ter"] + min_bl_thickness)]


def filter_out_strong_wind(forecast_df, max_windspeed):
    """
    Filter columns of a forecast DataFrame, where the wind speed
    exceeds max_windspeed

    Args:
        forecast_df (DataFrame): Forecast dataframe
        max_windspeed (int): Maximum windspeed (km/h)

    Returns:
        DataFrame: Filtered-out DataFrame
    """
    return forecast_df[
        forecast_df.apply(lambda row: max(row["wspd"]) < max_windspeed, axis=1)
    ]


def get_max_wind_gradient(z_list, windspeed_list):
    """
    Return the maximum wind gradient

    Args:
        z_list (list) : List of z coordinates (list(m))
        windspeed_list (list) : List of wind speeds (list(km/h))

    Returns:
        Float: Maximum wind gradient
    """
    windspeed_array = numpy.array(windspeed_list, dtype=float)
    z_array = numpy.array(z_list, dtype=float)
    return max(map(abs, numpy.gradient(windspeed_array, z_array)))


def filter_out_strong_wind_gradient(forecast_df, max_wind_gradient):
    """
    Filter columns of a forecast DataFrame, where the wind gradient
    exceeds max_wind_gradient

    Args:
        forecast_df (DataFrame): Forecast dataframe
        max_wind_gradient (int): Maximum wind gradient (km/h/hm)

    Returns:
        DataFrame: Filtered-out DataFrame
    """
    # we want the gradient in s^-1
    relative_max_wind_gradient = max_wind_gradient / 3.6 / 100
    return forecast_df[
        forecast_df.apply(
            lambda row: get_max_wind_gradient(row["z"], row["wspd"])
            < relative_max_wind_gradient,
            axis=1,
        )
    ]


def filter_out_wrong_takeoff_conditions(
    forecast_df,
    min_takeoff_windspeed,
    takeoff_winddir_reference,
    takeoff_winddir_tolerance,
    takeoff_wind_height,
):
    """
    Filter columns of a forecast DataFrame, where the wind :
    - is under min_takeoff_windspeed at min_takeoff_windspeed_height
    - hasn't a direction included in takeoff_winddir_reference
      +/- takeoff_winddir_tolerance

    Args:
        forecast_df (DataFrame): Forecast dataframe
        min_takeoff_windspeed (int): Minimum takeoff windspeed (km/h)
        takeoff_winddir_reference (int) : Takeoff optimal wind direction (°)
        takeoff_winddir_tolerance (int) : Takeoff wind direction tolerance (°)
        takeoff_wind_height (int) : Height above terrain where the takeoff
            windspeed and direction will be taken into account (m)

    Returns:
        DataFrame: Filtered-out DataFrame
    """
    return forecast_df[
        forecast_df.apply(
            lambda row: (
                (
                    abs(
                        numpy.interp(
                            takeoff_wind_height + row["ter"], row["z"], row["wdir"]
                        )
                        - takeoff_winddir_reference
                    )
                    < takeoff_winddir_tolerance
                )
                and (
                    numpy.interp(
                        takeoff_wind_height + row["ter"], row["z"], row["wspd"]
                    )
                    > (min_takeoff_windspeed / 3.6)
                )
            ),
            axis=1,
        )
    ]


def get_flight_score(forecast_df):
    """
    Return the flight score

    Args:
        forecast_df (DataFrame): Forecast dataframe

    Returns:
        Integer: flight score
    """
    if forecast_df.empty:
        return 0
    else:
        return sum(
            forecast_df.apply(
                lambda row: (
                    (row["pblh"] - row["ter"]) if row["pblh"] > row["ter"] else 0
                ),
                axis=1,
            )
        )


if __name__ == "__main__":
    with open("forecast.json", "r") as f:
        json_data = json.load(f)

    with open("locations.yaml", "r") as f:
        locations = yaml.load(f)

    site_parameters = locations["gensac"]
    print(site_parameters)

    forecast_df = pd.DataFrame(json_data["data"]).transpose()

    forecast_df = filter_out_hours(
        forecast_df, site_parameters["start_hour"], site_parameters["end_hour"]
    )
    print(forecast_df)

    filter_out_high_altitude_domain(forecast_df, 200)
    print(forecast_df)

    add_windspeed_winddir_to_forecast(forecast_df)
    print(forecast_df)

    forecast_df = filter_out_low_cloudbase(
        forecast_df, site_parameters["min_bl_thickness"]
    )
    print(forecast_df)

    forecast_df = filter_out_strong_wind(forecast_df, site_parameters["max_windspeed"])
    print(forecast_df)

    forecast_df = filter_out_strong_wind_gradient(
        forecast_df, site_parameters["max_wind_gradient"]
    )
    print(forecast_df)

    forecast_df = filter_out_wrong_takeoff_conditions(
        forecast_df,
        site_parameters["min_takeoff_windspeed"],
        site_parameters["takeoff_winddir_reference"],
        site_parameters["takeoff_winddir_tolerance"],
        site_parameters["takeoff_wind_height"],
    )
    print(forecast_df)

    print(get_flight_score(forecast_df))
