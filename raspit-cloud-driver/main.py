import os
from googleapiclient import discovery
from flask import jsonify
import time
import json
import base64
from jinja2 import Template

instance_launch_template = r"""{
    "kind": "compute#instance",
    "name": "{{ image }}",
    "zone": "projects/{{ project_id }}/zones/{{ zone }}",
    "machineType": "projects/{{ project_id }}/zones/{{ zone }}/machineTypes/{{ instance_type }}",
    "metadata": {
        "kind": "compute#metadata",
        "items": [
            {
                "key": "serial-port-enable",
                "value": "1"
            },
            {
                "key": "gce-container-declaration",
                "value": "spec:\n  containers:\n  - name: raspit-compute\n    image: gcr.io/{{ project_id }}/{{ image }}\n{{ env_vars }}    stdin: false\n    tty: false\n    restartPolicy: Never\n"
            },
            {
                "key": "google-logging-enabled",
                "value": "true"
            }
        ]
    },
    "tags": {
        "items": []
    },
    "disks": [
        {
            "kind": "compute#attachedDisk",
            "type": "PERSISTENT",
            "boot": true,
            "mode": "READ_WRITE",
            "autoDelete": true,
            "deviceName": "{{ image }}",
            "initializeParams": {
                "sourceImage": "projects/cos-cloud/global/images/cos-stable-73-11647-121-0",
                "diskType": "projects/{{ project_id }}/zones/{{ zone }}/diskTypes/pd-standard",
                "diskSizeGb": "20"
            }
        }
    ],
    "canIpForward": false,
    "networkInterfaces": [
        {
            "kind": "compute#networkInterface",
            "subnetwork": "projects/{{ project_id }}/regions/us-east1/subnetworks/default",
            "accessConfigs": [
                {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "type": "ONE_TO_ONE_NAT",
                    "networkTier": "PREMIUM"
                }
            ],
            "aliasIpRanges": []
        }
    ],
    "description": "",
    "labels": {
        "container-vm": "cos-stable-73-11647-121-0"
    },
    "scheduling": {
        "preemptible": false,
        "onHostMaintenance": "TERMINATE",
        "automaticRestart": false,
        "nodeAffinities": []
    },
    "deletionProtection": false,
    "serviceAccounts": [
        {
            "email": "raspit-admin@{{ project_id }}.iam.gserviceaccount.com",
            "scopes": [
                "https://www.googleapis.com/auth/cloud-platform"
            ]
        }
    ]
}"""


def wait_for_operation(compute, project, zone, operation_name, max_wait_seconds=120):
    print("Waiting for operation to finish...")
    end_time = time.time() + max_wait_seconds
    while time.time() < end_time:
        result = (
            compute.zoneOperations()
            .get(project=project, zone=zone, operation=operation_name)
            .execute()
        )

        if result["status"] == "DONE":
            print("done.")
            if "error" in result:
                raise Exception(result["error"])
            return result

        time.sleep(1)
    else:
        raise Exception("Operation timed out")


def launch_instance(event, context):
    """ Background Cloud Function to be triggered by Pub/Sub.
        Spawn an instance and launch a docker container on it,
        with optional environment variables.
    Args:
        event (dict): The dictionary with data specific to
            this type of event.

        Event data must be a JSON formatted with the following
        content:
            json_data'{"image":"<docker image to spawn>",
              "zone":"<zone to launch the instance in>",
              "instance_type":"<instance type>",
              "env":
                {"MY_ENV_VAR": "<value>"}
            }'
    """
    compute = discovery.build("compute", "v1")

    data = base64.b64decode(event['data']).decode('utf-8')
    json_data = json.loads(data)

    if json_data["env"] == "":
        env_vars = ""
    else:
        env_vars = r"    env:\n"
        for key, value in json_data["env"].items():
            env_vars += r"    - name: {key}\n      ".format(key=key)
            env_vars += r"value: {value}\n".format(value=value)

    project_id = os.getenv("GCLOUD_PROJECT")

    template = Template(instance_launch_template)
    filled_instance_launch_template = template.render(
        project_id=project_id,
        image=json_data["image"],
        zone=json_data["zone"],
        instance_type=json_data["instance_type"],
        env_vars=env_vars,
    )
    print(filled_instance_launch_template)
    body = json.loads(filled_instance_launch_template)

    operation = (
        compute.instances()
        .insert(
            project=project_id, zone=json_data["zone"], body=body
        )
        .execute()
    )

    wait_for_operation(
        compute, project_id, json_data["zone"], operation["name"]
    )


def delete_instance(event, context):
    """ Background Cloud Function to be triggered by Pub/Sub.
        Stop and delete an instance.
    Args:
        event (dict): The dictionary with data specific to
            this type of event.

        Event data must be a JSON formatted with the following
        content:
            '{"name":"<instance name>",
              "zone":"<zone that contains the instance>",
            }'
    """
    compute = discovery.build("compute", "v1")

    data = base64.b64decode(event['data']).decode('utf-8')
    json_data = json.loads(data)

    print(
        compute.instances()
        .delete(
            project=os.getenv("GCLOUD_PROJECT"),
            zone=json_data["zone"],
            instance=json_data["name"],
        )
        .execute()
    )
