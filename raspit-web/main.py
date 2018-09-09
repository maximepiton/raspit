from flask import Flask, render_template, jsonify, request
import json
import os
from jinja2 import Environment, FileSystemLoader
import requests
from google.cloud import datastore
from googleapiclient import discovery

datastore_client = datastore.Client()

app = Flask(__name__)


def get_daily_forecast(last_x_day):
    last_x_day = 0 if last_x_day < 0 else last_x_day
    print(last_x_day)
    query = datastore_client.query(kind='Forecast')
    query.order = ['-date']

    forecasts = query.fetch(limit=5)
    forecast = list(forecasts)[last_x_day]
    forecast_dict = {x: forecast[x] for x in forecast.keys()}

    return forecast_dict


@app.route('/compute-launch')
def three_day_run():
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    url = 'https://us-central1-' + project_id + \
          '.cloudfunctions.net/launch_instance'
    payload = {'project_id': project_id,
               'image': 'raspit-compute',
               'zone': 'us-east1-b',
               'instance_type': 'n1-highcpu-8',
               'env': {'GCS_BUCKET':
                        'gcr.io/' + project_id + '/raspit-compute',
                       'PUBSUB_TOPIC':
                        'gcr.io/' + project_id + '/raspit-compute'}}

    r = requests.post(url, json=payload)
    return 'OK'


@app.route('/forecast')
def forecast():
    try:
        last_x_day = int(request.args.get('last_x_day', 0))
    except ValueError:
        last_x_day = 0
    return jsonify(get_daily_forecast(last_x_day))


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    # Used only when testing locally
    app.run(host='127.0.0.1', port=8080, debug=True)
