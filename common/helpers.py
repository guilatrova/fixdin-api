class Struct:
    '''
    Makes dictionary to be acessible as objects.
    item['value'] can be used like item.value
    '''

    def __init__(self, **entries):
        self.__dict__.update(entries)
