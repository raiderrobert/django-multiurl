from asgiref.sync import iscoroutinefunction, sync_to_async
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
        # so it's simpler, but otherwise this mirrors Django's version.
        for pattern in self.url_patterns:
            try:
                sub_match = pattern.resolve(path)
            except Resolver404:
                sub_match = None
            if sub_match:
                # Here's the part that's different: instead of returning the
                # first match, build up a list of all matches.
                matched.append(sub_match)
                patterns_matched.append([pattern])
            tried.append([pattern])
        if matched:
            return MultiResolverMatch(matched, self._exceptions, patterns_matched, path)
        raise Resolver404({"tried": tried, "path": path})


class MultiResolverMatch:
    def __init__(
        self,
        matches: list[ResolverMatch],
        exceptions,
        patterns_matched,
        path,
        route=None,
        tried=None,
        captured_kwargs=None,
        extra_kwargs=None,
    ):
        self.matches = matches
        self.exceptions = exceptions
        self.patterns_matched = patterns_matched
        self.path = path
        # Every match resolved the same path, so report the first one's route
        # (Django joins it with any outer include() prefix).
        self.route = route if route is not None else (matches[0].route or "")
        self.tried = tried

        # Attributes to emulate ResolverMatch. Each sub-match carries its own
        # args/kwargs, so the outer resolver only contributes prefix kwargs.
        self.kwargs = {}
        self.args = ()
        self.captured_kwargs = captured_kwargs if captured_kwargs is not None else {}
        self.extra_kwargs = extra_kwargs if extra_kwargs is not None else {}
        self.url_name = None
        self.app_names = []
        self.app_name = None
        self.namespaces = []

    def _view_arguments(self, match, args, kwargs):
        # args/kwargs come from enclosing patterns, e.g. the <section> in
        # path("<str:section>/", include([multiurl(...)])). Same rule as
        # Django's URLResolver: if there are any kwargs, the outer positional
        # args are dropped, but the sub-pattern's own args are kept.
        view_kwargs = {**kwargs, **match.kwargs}
        view_args = tuple(match.args) if view_kwargs else args + tuple(match.args)
        return view_args, view_kwargs

    def _not_found(self):
        return Resolver404({"tried": self.patterns_matched, "path": self.path})

    @property
    def func(self):
        funcs = [match.func for match in self.matches]

        if any(iscoroutinefunction(f) for f in funcs):

            async def multiview(request, *args, **kwargs):
                for match in self.matches:
                    view_args, view_kwargs = self._view_arguments(match, args, kwargs)
                    view = match.func
                    if not iscoroutinefunction(view):
                        view = sync_to_async(view)
                    try:
                        return await view(request, *view_args, **view_kwargs)
                    except self.exceptions:
                        continue
                raise self._not_found()

        else:

            def multiview(request, *args, **kwargs):
                for match in self.matches:
                    view_args, view_kwargs = self._view_arguments(match, args, kwargs)
                    try:
                        return match.func(request, *view_args, **view_kwargs)
                    except self.exceptions:
                        continue
                raise self._not_found()

        attrs = {"multi_resolver_match": self}
        # Middleware only sees multiview, so carry over view-decorator flags,
        # but only where every sub-view agrees (otherwise keep the safe default).
        if all(getattr(f, "csrf_exempt", False) for f in funcs):
            attrs["csrf_exempt"] = True
        if all(getattr(f, "login_required", True) is False for f in funcs):
            attrs["login_required"] = False
        multiview.__dict__.update(attrs)
        return multiview
