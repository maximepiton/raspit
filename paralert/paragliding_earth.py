import json
import requests
import xmltodict
import numpy
import yaml


def get_sites(limit="99",style="short",north=44.8,south=42.24,east=5.18,west=-2.32):
    response = requests.get("https://paragliding.earth/export/getBoundingBoxSites.php/?limit=99&style=short&north=44.813018740612776&south=42.24478535602799&east=5.1800537109375&west=-2.3236083984375")

    return response


if __name__ == "__main__":

    sites_resp = get_sites()
#outStr = yaml.safe_dump(sites_resp.text)
#    print(outStr)
    a = xmltodict.parse(sites_resp.text)
    print(a.keys())
#    a = json.dumps(a)
#    print(a)



