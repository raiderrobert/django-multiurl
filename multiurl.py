from __future__ import unicode_literals

try:
    from django import urls as urlresolvers
    from django.urls.resolvers import RegexPattern
except ImportError:
    # Fallbacks and mocks for Django 1.*
    from django.core import urlresolvers

    urlresolvers.URLResolver = urlresolvers.RegexURLResolver

    def RegexPattern(pattern):
        return pattern


class ContinueResolving(Exception):
    pass


def multiurl(*urls, **kwargs):
    exceptions = kwargs.get('catch', (ContinueResolving,))
    return MultiRegexURLResolver(urls, exceptions)


class MultiRegexURLResolver(urlresolvers.URLResolver):
    def __init__(self, urls, exceptions):
        super(MultiRegexURLResolver, self).__init__(RegexPattern(''), None)
        self._urls = urls
        self._exceptions = exceptions

    @property
    def url_patterns(self):
        return self._urls

    def resolve(self, path):
        tried = []
        matched = []
        patterns_matched = []

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
                patterns_matched.append([pattern])
            tried.append([pattern])
        if matched:
            return MultiResolverMatch(matched, self._exceptions, patterns_matched, path)
        raise urlresolvers.Resolver404({'tried': tried, 'path': path})


class MultiResolverMatch(object):
    def __init__(self, matches, exceptions, patterns_matched, path, route='', tried=None):
        self.matches = matches
        self.exceptions = exceptions
        self.patterns_matched = patterns_matched
        self.path = path
        self.route = route
        self.tried = tried

        # Attributes to emulate ResolverMatch
        self.kwargs = {}
        self.args = ()
        self.url_name = None
        self.app_names = []
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
            raise urlresolvers.Resolver404({'tried': self.patterns_matched, 'path': self.path})
        multiview.multi_resolver_match = self
        return multiview
