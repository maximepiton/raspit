from os import path, environ
import logging
from datetime import datetime
import math
import re
import click
from netCDF4 import Dataset
from wrf import getvar, ll_to_xy
from google.cloud import firestore, storage
from flask import Flask, request, abort, jsonify

app = Flask(__name__)

logging.basicConfig(
    level="INFO", format="wrf_forecast_extractor - %(levelname)s - %(message)s"
)

GCS_BUCKET = environ.get("GCS_BUCKET", "")


def download_wrf_file(bucket_name, date_time, out_folder):
    """
    Download wrf file of a specific date/time from a GCS bucket

    Args:
        bucket_name (str): Name of the GCS bucket
        date_time (datetime): Forecast datetime
        out_folder (str): Folder where the file will be downloaded

    Returns:
        str: Path of downloaded file
    """
    client = storage.Client(project="raspit-248118")
    bucket = client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=date_time.strftime("%Y%m"))
    print(date_time.strftime("%Y%m%d"))

    file_pattern = "\d{8}\/wrfout_.{3}_" + date_time.strftime("%Y-%m-%d_%H:00:00")
    print(file_pattern)
    out_path_list = []
    for blob in blobs:
        print(blob.name)
        if re.search(file_pattern, blob.name):
            out_file_path = path.join(out_folder, path.basename(blob.name))
            logging.info("Downloading {} to {}".format(blob.name, out_file_path))
            with open(out_file_path, "wb") as f:
                blob.download_to_file(f)
            return out_file_path

    logging.warning("Could not find any suitable wrf file to download")
    return None


def process_wrf_file(file_path, two_d_vars, three_d_vars, lon, lat):
    """
    Extract variables from a wrf file into a forecast dictionaries

    Args:
        file_path (str): Path of the wrf file to process
        two_d_vars (list): List of 2D variables to extract from the dataset
        three_d_vars (list): List of 3D variables to extract from the dataset
        lon (double): Longitude
        lat (double): Latitude

    Returns:
        Dict: Forecast
    """
    logging.info("Post-processing {}".format(file_path))

    dataset = Dataset(file_path)
    json_out = {}

    # Get grid coordinates
    x_y = ll_to_xy(dataset, lat, lon, as_int=True)

    # Extract variables
    for variable in two_d_vars:
        json_out[variable.lower()] = getvar(dataset, variable)[
            x_y[0], x_y[1]
        ].values.tolist()
    for variable in three_d_vars:
        json_out[variable.lower()] = getvar(dataset, variable)[
            :, x_y[0], x_y[1]
        ].values.tolist()

    # Enrich document with forecast date
    date = datetime.strptime(getattr(dataset, "START_DATE"), "%Y-%m-%d_%H:%M:%S")
    json_out["date"] = date

    # Store real location data
    json_out["true_lon"] = json_out["lon"]
    json_out["true_lat"] = json_out["lat"]
    json_out["lon"] = lon
    json_out["lat"] = lat

    logging.info("WRF files post-processing done")

    return json_out


def extract_forecast(bucket_name, date_time, lon, lat, wrf_file_path):
    logging.info("Starting WRF post-processing")

    date_time = datetime.strptime(date_time, "%Y%m%d%H")

    if not wrf_file_path:
        wrf_file_path = download_wrf_file(bucket_name, date_time, "/tmp")
    else:
        logging.info("WRF file specified, skipping download")

    # Variables to extract from the raw wrf file
    two_d_vars = ["PBLH", "RAINNC", "ter", "lon", "lat"]
    three_d_vars = ["z", "U", "V", "CLDFRA", "tc", "td", "p"]

    if wrf_file_path:
        return process_wrf_file(wrf_file_path, two_d_vars, three_d_vars, lon, lat)
    else:
        return None


@click.command("extract-forecast")
@click.option("--bucket-name", default=GCS_BUCKET, help="GCS bucket name")
@click.option("--date-time", help="Forecast date/time (YYYMMDDHH)")
@click.option("--lon", help="Forecast longitude")
@click.option("--lat", help="Forecast latitude")
@click.option("--wrf-file-path", help="WRF input file (for debug purposes)")
def extract_forecast_cli(bucket_name, date_time, lon, lat, wrf_file_path):
    return extract_forecast(bucket_name, date_time, lon, lat, wrf_file_path)


@app.route("/forecast", methods=["GET"])
def get_forecast():
    if not all(arg in request.args for arg in ("lon", "lat", "datetime")):
        abort(400)
    return jsonify(
        extract_forecast(
            GCS_BUCKET,
            request.args["datetime"],
            request.args["lon"],
            request.args["lat"],
            None,
        )
    )


@app.route("/healthz", methods=["GET"])
def health():
    return "Serving"


if __name__ == "__main__":
    extract_forecast()
