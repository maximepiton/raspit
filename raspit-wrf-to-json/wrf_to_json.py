from os import path
import logging
import datetime
import click
from netCDF4 import Dataset
from wrf import getvar, xy_to_ll
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
        break

    return out_path_list


def process_wrf_file(file_path, two_d_vars, three_d_vars):
    """
    Extract variables from a wrf file into a dictionary

    Args:
        file_path (str): Path of the wrf file to process
        two_d_vars (list): List of 2D variables to extract from the dataset
        three_d_vars (list): List of 3D variables to extract from the dataset

    Returns:
        Dict: Forecast dictionary
    """
    logging.info("Post-processing {}".format(file_path))

    dataset = Dataset(file_path)

    # Extract all variables first
    extracted_vars = {}
    for variable in two_d_vars:
        extracted_vars[variable] = getvar(dataset, variable)
    for variable in three_d_vars:
        extracted_vars[variable] = getvar(dataset, variable)

    # Loop over grid to extract all vars
    for x in range(getattr(dataset, "WEST-EAST_GRID_DIMENSION") - 1):
        for y in range(getattr(dataset, "SOUTH-NORTH_GRID_DIMENSION") - 1):
            [lat, lon] = xy_to_ll(dataset, x, y)
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
    json_out["date"] = datetime.datetime.strptime(
        getattr(dataset, "START_DATE"), "%Y-%m-%d_%H:%M:%S"
    )

    return json_out


def push_forecast(datastore_client, forecast):
    """
    Push a dictionary forecast to cloud datastore

    Args:
        datastore_client (google.cloud.datastore.client): datastore
            client that will be used to do the requests
        forecast (dict): Forecast dictionary

    Returns:
        -
    """
    logging.info("Pushing forecast to cloud datastore")
    key = datastore_client.key("Forecast")
    entity = datastore.Entity(key=key)
    entity.update(forecast)
    datastore_client.put(entity)


@click.command()
@click.option(
    "--bucket-name",
    prompt=True,
    default=lambda: os.environ.get("GCS_BUCKET", ""),
    help="Bucket that contains files to process",
)
@click.option(
    "--prefix",
    prompt=True,
    default=lambda: os.environ.get("PREFIX", ""),
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
        forecast_dict = process_wrf_file(file_path, two_d_vars, three_d_vars)
        push_forecast(datastore_client, forecast_dict)

    logging.info("WRF files post-processing done")

if __name__ == "__main__":
    logging.basicConfig(
        level="INFO", format="wrf_to_json - %(levelname)s - %(message)s"
    )
    wrf_to_json()
