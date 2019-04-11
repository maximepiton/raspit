def dequeue(data, context):
    """
    Background Cloud Function to be triggered by Pub/Sub.
    It launches a GCE instance with a raspit-wrf-to-json container on it,
    with environment variables coming from the Pub/Sub message.

    Args:
         data (dict): The dictionary with data specific to this type of event.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata.
    """
    import os
    import base64
    import requests
    from flask import abort

    # Check event type
    event_name = base64.b64decode(data["data"]).decode("utf-8")
    if event_name != "run_finished_event":
        print("Unknown event: {}".format(event_name))
        return abort(400)

    # Extract message payload
    bucket = data["attributes"]["bucket"]
    prefix = data["attributes"]["prefix"]
    print(
        "Launching post-processing of {prefix} in {bucket}".format(
            prefix=prefix, bucket=bucket
        )
    )

    # Call raspit-driver
    project_id = os.getenv("GCLOUD_PROJECT")
    url = "https://us-central1-" + project_id + ".cloudfunctions.net/launch_instance"
    payload = {
        "project_id": project_id,
        "image": "raspit-wrf-to-json",
        "zone": "us-east1-c",
        "instance_type": "f1-micro",
        "env": {"GCS_BUCKET": bucket, "PREFIX": prefix},
    }

    r = requests.post(url, json=payload)
    print("Request status: {}".format(r.status_code))
