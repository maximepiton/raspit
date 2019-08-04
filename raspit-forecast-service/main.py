from os import path, environ, makedirs
import base64
import logging
from datetime import datetime, date
import math
import re
import threading
import glob
import shutil
import click
from netCDF4 import Dataset
from wrf import getvar, ll_to_xy
import geohash2 as geohash
from google.cloud import firestore, storage
from flask import Flask, request, abort, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(
    level="INFO", format="wrf_forecast_service - %(levelname)s - %(message)s"
)

GCS_BUCKET = environ.get("GCS_BUCKET", "")
WRF_CACHE_FOLDER = environ.get("WRF_CACHE_FOLDER", "/cache")


def update_wrf_cache(bucket_name, run, cache_folder):
    """
    Download wrf files of a specific run from a GCS bucket

    Args:
        bucket_name (str): Name of the GCS bucket
        run (string): Compute run
        cache_folder (str): Folder where the files will be downloaded
    """
    logging.info("Updating WRF cache")

    run_folder = path.join(cache_folder, run)
    logging.info("Run folder: '{}'".format(run_folder))
    if path.exists(run_folder):
        shutil.rmtree(run_folder)
    makedirs(run_folder)

    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=run)

    for blob in blobs:
        out_file_path = path.join(run_folder, path.basename(blob.name))
        logging.info("Downloading {} to {}".format(blob.name, out_file_path))
        with open(out_file_path, "wb") as f:
            blob.download_to_file(f)

    logging.info("Cache update finished")


def garbage_collect_wrf_cache(run_to_keep, cache_folder):
    logging.info("Garbage collecting WRF cache (keeping {})".format(run_to_keep))
    g = cache_folder + "/*/"
    subfolders_list = glob.glob(g)
    for subfolder in subfolders_list:
        if (
            subfolder == path.join(cache_folder, run_to_keep) + "/"
            or subfolder == cache_folder + "/"
        ):
            continue
        logging.info("Removing {}".format(subfolder))
        shutil.rmtree(subfolder)
    logging.info("Garbage collection finished")


def process_wrf_file(file_path, two_d_vars, three_d_vars, lat, lon):
    """
    Extract variables from wrf file(s) into a forecast dictionary

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

    forecast = {}

    wrf_file_pattern = re.search(
        "wrfout_.{3}_\d{4}-\d{2}-\d{2}_(\d{2}:\d{2}):00", file_path
    )
    if wrf_file_pattern:
        hour = wrf_file_pattern.group(1)

    logging.info("ll_to_xy")
    # Get grid coordinates
    x_y = ll_to_xy(dataset, lat, lon, as_int=True)

    logging.info("2dvars")
    # Extract variables
    for variable in two_d_vars:
        forecast[variable.lower()] = getvar(dataset, variable)[
            x_y[1], x_y[0]
        ].values.tolist()
    logging.info("3dvars")
    for variable in three_d_vars:
        forecast[variable.lower()] = getvar(dataset, variable)[
            :, x_y[1], x_y[0]
        ].values.tolist()

    # Enrich document with forecast date
    forecast_date = datetime.strptime(
        getattr(dataset, "START_DATE"), "%Y-%m-%d_%H:%M:%S"
    )
    forecast["date"] = forecast_date

    json_out = {
        "lat": lat,
        "lon": lon,
        "true_lat": forecast["lat"],
        "true_lon": forecast["lon"],
        "forecasts": {hour: forecast},
    }

    logging.info("WRF file post-processing done")

    return json_out


def extract_forecast(bucket_name, lat, lon, wrf_files_path):
    logging.info("Starting forecast extraction")

    # Variables to extract from the raw wrf file
    two_d_vars = ["PBLH", "RAINNC", "ter", "lon", "lat"]
    three_d_vars = ["z", "U", "V", "CLDFRA", "tc", "td", "p"]

    # Generate forecast with all wrf files
    forecast = {}
    for wrf_file in wrf_files_path:
        if forecast == {}:
            forecast = process_wrf_file(wrf_file, two_d_vars, three_d_vars, lat, lon)
        else:
            forecast["forecasts"].update(
                process_wrf_file(wrf_file, two_d_vars, three_d_vars, lat, lon)[
                    "forecasts"
                ]
            )
    return forecast


def push_forecast_to_db(forecast, run, date_time_str):
    """
    Push a dictionary forecast to cloud firestore

    Args:
        firestore_client (google.cloud.firestore.client): firestore
            client that will be used to do the requests
        forecast (dict): Forecast

    Returns:
        -
    """

    logging.info("Pushing forecast to cloud firestore")

    firestore_client = firestore.Client()
    doc = (
        firestore_client.collection("forecast_run")
        .document(run)
        .collection("forecast_date")
        .document(date_time_str)
        .collection("forecast_geohash")
        .document(geohash.encode(forecast["lat"], forecast["lon"], 5))
        .collection("forecast_geopoint")
        .document()
    )
    doc.set(forecast)


def get_forecast_from_db(lat, lon, date_time_str, run):
    firestore_client = firestore.Client()
    forecasts = (
        firestore_client.collection("forecast_run")
        .document(run)
        .collection("forecast_date")
        .document(date_time_str)
        .collection("forecast_geohash")
        .document(geohash.encode(lat, lon, 5))
        .collection("forecast_geopoint")
        .get()
    )

    for forecast in forecasts:
        forecast_dict = forecast.to_dict()
        if forecast_dict["lat"] == lat and forecast_dict["lon"] == lon:
            return forecast_dict

    return None


def get_forecast(bucket_name, wrf_cache_folder, date_time_str, lat, lon):
    logging.info("Getting forecast for {}, {} @ {}".format(lat, lon, date_time_str))

    # We want to get different forecasts only each 0.01° (~1.1km near the equator)
    lat = round(float(lat), 2)
    lon = round(float(lon), 2)

    # Depending on date_time length, we will select only one wrf file, or a bunch of them
    if len(date_time_str) == 10:
        date_time = datetime.strptime(date_time_str, "%Y%m%d%H")
        wrf_file_pattern = "wrfout_.{3}_" + date_time.strftime("%Y-%m-%d_%H:00:00")
    else:
        date_only = datetime.strptime(date_time_str, "%Y%m%d")
        wrf_file_pattern = "wrfout_.{3}_" + date_only.strftime("%Y-%m-%d_")

    run = get_current_run()
    if run is None:
        return

    # Try to fetch from DB first
    cached_forecast = get_forecast_from_db(lat, lon, date_time_str, run)
    if cached_forecast is not None:
        logging.info("Found matching forecast in db")
        return cached_forecast
    else:
        logging.info("No matching forecast found in db")

        # Select only relevant wrf files
        run_wrf_files = glob.glob(path.join(wrf_cache_folder, run, "*"))
        wrf_files = []
        for f in run_wrf_files:
            if re.search(wrf_file_pattern, f):
                wrf_files.append(f)

        # Extract forecast from all wrf files
        forecast = extract_forecast(bucket_name, lat, lon, wrf_files)
        logging.info(forecast)

        # Push it to DB for later use
        push_forecast_to_db(forecast, run, date_time_str)

        return forecast


def get_current_run():
    firestore_client = firestore.Client()
    ref = firestore_client.collection("current_run").document("current_run")
    doc = ref.get().to_dict()
    if doc is None:
        return None
    else:
        return doc["id"]


def set_current_run(run):
    def background_run_update(bucket_name, run, cache_folder):
        # Update local cache first
        update_wrf_cache(bucket_name, run, cache_folder)

        # Update DB when done
        doc = {"id": run}
        firestore_client = firestore.Client()
        firestore_client.collection("current_run").document("current_run").set(doc)

        # Delete old runs
        garbage_collect_wrf_cache(run, cache_folder)

    # Update the cache in background (can take minutes)
    thread = threading.Thread(
        target=background_run_update,
        kwargs={
            "bucket_name": GCS_BUCKET,
            "run": run,
            "cache_folder": WRF_CACHE_FOLDER,
        },
    )
    thread.start()


@click.command("extract-forecast")
@click.option("--bucket-name", default=GCS_BUCKET, help="GCS bucket name")
@click.option("--date-time", help="Forecast date/time (YYYMMDDHH)")
@click.option("--lat", help="Forecast latitude")
@click.option("--lon", help="Forecast longitude")
@click.option("--wrf-file-path", help="WRF input file (for debug purposes)")
def extract_forecast_cli(bucket_name, date_time, lat, lon, wrf_file_path):
    return extract_forecast(bucket_name, date_time, lat, lon, wrf_file_path)


@app.route("/forecast", methods=["GET"])
def forecast_route():
    if not all(arg in request.args for arg in ("lat", "lon", "datetime")):
        abort(400)
    return jsonify(
        get_forecast(
            GCS_BUCKET,
            WRF_CACHE_FOLDER,
            request.args["datetime"],
            request.args["lat"],
            request.args["lon"],
        )
    )


@app.route("/run", methods=["GET", "POST"])
def run_route():
    if request.method == "GET":
        return get_current_run()
    else:
        json = request.get_json()
        run = base64.b64decode(json["message"]["data"]).decode("utf-8")
        set_current_run(run)
        return "Updating"


@app.route("/healthz", methods=["GET"])
def health_route():
    return "Serving"


@app.before_first_request
def init_wrf_cache():
    logging.info("Initializing cache")
    run = get_current_run()
    if run is None:
        logging.warning("No current run defined in DB")
        return
    update_wrf_cache(GCS_BUCKET, run, WRF_CACHE_FOLDER)


if __name__ == "__main__":
    extract_forecast()
