import json
import requests
import numpy

import utilities

def get_paraglidable_json():
    
    response = requests.get("https://api.paraglidable.com/?key=d60092fb1105a1f4&format=JSON&version=1")
    forecast_pgble = json.loads(response.text)
          
    write_to_JSON_file('./paraglidable_forecast/', 'forecast_pgble', forecast_pgble)


def write_to_JSON_file(path, fileName, data):
    
    filePathNameWExt = './' + path + '/' + fileName + '.json'
    with open(filePathNameWExt, 'w') as fp:
        json.dump(data, fp)

        
def get_score_paraglidable(site):
    
    with open("./paraglidable_forecast/forecast_pgble.json", "r") as f:
        pgble_data = json.load(f)

    tm_fly = pgble_data[utilities.date_N_day_after(1)][site]['forecast']['fly']
    tm_XC = pgble_data[utilities.date_N_day_after(1)][site]['forecast']['XC']
    atm_fly = pgble_data[utilities.date_N_day_after(2)][site]['forecast']['fly']
    atm_XC = pgble_data[utilities.date_N_day_after(2)][site]['forecast']['XC']
        
    tomorrow_score = numpy.mean([tm_fly,tm_XC])
    after_tomorrow_score = numpy.mean([atm_fly,atm_XC])
    
    tm_score_10 = int(tomorrow_score * 10)
    atm_score_10 = int(after_tomorrow_score * 10)
    
    print(pgble_data[utilities.date_N_day_after(1)][site]['name'])    
    print('demain : ' + str(tm_score_10) + '/10')
    print('apres demain : ' + str(atm_score_10) + '/10')
    
