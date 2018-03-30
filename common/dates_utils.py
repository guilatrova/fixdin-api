import calendar
from datetime import date

def get_last_day_of(datein):
    days_count = calendar.monthrange(datein.year, datein.month)[1]
    return date(datein.year, datein.month, days_count)

def get_start_end_month(date):
    start = date.replace(day=1)
    week, days_amount = calendar.monthrange(start.year, start.month)
    end = start.replace(day=days_amount)

    return (start, end)