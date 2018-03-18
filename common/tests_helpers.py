from django.urls import reverse, resolve

class UrlsTestHelper:
    def resolve_by_name(self, name, **kwargs): 
        url = reverse(name, kwargs=kwargs)
        return resolve(url)

    def assert_has_actions(self, allowed, actions):
        self.assertEqual(len(allowed), len(actions))

        for allows in allowed:
            self.assertIn(allows, actions)