import unittest

from django.conf.urls.i18n import i18n_patterns
from django.http import Http404, HttpResponse
from django.test import SimpleTestCase
from django.urls import (
    NoReverseMatch,
    Resolver404,
    URLResolver,
    include,
    path,
    re_path,
    resolve,
    reverse,
)
from django.urls.resolvers import RegexPattern
from django.views import View

from multiurl import ContinueResolving, multiurl


class MultiviewTests(unittest.TestCase):
    def setUp(self):
        # Patterns with a "catch all" view (thing) at the end.
        self.patterns_catchall = URLResolver(
            RegexPattern(r"^/"),
            [
                multiurl(
                    re_path(r"^(\w+)/$", person, name="person"),
                    re_path(r"^(\w+)/$", place, name="place"),
                    re_path(r"^(\w+)/$", thing, name="thing"),
                )
            ],
        )

        self.patterns_pathall = URLResolver(
            RegexPattern(r"^/"),
            i18n_patterns(
                multiurl(
                    path("<str:name>/", brand, name="brand"),
                    path("<str:name>/", model, name="model"),
                ),
            ),
        )

        # Patterns with no "catch all" - last view could still raise ContinueResolving.
        self.patterns_no_fallthrough = URLResolver(
            RegexPattern(r"^/"),
            [
                multiurl(
                    re_path(r"^(\w+)/$", person, name="person"),
                    re_path(r"^(\w+)/$", place, name="place"),
                )
            ],
        )

    def test_resolve_match_first(self):
        m = self.patterns_catchall.resolve("/jane/")
        response = m.func(None, *m.args, **m.kwargs)
        self.assertEqual(response.content, b"Person: Jane Doe")

    def test_resolve_match_middle(self):
        m = self.patterns_catchall.resolve("/sf/")
        response = m.func(None, *m.args, **m.kwargs)
        self.assertEqual(response.content, b"Place: San Francisco")

    def test_resolve_match_last(self):
        m = self.patterns_catchall.resolve("/bacon/")
        response = m.func(None, *m.args, **m.kwargs)
        self.assertEqual(response.content, b"Thing: Bacon")

    def test_resolve_match_path_brand(self):
        m = self.patterns_pathall.resolve("/en-us/bmw/")
        response = m.func(None, *m.args, **m.kwargs)
        self.assertEqual(response.content, b"Brand: BMW Series")

    def test_resolve_match_path_model(self):
        m = self.patterns_pathall.resolve("/en-us/x5/")
        response = m.func(None, *m.args, **m.kwargs)
        self.assertEqual(response.content, b"Model: X5 2019")

    def test_resolve_match_faillthrough(self):
        m = self.patterns_no_fallthrough.resolve("/bacon/")
        with self.assertRaises(Resolver404):
            m.func(None, *m.args, **m.kwargs)

    def test_no_match(self):
        with self.assertRaises(Resolver404):
            self.patterns_catchall.resolve("/eggs/and/bacon/")

    def test_reverse(self):
        self.assertEqual("joe/", self.patterns_catchall.reverse("person", "joe"))
        self.assertEqual("joe/", self.patterns_catchall.reverse("place", "joe"))
        self.assertEqual("joe/", self.patterns_catchall.reverse("thing", "joe"))
        with self.assertRaises(NoReverseMatch):
            self.patterns_catchall.reverse("person")
        with self.assertRaises(NoReverseMatch):
            self.patterns_catchall.reverse("argh", "xyz")


class RequestDispatchTests(SimpleTestCase):
    """End-to-end tests through Django's request handler (ROOT_URLCONF = tests)."""

    def test_client_request_end_to_end(self):
        response = self.client.get("/top/jane/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Person: Jane Doe")

    def test_client_request_falls_through(self):
        response = self.client.get("/top/sf/")
        self.assertEqual(response.content, b"Place: San Francisco")

    def test_client_request_all_continue_is_404(self):
        response = self.client.get("/top/bacon/")
        self.assertEqual(response.status_code, 404)

    def test_namespaced_include_reverse(self):
        self.assertEqual(reverse("ns:person", args=["joe"]), "/ns/joe/")
        self.assertEqual(reverse("ns:place", args=["joe"]), "/ns/joe/")

    def test_namespaced_include_resolve(self):
        match = resolve("/ns/joe/")
        self.assertEqual(match.namespace, "ns")
        self.assertEqual(self.client.get("/ns/nyc/").content, b"Place: New York City")

    def test_outer_prefix_kwargs_passed(self):
        response = self.client.get("/s/news/x/")
        self.assertEqual(response.content, b"Sectioned B: news/x")

    def test_outer_prefix_kwargs_first_view(self):
        response = self.client.get("/s/news/jane/")
        self.assertEqual(response.content, b"Sectioned A: news/jane")

    def test_catch_http404(self):
        response = self.client.get("/h/anything/")
        self.assertEqual(response.content, b"Thing: Anything")

    def test_class_based_view(self):
        response = self.client.get("/c/widget/")
        self.assertEqual(response.content, b"CBV: widget")

    def test_resolver_match_route(self):
        self.assertEqual(resolve("/top/jane/").route, "top/<str:name>/")


#
# Some "views" to test against.
#


def person(request, name):
    people = {
        "john": "John Smith",
        "jane": "Jane Doe",
    }
    if name in people:
        return HttpResponse("Person: " + people[name])
    raise ContinueResolving


def place(request, name):
    places = {
        "sf": "San Francisco",
        "nyc": "New York City",
    }
    if name in places:
        return HttpResponse("Place: " + places[name])
    raise ContinueResolving


def thing(request, name):
    return HttpResponse("Thing: " + name.title())


def brand(request, name):
    brand = {
        "bmw": "BMW Series",
    }
    if name in brand:
        return HttpResponse("Brand: " + brand[name])
    raise ContinueResolving


def model(request, name):
    model = {
        "x5": "X5 2019",
    }
    if name in model:
        return HttpResponse("Model: " + model[name])
    raise ContinueResolving


def sectioned_a(request, section, name):
    if name == "jane":
        return HttpResponse(f"Sectioned A: {section}/{name}")
    raise ContinueResolving


def sectioned_b(request, section, name):
    return HttpResponse(f"Sectioned B: {section}/{name}")


def not_found(request, name):
    raise Http404


class WidgetView(View):
    def get(self, request, name):
        return HttpResponse(f"CBV: {name}")


# ROOT_URLCONF for RequestDispatchTests (see conftest.py).
urlpatterns = [
    path(
        "top/",
        include(
            [
                multiurl(
                    path("<str:name>/", person, name="person"),
                    path("<str:name>/", place, name="place"),
                )
            ]
        ),
    ),
    path(
        "ns/",
        include(
            (
                [
                    multiurl(
                        path("<str:name>/", person, name="person"),
                        path("<str:name>/", place, name="place"),
                    )
                ],
                "app",
            ),
            namespace="ns",
        ),
    ),
    path(
        "s/<str:section>/",
        include(
            [
                multiurl(
                    path("<str:name>/", sectioned_a),
                    path("<str:name>/", sectioned_b),
                )
            ]
        ),
    ),
    path(
        "h/",
        include(
            [
                multiurl(
                    path("<str:name>/", not_found),
                    path("<str:name>/", thing),
                    catch=(Http404, ContinueResolving),
                )
            ]
        ),
    ),
    path(
        "c/",
        include(
            [
                multiurl(
                    path("<str:name>/", person),
                    path("<str:name>/", WidgetView.as_view()),
                )
            ]
        ),
    ),
]
