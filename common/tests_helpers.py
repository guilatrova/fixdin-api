from django.urls import reverse, resolve

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