# Raspit

Soaring weather forecast web distribution

## Components

### raspit-cloud-driver

Bundles two Google Cloud Functions, triggered by HTTP calls :
* **launch_instance** : Spins up a Google Compute Engine instance, and starts a specific docker container on it ;
* **delete_instance** : Stops and deletes a specific instance. 

#### How to deploy
```shell
$ gcloud functions deploy launch_instance --runtime python37 --trigger-topic launch-instance
$ gcloud functions deploy delete_instance --runtime python37 --trigger-topic delete-instance
$ gcloud beta scheduler jobs create pubsub compute-launch \
--schedule '0 5 * * *' \
--topic launch-instance \
--message-body '{"image": "raspit-compute", "zone": "us-east1-b", "instance_type": "n1-highcpu-8", "env": {"GCS_BUCKET": "raspit-compute", "PUBSUB_TOPIC": "run-finished"}}' \
--time-zone 'Europe/Paris'
```

### raspit-forecast-service

Docker image used to post-process raw WRF files. It fetches WRF files from a Google
Cloud Storage bucket, generates one JSON document per WRF file, containing variables
we want to extract, and push them to Google Cloud Datastore.

#### How to deploy
```shell
$ gcloud builds submit -t gcr.io/<gcp_project_id>/raspit-forecast-service .
$ gcloud beta run deploy --image gcr.io/raspit-248118/raspit-forecast-service --platform managed --region europe-west1 --update-env-vars GCS_BUCKET=raspit-compute --memory=1Gi
```

#### How to launch locally

You have to generate a service account JSON key from the IAM GCP console first.

```shell
$ docker run -it -e GOOGLE_APPLICATION_CREDENTIALS="/key.json" -v $(pwd):/src/ -v <path_to_json_key>:/key.json --rm gcr.io/<gcp_project_id>/raspit-forecast-service:latest bash
# python wrf_to_json.py --bucket-name <bucket_name> --prefix <prefix>
```

### raspit-compute-image

WRF-ARW Weather forecast compute image for SW France. Include 2 docker images :
* Docker-rasp-wrfv3/ : Generic wrfv3 rasp dockerfile (for development purpose) ;
* Docker-raspit-compute/ : "Production" image, derived from the above. Does a run for the next 3 days upon startup, transfer the data generated to Cloud Storage and kills the host (via a raspit-cloud-driver call) when done.

Uses two different domains :
* PYR2/ : 1-stage 0.5deg GFS initialized 6km grid, for days n+2 and n+3 ;
* PYR3/ : 1-stage 0.25deg GFS initialized 3km grid, for day n+1.

#### How to deploy
```shell
$ cd raspit-compute/Docker-rasp-wrfv3
$ wget http://rasp-uk.uk/SOFTWARE/WRFV3.x/raspGM.tgz
$ wget http://rasp-uk.uk/SOFTWARE/WRFV3.x/raspGM-bin.tgz
$ wget http://rasp-uk.uk/SOFTWARE/WRFV3.x/rangs.tgz
$ wget https://github.com/WRF-CMake/WPS/releases/download/WPS-CMake-4.0.2/wps-cmake-4.0.2-serial-basic-release-linux.tar.xz
$ docker build -t rasp-wrfv3 .
$ cd ../Docker-raspit-compute
$ docker build -t gcr.io/<gcp_project_id>/raspit-compute .
$ docker push gcr.io/<gcp_project_id>/raspit-compute
```

#### How to start a development container

```
$ cd raspit-compute/Docker-raspit-compute
$ docker run --rm -it \
    -e "DEV_ENV=y" \
    -v $(pwd):/root/rasp/Raspit-compute-image \
    rasp-wrfv3 bash
```

### raspit-web

Google App Engine flask-based webserver. Also includes an App Engine cron job, that calls the /compute-launch (see below) route daily.

#### Routes

* / : User endpoint ;
* /forecast : Returns JSON forecast data fetch from Google Cloud Datastore ;
* /compute-launch : Triggers a forecast run, via a launch_instance Cloud Function call.

#### How to deploy

```
$ cd raspit-web
$ gcloud app deploy
$ gcloud app deploy cron.yaml
```

## Simplified architecture diagram

![raspit architecture diagram](raspit_architecture_diagram.png)

## Based on the work of

* Dr Jack : [RASP](http://www.drjack.info/RASP/), a WRF-ARW forecast distribution ;
* V. Mayamsin : [Rasp docker scripts](https://github.com/wargoth/rasp-docker-script)
