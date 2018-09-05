import datetime
from flask import Flask, render_template, jsonify
from google.cloud import datastore

datastore_client = datastore.Client()

app = Flask(__name__)


def get_daily_forecast(last_x_day=1):
    query = datastore_client.query(kind='Forecast')
    query.order = ['-date']
    # query.add_filter('date', '=', date)

    forecasts = query.fetch(limit=5)
    forecast = list(forecasts)[last_x_day]
    forecast_dict = {x: forecast[x] for x in forecast.keys()}

    return forecast_dict


@app.route('/forecast')
def forecast():
    return jsonify(get_daily_forecast())


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    # Used only when testing locally
    app.run(host='127.0.0.1', port=8080, debug=True)
