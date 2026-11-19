# django-multiurl

[![CI](https://github.com/raiderrobert/django-multiurl/actions/workflows/ci.yml/badge.svg)](https://github.com/raiderrobert/django-multiurl/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/django-multiurl.svg)](https://pypi.org/project/django-multiurl/)

Have you ever wanted multiple views to match to the same URL? Now you can.

You may once have tried something like this:

```python
urlpatterns = [
    path("app/<str:name>/", app.views.people),
    path("app/<str:name>/", app.views.place),
]
```

However, if you try this, `/app/san-francisco/` will only map to
`app.views.people`. Raising an `Http404` from `app.views.people` doesn't
help: you only get a 404 in the browser because Django stops resolving
URLs at the first match.

Well, `django-multiurl` solves this problem. Just `pip install django-multiurl`,
then do this:

```python
from django.urls import path
from multiurl import multiurl

urlpatterns = [
    multiurl(
        path("app/<str:name>/", app.views.people),
        path("app/<str:name>/", app.views.place),
    ),
]
```

Now in your views, raise `multiurl.ContinueResolving` anywhere you'd like
to break out of the view and keep resolving. For example, here's what
`app.views.people` might look like:

```python
from multiurl import ContinueResolving


def people(request, name):
    try:
        person = Person.objects.get(name=name)
    except Person.DoesNotExist:
        raise ContinueResolving
    return render(...)
```

That's it! `ContinueResolving` will cause `multiurl` to continue onto the
next view (`app.views.place`, in this example).

A few notes to round things out:

- If you don't want to use `ContinueResolving` (perhaps you'd rather keep
  using `get_object_or_404`, or you're using third-party views that you
  can't modify to raise `ContinueResolving`), you can pass a `catch`
  argument into `multiurl` to control which exceptions are considered
  "continue" statements. For example, to allow `Http404` exceptions to
  continue resolving, do this:

  ```python
  urlpatterns = [
      multiurl(
          path("app/<str:name>/", app.views.people),
          path("app/<str:name>/", app.views.place),
          catch=(Http404, ContinueResolving),
      ),
  ]
  ```

  As you can see, `catch` should be a tuple of exceptions. It's probably a
  good idea to always include `ContinueResolving` in the tuple.

- If the last view in a `multiurl` raises `ContinueResolving` (or another
  "continuing" exception), a 404 will be raised instead. That is, if resolving
  "falls off the end" of some multi-urls, you'll get the 404 you expect.

- `path()` and `re_path()` both work, as does nesting `multiurl` inside
  `include()` (namespaces and captured prefix arguments are passed through).

- Reverse URL resolution just works as expected. Name your sub-URLs and then
  reverse your heart out.

## Supported versions

| django-multiurl | Python      | Django                |
| --------------- | ----------- | --------------------- |
| 2.x             | 3.10 – 3.14 | 4.2, 5.2, 6.0, 6.1    |
| 1.x             | 2.7, 3.4+   | 1.11 – 3.2            |

## Contributing

Development takes place
[on GitHub](https://github.com/raiderrobert/django-multiurl); pull requests
are welcome. The project uses [uv](https://docs.astral.sh/uv/):

```sh
uv run pytest                                      # run the tests
uv run --with "django==5.2.*" pytest               # against a specific Django
uv run ruff check . && uv run ruff format --check . && uv run ty check
```
