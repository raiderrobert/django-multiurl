from __future__ import unicode_literals

import unittest

from django.conf import settings
from django.conf.urls import url
from django.conf.urls.i18n import i18n_patterns
from django.http import HttpResponse
from django.urls import path

from multiurl import ContinueResolving, multiurl

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

        self.patterns_pathall = urlresolvers.URLResolver(RegexPattern(r'^/'), i18n_patterns(
            multiurl(
                path('<str:name>/', brand, name='brand'),
                path('<str:name>/', model, name='model'),
            ),
        ))


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

    def test_resolve_match_path_brand(self):
        m = self.patterns_pathall.resolve('/en-us/bmw/')
        response = m.func(request=None, *m.args, **m.kwargs)
        self.assertEqual(response.content, b"Brand: BMW Series")

    def test_resolve_match_path_model(self):
        m = self.patterns_pathall.resolve('/en-us/x5/')
        response = m.func(request=None, *m.args, **m.kwargs)
        self.assertEqual(response.content, b"Model: X5 2019")

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


def brand(request, name):
    brand = {
        'bmw': 'BMW Series',
    }
    if name in brand:
        return HttpResponse("Brand: " + brand[name])
    raise ContinueResolving


def model(request, name):
    model = {
        'x5': 'X5 2019',
    }
    if name in model:
        return HttpResponse("Model: " + model[name])
    raise ContinueResolving


if __name__ == '__main__':
    settings.configure()
    unittest.main()
