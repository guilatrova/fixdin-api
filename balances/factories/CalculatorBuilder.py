from balances.services.calculator import Calculator
from balances.strategies.query import (
    based,
    OnDateStrategy,
    BetweenDateStrategy,
    UntilDateStrategy,
    PlainFormatStrategy,
    DetailedFormatStrategy,
    DetailedAccountFormatStrategy,
    CompleteFormatStrategy
)

class CalculatorBuilder:

    def consider(self, based):
        self.based = based
        return self

    def owned_by(self, user_id):
        self.user_id = user_id
        return self

    def on_date(self, date):
        self.date_strategy = OnDateStrategy(data, based=self.based)
        return self

    def between_dates(self, from_date, until_date):
        self.date_strategy = BetweenDateStrategy(from_date, until_date, based=self.based)
        return self

    def until(self, until_date):
        self.date_strategy = UntilDateStrategy(until_date, based=self.based)
        return self

    def as_plain(self, **kwargs):
        self.format_strategy = PlainFormatStrategy(**kwargs)
        return self

    def as_detailed(self):
        self.format_strategy = DetailedFormatStrategy()
        return self

    def as_complete(self):
        self.format_strategy = CompleteFormatStrategy()
        return self

    def as_detailed_accounts(self):
        self.format_strategy = DetailedAccountFormatStrategy(self.user_id)
        return self

    def build(self):
        return Calculator(self.user_id, self.date_strategy, self.format_strategy)