from os import path, environ
import logging
import datetime
import click
from netCDF4 import Dataset
from wrf import getvar
from google.cloud import datastore, storage


def download_wrf_files(bucket_name, prefix, out_folder):
    """
    Download wrf files from a GCS bucket

    Args:
        bucket_name (str): Name of the GCS bucket
        prefix (str): Prefix (~=folder) that contains the wrf files
        out_folder (str): Folder where the files will be downloaded

    Returns:
        List: List of path of files downloaded
    """
    client = storage.Client(project="voltaic-layout-207517")
    bucket = client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)

    out_path_list = []
    for blob in blobs:
        out_file_path = path.join(out_folder, path.basename(blob.name))
        logging.info("Downloading {} to {}".format(blob.name, out_file_path))
        with open(out_file_path, "wb") as f:
            blob.download_to_file(f)
        out_path_list.append(out_file_path)

    return out_path_list


def process_wrf_file(file_path, two_d_vars, three_d_vars):
    """
    Extract variables from a wrf file into a list of forecast dictionaries

    Args:
        file_path (str): Path of the wrf file to process
        two_d_vars (list): List of 2D variables to extract from the dataset
        three_d_vars (list): List of 3D variables to extract from the dataset

    Returns:
        List: Forecasts
    """
    logging.info("Post-processing {}".format(file_path))

    dataset = Dataset(file_path)

    date = datetime.datetime.strptime(
        getattr(dataset, "START_DATE"), "%Y-%m-%d_%H:%M:%S"
    )

    forecast_list = list()

    # Extract all variables first
    extracted_vars = {}
    for variable in two_d_vars:
        extracted_vars[variable] = getvar(dataset, variable)
    for variable in three_d_vars:
        extracted_vars[variable] = getvar(dataset, variable)

    # Loop over grid to extract all vars
    for x in range(getattr(dataset, "WEST-EAST_GRID_DIMENSION") - 1):
        for y in range(getattr(dataset, "SOUTH-NORTH_GRID_DIMENSION") - 1):
            json_out = {}
            for variable in two_d_vars:
                json_out[variable.lower()] = extracted_vars[variable][
                    y, x
                ].values.tolist()

            for variable in three_d_vars:
                json_out[variable.lower()] = extracted_vars[variable][
                    :, y, x
                ].values.tolist()

            # Enrich document with forecast date
            json_out["date"] = date

            forecast_list.append(json_out)

    return forecast_list


def push_forecast(datastore_client, forecast_list):
    """
    Push a dictionary forecast to cloud datastore

    Args:
        datastore_client (google.cloud.datastore.client): datastore
            client that will be used to do the requests
        forecast (List): List of forecast dictionaries

    Returns:
        -
    """
    logging.info("Pushing forecast to cloud datastore")
    entities = list()
    for forecast in forecast_list:
        key = datastore_client.key("Forecast")
        entity = datastore.Entity(key=key)
        entity.update(forecast)
        entities.append(entity)
    datastore_client.put_multi(entities)


@click.command()
@click.option(
    "--bucket-name",
    default=lambda: environ.get("GCS_BUCKET", ""),
    help="Bucket that contains files to process",
)
@click.option(
    "--prefix",
    default=lambda: environ.get("PREFIX", ""),
    help="'Folder' in the bucket that contains files to process",
)
def wrf_to_json(bucket_name, prefix):
    logging.info("Starting WRF post-processing")
    wrf_files = download_wrf_files(bucket_name, prefix, "/tmp")

    # Variables to extract from the raw wrf file
    two_d_vars = ["PBLH", "RAINNC", "ter", "lon", "lat"]
    three_d_vars = ["z", "U", "V", "CLDFRA", "tc", "td", "p"]

    datastore_client = datastore.Client()
    for file_path in wrf_files:
        forecast_list = process_wrf_file(file_path, two_d_vars, three_d_vars)
        push_forecast(datastore_client, forecast_list)

    logging.info("WRF files post-processing done")

if __name__ == "__main__":
    logging.basicConfig(
        level="INFO", format="wrf_to_json - %(levelname)s - %(message)s"
    )
    wrf_to_json()
