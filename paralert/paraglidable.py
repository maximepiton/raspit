import json
import requests
import numpy

import paralert_tool

number_of_sites = 0

def get_paraglidable_json():
    
    response = requests.get("https://api.paraglidable.com/?key=4933a9d306367800&format=JSON&version=1")
    forecast_pgble = json.loads(response.text)

    global number_of_sites
    number_of_sites =len(forecast_pgble[paralert_tool.date_N_day_after(1)])
    
    return forecast_pgble

        
def get_paraglidable_score(json, site):

    """ get scores in json file """
    tm_fly = json[paralert_tool.date_N_day_after(1)][site]['forecast']['fly']
    tm_XC = json[paralert_tool.date_N_day_after(1)][site]['forecast']['XC']
    atm_fly = json[paralert_tool.date_N_day_after(2)][site]['forecast']['fly']
    atm_XC = json[paralert_tool.date_N_day_after(2)][site]['forecast']['XC']
       
    """ Score : mean of the 'XC' and 'fly' score """
    tomorrow_score = numpy.mean([tm_fly,tm_XC])
    after_tomorrow_score = numpy.mean([atm_fly,atm_XC])
    
    """ Manage score to print note xx/10 """
    tm_score_10 = int(tomorrow_score * 10)
    atm_score_10 = int(after_tomorrow_score * 10)
    
    site_name = json[paralert_tool.date_N_day_after(1)][site]['name']
    
    result_table = [site_name, tm_score_10, atm_score_10]
    return result_table


def get_paraglidable_all_scores(pgble_json):
    
        table = []
    
        """ range depend of the number of sites in paraglidable json file """
        for x in range(0, number_of_sites):
            table.append(get_paraglidable_score(pgble_json, x))

        return table

