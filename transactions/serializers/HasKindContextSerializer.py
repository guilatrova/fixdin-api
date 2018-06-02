class HasKindContextSerializer:
    def get_kind(self, obj):
        return self.context['kind']
