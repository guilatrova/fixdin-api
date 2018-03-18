from django.urls import reverse, resolve

class UrlsTestHelper:
    def resolve_by_name(self, name, **kwargs): 
        url = reverse(name, kwargs=kwargs)
        return resolve(url)