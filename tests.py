from __future__ import unicode_literals

import unittest

from django.conf import settings
from django.conf.urls import url

from django.http import HttpResponse

from multiurl import multiurl, ContinueResolving

try:
    from django import urls as urlresolvers
    from django.urls.resolvers import RegexPattern
except ImportError:
    # Fallbacks and mocks for Django 1.*
    from django.core import urlresolvers

    urlresolvers.URLResolver = urlresolvers.RegexURLResolver

    def RegexPattern(pattern):
        return pattern


class MultiviewTests(unittest.TestCase):
    def setUp(self):
        # Patterns with a "catch all" view (thing) at the end.
        self.patterns_catchall = urlresolvers.URLResolver(RegexPattern(r'^/'), [
            multiurl(
                url(r'^(\w+)/$', person, name='person'),
                url(r'^(\w+)/$', place, name='place'),
                url(r'^(\w+)/$', thing, name='thing'),
            )
        ])

        # Patterns with no "catch all" - last view could still raise ContinueResolving.
        self.patterns_no_fallthrough = urlresolvers.URLResolver(RegexPattern(r'^/'), [
            multiurl(
                url(r'^(\w+)/$', person, name='person'),
                url(r'^(\w+)/$', place, name='place'),
            )
        ])

    def test_resolve_match_first(self):
        m = self.patterns_catchall.resolve('/jane/')
        response = m.func(request=None, *m.args, **m.kwargs)
        self.assertEqual(response.content, b"Person: Jane Doe")

    def test_resolve_match_middle(self):
        m = self.patterns_catchall.resolve('/sf/')
        response = m.func(request=None, *m.args, **m.kwargs)
        self.assertEqual(response.content, b"Place: San Francisco")

    def test_resolve_match_last(self):
        m = self.patterns_catchall.resolve('/bacon/')
        response = m.func(request=None, *m.args, **m.kwargs)
        self.assertEqual(response.content, b"Thing: Bacon")

    def test_resolve_match_faillthrough(self):
        m = self.patterns_no_fallthrough.resolve('/bacon/')
        with self.assertRaises(urlresolvers.Resolver404):
            m.func(request=None, *m.args, **m.kwargs)

    def test_no_match(self):
        with self.assertRaises(urlresolvers.Resolver404):
            self.patterns_catchall.resolve('/eggs/and/bacon/')

    def test_reverse(self):
        self.assertEqual('joe/', self.patterns_catchall.reverse('person', 'joe'))
        self.assertEqual('joe/', self.patterns_catchall.reverse('place', 'joe'))
        self.assertEqual('joe/', self.patterns_catchall.reverse('thing', 'joe'))
        with self.assertRaises(urlresolvers.NoReverseMatch):
            self.patterns_catchall.reverse('person')
        with self.assertRaises(urlresolvers.NoReverseMatch):
            self.patterns_catchall.reverse('argh', 'xyz')

#
# Some "views" to test against.
#


def person(request, name):
    people = {
        'john': 'John Smith',
        'jane': 'Jane Doe',
    }
    if name in people:
        return HttpResponse("Person: " + people[name])
    raise ContinueResolving


def place(request, name):
    places = {
        'sf': 'San Francisco',
        'nyc': 'New York City',
    }
    if name in places:
        return HttpResponse("Place: " + places[name])
    raise ContinueResolving


def thing(request, name):
    return HttpResponse("Thing: " + name.title())


if __name__ == '__main__':
    settings.configure()
    unittest.main()
