from .resolvers import MultiRegexURLResolver, MultiResolverMatch


class ContinueResolving(Exception):
    pass


def multiurl(*urls, **kwargs):
    exceptions = kwargs.get("catch", (ContinueResolving,))
    return MultiRegexURLResolver(urls, exceptions)
