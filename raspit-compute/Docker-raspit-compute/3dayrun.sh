#!/bin/bash

# Function that removes all the shit before and after each run
# Params : $1 : Domain
function sweep {
  cd /root/rasp/$1
  rm -f met_em.d* ; rm -f wrfout* ; rm -f met_em* ; rm -f UNGRIB:* ; rm -f wrfinput_* ; rm -f GRIB/* ; rm -f OUT/*
}

# Function that call a google cloud function to stop itself
function stop_instance {
  PROJECT_ID=$(curl "http://metadata.google.internal/computeMetadata/v1/project/project-id" -H "Metadata-Flavor: Google")
  INSTANCE_NAME=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/name" -H "Metadata-Flavor: Google")
  INSTANCE_REGION_FULL=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/zone" -H "Metadata-Flavor: Google")
  re="(.*\/)(.*)"
  if [[ $INSTANCE_REGION_FULL =~ $re ]]; then INSTANCE_REGION=${BASH_REMATCH[2]}; fi
  gcloud functions call delete_instance --data "{\"project_id\":\"$PROJECT_ID\", \"name\":\"$INSTANCE_NAME\", \"zone\":\"$INSTANCE_REGION\"}"
}

# Function that uploads output images to a ftp server or a GCS bucket, 
# depending on USE_FTP and GCS_BUCKET environment variables
# Params : $1 : Domain ; $2 : run date
function upload {
  if [[ -n "$GCS_BUCKET" ]]
  then
    echo "Uploading "$2" run of "$1" to "$GCS_BUCKET" GCS bucket"
    gsutil rm -r gs://$GCS_BUCKET/$2
    gsutil -m cp /root/rasp/$1/wrfout*d02*00:00 gs://$GCS_BUCKET/$2/
    echo "Publishing event to "$PUBSUB_TOPIC
    gcloud pubsub topics publish $PUBSUB_TOPIC --message="run_finished_event" --attribute path=$GCS_BUCKET/$2
  else
    echo "WARNING : GCS_BUCKET environment variable not set. No upload will be done."
  fi
}

# Function that copy a domain from the Raspit-compute-image folder (for development purposes only)
# Params : $1 : Domain
function cp_dev_domain {
  cd /root/rasp
  rm -rf $1 && mkdir $1  
  cp --preserve=links -r region.TEMPLATE/* $1/
  cp -r Raspit-compute-image/$1/* $1/
  cp $1/namelist.input $1/namelist.input.template && cp $1/namelist.wps $1/namelist.wps.template
}

# Function that does one run, corresponding to a certain domain and a certain day
# Params : $1 : Domain ; $2 : start_hour
function one_day_run {
  sweep $1
  export START_HOUR=$2
  cd /root/rasp
  echo "Running "$1" with START_HOUR="$2
  runGM $1
  echo $1" with START_HOUR="$2" done."
  upload $1 $(date --date=$(($2 / 24))" days" +%Y%m%d)
  sweep $1
}

# Depending on the current hour, we will use 0Z or 12Z grib files from the ncep servers
currentHour=$(date -u +%H)
if [ $currentHour -lt 16 ]
then
  export MODEL_RUN=0
else
  export MODEL_RUN=12
fi
echo "Model run : "$MODEL_RUN"Z"

# We copy the GM & domain directories, and the boto file from our dev directory to the rasp directory if DEV_ENV is set
if [[ -n "$DEV_ENV" ]]
then
  echo "Development environment detected. Copying domains and GM folder from external volume..."
  cp_dev_domain PYR2
  cp_dev_domain PYR3
  cp -r Raspit-compute-image/GM /root/rasp/
else
  echo "Production environment detected. Domains should already be in the rasp directory"
fi

# Run launch
#one_day_run PYR2 33
#one_day_run PYR2 57
one_day_run PYR2 9
stop_instance
