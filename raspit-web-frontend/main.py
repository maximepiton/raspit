from flask import Flask, render_template, jsonify, request
import json
import os
from jinja2 import Environment, FileSystemLoader
import requests
from googleapiclient import discovery

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    # Used only when testing locally
    app.run(host='127.0.0.1', port=8080, debug=True)
