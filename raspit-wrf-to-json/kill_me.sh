#!/bin/bash
# Script that call a google cloud function, to stop the instance the script is launched on

PROJECT_ID=$(curl "http://metadata.google.internal/computeMetadata/v1/project/project-id" -H "Metadata-Flavor: Google")
INSTANCE_NAME=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/name" -H "Metadata-Flavor: Google")
INSTANCE_REGION_FULL=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/zone" -H "Metadata-Flavor: Google")
re="(.*\/)(.*)"
if [[ $INSTANCE_REGION_FULL =~ $re ]]; then INSTANCE_REGION=${BASH_REMATCH[2]}; fi
echo "kill_me: $INSTANCE_NAME on $INSTANCE_REGION (project: $PROJECT_ID)"
gcloud functions call delete_instance --data "{\"project_id\":\"$PROJECT_ID\", \"name\":\"$INSTANCE_NAME\", \"zone\":\"$INSTANCE_REGION\"}"

sleep 5
