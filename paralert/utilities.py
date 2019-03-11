from datetime import datetime, timedelta

def date_N_day_after(N):
    
    tomorrow = datetime.now() + timedelta(days=N)

    return tomorrow.strftime("%Y-%m-%d")
    
    