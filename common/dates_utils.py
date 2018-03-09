import calendar
from datetime import date

def get_last_day_of(datein):
    days_count = calendar.monthrange(datein.year, datein.month)[1]
    return date(datein.year, datein.month, days_count)