from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList

class SerializerMayReturnListMixin:
    @property
    def data(self):
        if hasattr(self, 'initial_data') and not hasattr(self, '_validated_data'):
            msg = (
                'When a serializer is passed a `data` keyword argument you '
                'must call `.is_valid()` before attempting to access the '
                'serialized `.data` representation.\n'
                'You should either call `.is_valid()` first, '
                'or access `.initial_data` instead.'
            )
            raise AssertionError(msg)

        if not hasattr(self, '_data'):
            if self.instance is not None and not getattr(self, '_errors', None):
                self._data = self.to_representation(self.instance)
            elif hasattr(self, '_validated_data') and not getattr(self, '_errors', None):
                self._data = self.to_representation(self.validated_data)
            else:
                self._data = self.get_initial()        
        
        if hasattr(self, '_validated_data') and self.is_return_data_list(self._validated_data):
            return ReturnList(self._data, serializer=self)
        return ReturnDict(self._data, serializer=self)

    def to_representation(self, value):
        if isinstance(value, list):
            return [super(SerializerMayReturnListMixin, self).to_representation(x) for x in value]

        return super(SerializerMayReturnListMixin, self).to_representation(value)