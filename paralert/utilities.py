import json
from datetime import datetime, timedelta


def date_N_day_after(N):
    
    tomorrow = datetime.now() + timedelta(days=N)

    return tomorrow.strftime("%Y-%m-%d")


def write_to_JSON_file(path, fileName, data):
    
    filePathNameWExt = './' + path + '/' + fileName + '.json'
    with open(filePathNameWExt, 'w') as fp:
        json.dump(data, fp)