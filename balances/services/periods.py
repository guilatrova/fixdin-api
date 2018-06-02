import calendar
import datetime


def get_current_period():
    return get_period_from(datetime.date.today())

def get_period_from(date):
    if date:
        start = date.replace(day=1)
        week, days_amount = calendar.monthrange(start.year, start.month)
        end = start.replace(day=days_amount)

        return (start, end)
    return None
