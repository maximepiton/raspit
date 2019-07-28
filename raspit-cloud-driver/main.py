from googleapiclient import discovery
from flask import jsonify
import time
import json
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


def launch_instance(request):
    """ HTTP Cloud Function.
        Spawn an instance and launch a docker container on it,
        with optional environment variables.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/0.12/api/#flask.Request>
        Must contain a JSON payload with the following :
            '{"project_id":"<project id>",
              "image":"<docker iamge to spawn>",
              "zone":"<zone to launch the instance in>",
              "instance_type":"<instance type>",
              "env":
                {"MY_ENV_VAR": "<value>"}
            }'
    Returns:
        Always OK. Isn't that great?
    """
    compute = discovery.build("compute", "v1")

    request_json = request.get_json()
    expected_keys = ["image", "project_id", "zone", "instance_type", "env"]
    if request_json and all(key in request_json for key in expected_keys):
        if request_json["env"] == "":
            env_vars = ""
        else:
            env_vars = r"    env:\n"
            for key, value in request_json["env"].items():
                env_vars += r"    - name: {key}\n      ".format(key=key)
                env_vars += r"value: {value}\n".format(value=value)
    else:
        return "ERROR : Can't launch instance, request parameter(s) missing"

    template = Template(instance_launch_template)
    filled_instance_launch_template = template.render(
        project_id=request_json["project_id"],
        image=request_json["image"],
        zone=request_json["zone"],
        instance_type=request_json["instance_type"],
        env_vars=env_vars,
    )
    print(filled_instance_launch_template)
    body = json.loads(filled_instance_launch_template)

    operation = (
        compute.instances()
        .insert(
            project=request_json["project_id"], zone=request_json["zone"], body=body
        )
        .execute()
    )

    wait_for_operation(
        compute, request_json["project_id"], request_json["zone"], operation["name"]
    )

    return "OK"


def delete_instance(request):
    """ HTTP Cloud Function.
        Stop and delete an instance.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/0.12/api/#flask.Request>
        Must contain a JSON payload with the following :
            '{"project_id":"<project id>",
              "name":"<instance name>",
              "zone":"<zone that contains the instance>",
            }'
    Returns:
        Always OK. Isn't that great?
    """
    compute = discovery.build("compute", "v1")

    request_json = request.get_json()
    expected_keys = ["name", "project_id", "zone"]
    if not request_json or not all(key in request_json for key in expected_keys):
        return "ERROR : Can't delete instance, request parameter(s) missing"

    print(
        compute.instances()
        .delete(
            project=request_json["project_id"],
            zone=request_json["zone"],
            instance=request_json["name"],
        )
        .execute()
    )

    return "OK"
