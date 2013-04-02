from __future__ import unicode_literals

from django.core import urlresolvers

class ContinueResolving(Exception):
    pass

def multiurl(*urls, **kwargs):
    exceptions = kwargs.get('catch', (ContinueResolving,))
    return MultiRegexURLResolver(urls, exceptions)

class MultiRegexURLResolver(urlresolvers.RegexURLResolver):
    def __init__(self, urls, exceptions):
        super(MultiRegexURLResolver, self).__init__('', None)
        self._urls = urls
        self._exceptions = exceptions

    @property
    def url_patterns(self):
        return self._urls

    def resolve(self, path):
        tried = []
        matched = []

        # This is a simplified version of RegexURLResolver. It doesn't
        # support a regex prefix, and it doesn't need to handle include(),
        # so it's simplier, but otherwise this is mostly a copy/paste.
        for pattern in self.url_patterns:
            sub_match = pattern.resolve(path)
            if sub_match:
                # Here's the part that's different: instead of returning the
                # first match, build up a list of all matches.
                rm = urlresolvers.ResolverMatch(sub_match.func, sub_match.args, sub_match.kwargs, sub_match.url_name)
                matched.append(rm)
            tried.append([pattern])
        if matched:
            return MultiResolverMatch(matched, self._exceptions)
        raise urlresolvers.Resolver404({'tried': tried, 'path': path})

class MultiResolverMatch(object):
    def __init__(self, matches, exceptions):
        self.matches = matches
        self.exceptions = exceptions

        # Attributes to emulate ResolverMatch
        self.kwargs = {}
        self.args = []
        self.url_name = None
        self.app_name = None
        self.namespaces = []

    @property
    def func(self):
        def multiview(request):
            for i, match in enumerate(self.matches):
                try:
                    return match.func(request, *match.args, **match.kwargs)
                except self.exceptions:
                    continue
            raise urlresolvers.Resolver404()
        return multiview
