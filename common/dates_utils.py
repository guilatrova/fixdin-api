import calendar
from datetime import date, datetime


def get_last_day_of(datein):
    days_count = calendar.monthrange(datein.year, datein.month)[1]
    return date(datein.year, datein.month, days_count)

def get_start_end_month(datein):
    start = datein.replace(day=1)
    week, days_amount = calendar.monthrange(start.year, start.month)
    end = start.replace(day=days_amount)

    return (start, end)

def get_year_range(datein=None):
    datein = datein or date.today()
    start = datein.replace(day=1, month=1)
    week,  days_amount = calendar.monthrange(start.year, 12)
    end = start.replace(day=days_amount, month=12)

    return (start, end)

def from_str(strin):
    return datetime.strptime(strin, '%Y-%m-%d')
