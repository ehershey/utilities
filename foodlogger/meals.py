# meals.py


import datetime


def get_default_meal(timestamp=datetime.datetime.now()):
    # Before noon is breakfast
    #
    if timestamp.hour < 12:
        return "breakfast"
    # Before 5pm is lunch
    #
    elif timestamp.hour < 17:
        return "lunch"
    # 5 and later is dinner
    else:
        return "dinner"
