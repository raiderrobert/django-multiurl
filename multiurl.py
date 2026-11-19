from django.urls import Resolver404, ResolverMatch, URLResolver
from django.urls.resolvers import RegexPattern
from django.utils.functional import cached_property


class ContinueResolving(Exception):
    pass


def multiurl(*urls, catch=(ContinueResolving,)):
    return MultiRegexURLResolver(urls, catch)


class MultiRegexURLResolver(URLResolver):
    def __init__(self, urls, exceptions):
        super().__init__(RegexPattern(""), None)
        self._urls = urls
        self._exceptions = exceptions

    @cached_property
    def url_patterns(self):
        return self._urls

    def resolve(self, path):
        tried = []
        matched = []
        patterns_matched = []

        # This is a simplified version of URLResolver.resolve. It doesn't
        # support a regex prefix, and it doesn't need to handle include(),
        # so it's simpler, but otherwise this is mostly a copy/paste.
        for pattern in self.url_patterns:
            sub_match = pattern.resolve(path)
            if sub_match:
                # Here's the part that's different: instead of returning the
                # first match, build up a list of all matches.
                rm = ResolverMatch(
                    sub_match.func, sub_match.args, sub_match.kwargs, sub_match.url_name
                )
                matched.append(rm)
                patterns_matched.append([pattern])
            tried.append([pattern])
        if matched:
            return MultiResolverMatch(matched, self._exceptions, patterns_matched, path)
        raise Resolver404({"tried": tried, "path": path})


class MultiResolverMatch:
    def __init__(
        self,
        matches,
        exceptions,
        patterns_matched,
        path,
        route="",
        tried=None,
        captured_kwargs=None,
        extra_kwargs=None,
    ):
        self.matches = matches
        self.exceptions = exceptions
        self.patterns_matched = patterns_matched
        self.path = path
        self.route = route
        self.tried = tried
        # Read by URLResolver.resolve() since Django 4.1.
        self.captured_kwargs = captured_kwargs if captured_kwargs is not None else {}
        self.extra_kwargs = extra_kwargs if extra_kwargs is not None else {}

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
            for match in self.matches:
                try:
                    return match.func(request, *match.args, **match.kwargs)
                except self.exceptions:
                    continue
            raise Resolver404({"tried": self.patterns_matched, "path": self.path})

        multiview.multi_resolver_match = self  # ty: ignore[missing-attribute]
        return multiview
