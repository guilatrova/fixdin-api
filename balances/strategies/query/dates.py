from .BaseStrategy import BaseStrategy
from .based import EFFECTIVE, REAL, BOTH

class OnDateStrategy(BaseStrategy):
    """
    Filters query to care about one date only
    """
    def __init__(self, date, based):
        """
        Initializes strategy class

        :param date: Which date should be used
        :param based: String determines whether date field should be due_date or payment_date
        """
        self.date = date
        self.based = based

    def apply(self, query):
        kwargs = { self.based: self.date }
        return query.filter(**kwargs)

class BetweenDateStrategy(BaseStrategy):
    """
    Filters query to care about a date range
    """
    def __init__(self, from_date, until_date, based):
        """
        Initializes strategy class

        :param from_date: When it starts
        :param until_date: When it ends
        :param based: String determines whether date field should be due_date or payment_date
        """
        self.from_date = from_date
        self.until_date = until_date
        self.based = based


    def apply(self, query):
        if self.based == EFFECTIVE:
            return query.expires_between(self.from_date, self.until_date)
        
        if self.based == REAL:
            return query.payed_between(self.from_date, self.until_date)
        
        #Used only for complete format balance
        return query.in_date_range(self.from_date, self.until_date)

class UntilDateStrategy(BaseStrategy):
    """
    Filters query to a limit date only
    """
    def __init__(self, until_date, based):
        """
        Initializes strategy class

        :param until_date: When it ends
        :param based: String determines whether date field should be due_date or payment_date
        """
        self.until_date = until_date
        self.based = based

    def apply(self, query):
        key = "{}__lte".format(self.based)
        kwargs = { key: self.until_date }
        return query.filter(**kwargs)
