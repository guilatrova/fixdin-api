from django.urls import resolve, reverse


class UrlsTestHelper:
    def resolve_by_name(self, name, **kwargs): 
        url = reverse(name, kwargs=kwargs)
        return resolve(url)

    def assert_has_actions(self, allowed, actions):
        self.assertEqual(len(allowed), len(actions))

        for allows in allowed:
            self.assertIn(allows, actions)
    
    def assert_resolves_actions(self, resolver, actions_map):
        for key, value in actions_map.items():
            self.assertIn(key, resolver.func.actions)
            self.assertEqual(value, resolver.func.actions[key])

class SerializerTestHelper:
    def assert_has_field_error(self, serializer, key='non_field_errors'):
        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 1)
        self.assertIn(key, serializer.errors)

    def get_data(self, **kwargs):
        data = self.serializer_data
        data.update(kwargs)
        return data

    def get_context(self, **kwargs):
        context = self.serializer_context
        context.update(kwargs)
        return context
