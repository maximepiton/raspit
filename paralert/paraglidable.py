import json
import requests
import numpy

import utilities

def get_paraglidable_json():
    
    response = requests.get("https://api.paraglidable.com/?key=d60092fb1105a1f4&format=JSON&version=1")
    forecast_pgble = json.loads(response.text)
          
    utilities.write_to_JSON_file('./paraglidable_forecast/', 'forecast_pgble', forecast_pgble)

        
def get_paraglidable_score(site):
    
    with open("./paraglidable_forecast/forecast_pgble.json", "r") as f:
        pgble_data = json.load(f)

    """ get scores in json file """
    tm_fly = pgble_data[utilities.date_N_day_after(1)][site]['forecast']['fly']
    tm_XC = pgble_data[utilities.date_N_day_after(1)][site]['forecast']['XC']
    atm_fly = pgble_data[utilities.date_N_day_after(2)][site]['forecast']['fly']
    atm_XC = pgble_data[utilities.date_N_day_after(2)][site]['forecast']['XC']
       
    """ Score : mean of the 'XC' and 'fly' score """
    tomorrow_score = numpy.mean([tm_fly,tm_XC])
    after_tomorrow_score = numpy.mean([atm_fly,atm_XC])
    
    """ Manage score to print note xx/10 """
    tm_score_10 = int(tomorrow_score * 10)
    atm_score_10 = int(after_tomorrow_score * 10)
    
    site_name = pgble_data[utilities.date_N_day_after(1)][site]['name']
    
    result_table = [site_name, tm_score_10, atm_score_10]
    return result_table


def get_paraglidable_all_scores():
    
        table = []
    
        """ range depend of the number of sites in paraglidable json file """
        for x in range(0, 3):
            table.append(get_paraglidable_score(x))

        return table