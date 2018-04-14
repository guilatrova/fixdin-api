class QueryStrategy:
    def __init__(self, query, date_strategy):
        self.query = query
        self.date_strategy = date_strategy

    def generate(self):        
        self.date_strategy.apply(self.query)

class OnDateStrategy:
    def __init__(self, date):
        self.date = date
