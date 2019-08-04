#!/bin/bash
# Script that publish a message on the compute-delete pub/sub topic,
# in order to stop the instance the script is launched on

INSTANCE_NAME=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/name" -H "Metadata-Flavor: Google")
INSTANCE_REGION_FULL=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/zone" -H "Metadata-Flavor: Google")
re="(.*\/)(.*)"
if [[ $INSTANCE_REGION_FULL =~ $re ]]; then INSTANCE_REGION=${BASH_REMATCH[2]}; fi
echo "kill_me: $INSTANCE_NAME on $INSTANCE_REGION"
gcloud pubsub topics publish delete-instance --message="{\"name\":\"$INSTANCE_NAME\", \"zone\":\"$INSTANCE_REGION\"}"

sleep 5
