import unittest

from django.conf.urls.i18n import i18n_patterns
from django.http import Http404, HttpResponse
from django.test import Client, SimpleTestCase, override_settings
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
from django.views.decorators.csrf import csrf_exempt

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

    def test_inner_positional_args_kept_with_extra_kwargs(self):
        # Matches plain Django: an extra-kwargs dict doesn't drop the
        # pattern's own unnamed groups.
        response = self.client.get("/d/i/")
        self.assertEqual(response.content, b"args=('i',) kwargs={'d': 1}")

    def test_inner_positional_args_kept_with_outer_named_prefix(self):
        response = self.client.get("/p/sec/i/")
        self.assertEqual(response.content, b"args=('i',) kwargs={'section': 'sec'}")

    def test_async_views(self):
        self.assertEqual(self.client.get("/a/x/").content, b"Async B: x")
        self.assertEqual(self.client.get("/a/jane/").content, b"Async A: jane")

    async def test_async_views_async_client(self):
        response = await self.async_client.get("/a/x/")
        self.assertEqual(response.content, b"Async B: x")

    def test_mixed_sync_and_async_views(self):
        self.assertEqual(self.client.get("/m/x/").content, b"Async B: x")
        self.assertEqual(self.client.get("/m/jane/").content, b"Person: Jane Doe")

    def test_async_views_all_continue_is_404(self):
        self.assertEqual(self.client.get("/an/zzz/").status_code, 404)

    @override_settings(MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"])
    def test_csrf_exempt_when_all_views_exempt(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/csrf/x/").status_code, 200)

    @override_settings(MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"])
    def test_csrf_enforced_when_any_view_not_exempt(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/csrf-mixed/x/").status_code, 403)

    def test_login_not_required_when_all_views_opt_out(self):
        self.assertIs(resolve("/public/x/").func.login_required, False)
        self.assertTrue(getattr(resolve("/top/x/").func, "login_required", True))


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


def echo_args(request, *args, **kwargs):
    return HttpResponse(f"args={args!r} kwargs={kwargs!r}")


async def async_a(request, name):
    if name == "jane":
        return HttpResponse(f"Async A: {name}")
    raise ContinueResolving


async def async_b(request, name):
    return HttpResponse(f"Async B: {name}")


async def async_never(request, name):
    raise ContinueResolving


@csrf_exempt
def exempt_a(request, name):
    raise ContinueResolving


@csrf_exempt
def exempt_b(request, name):
    return HttpResponse("exempt")


def public_view(request, name):
    return HttpResponse("public")


# What @login_not_required sets (Django 5.1+).
public_view.login_required = False  # ty: ignore[missing-attribute]


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
    path("d/", include([multiurl(re_path(r"^(\w+)/$", echo_args, {"d": 1}))])),
    path(
        "p/<str:section>/",
        include([multiurl(re_path(r"^(\w+)/$", echo_args))]),
    ),
    path(
        "a/",
        include([multiurl(path("<str:name>/", async_a), path("<str:name>/", async_b))]),
    ),
    path(
        "an/",
        include(
            [multiurl(path("<str:name>/", async_a), path("<str:name>/", async_never))]
        ),
    ),
    path(
        "m/",
        include([multiurl(path("<str:name>/", person), path("<str:name>/", async_b))]),
    ),
    path(
        "csrf/",
        include(
            [multiurl(path("<str:name>/", exempt_a), path("<str:name>/", exempt_b))]
        ),
    ),
    path(
        "csrf-mixed/",
        include([multiurl(path("<str:name>/", exempt_a), path("<str:name>/", thing))]),
    ),
    path(
        "public/",
        include(
            [
                multiurl(
                    path("<str:name>/", public_view), path("<str:name>/", public_view)
                )
            ]
        ),
    ),
]
