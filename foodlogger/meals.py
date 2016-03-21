# meals.py


import datetime


# Choose a meal based on time -
# 3am - 10am - Breakfast
# 10am - noon - Snack 1
# noon - 2pm - Lunch
# 2pm - 5pm - Snack 2
# 5pm - 8pm - Dinner
# 8pm - 3am - Snack 3

def get_default_meal(timestamp=datetime.datetime.now()):
    if timestamp.hour < 3:
        return "Snack 3"
    elif timestamp.hour < 10:
        return "Breakfast"
    elif timestamp.hour < 12:
        return "Snack 1"
    elif timestamp.hour < 14:
        return "Lunch"
    elif timestamp.hour < 17:
        return "Snack 2"
    elif timestamp.hour < 20:
        return "Dinner"
    else:
        return "Snack 3"
