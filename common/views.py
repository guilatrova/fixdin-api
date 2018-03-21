from rest_framework.response import Response

class PatchModelListMixin:
    """
    Patch a list of instances passed by "?ids=1,2,3" on query params.
    """

    def partial_update_list(self, request, *args, **kwargs):
        param_ids = self.request.query_params.get('ids', False)
        if param_ids:
            ids = param_ids.split(',')
            queryset = self.get_queryset().filter(id__in=ids)
            filtered = self.filter_queryset(queryset)
            to_return = self.perform_partial_update_list(request.data, filtered)

            return Response(to_return)

        return Response(status=status.HTTP_404_NOT_FOUND)

    def perform_partial_update_list(self, data, instances):
        to_return = []

        for instance in instances:
            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            to_return.append(serializer.data)

        return to_return