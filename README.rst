django-multiurl
===============
.. image:: https://travis-ci.org/raiderrobert/django-multiurl.svg?branch=master
    :target: http://travis-ci.org/raiderrobert/django-multiurl
.. image:: https://coveralls.io/repos/github/raiderrobert/django-multiurl/badge.svg?branch=master
    :target: https://coveralls.io/github/raiderrobert/django-multiurl?branch=master
    
Have you ever wanted multiple views to match to the same URL? Now you can.

You may once have tried something like this::

    urlpatterns = [
        url('/app/(\w+)/$', app.views.people),
        url('/app/(\w+)/$', app.views.place),
    ]

However, if you try this, ``/app/san-francisco/`` will only map to
``app.views.people``. Raising an ``Http404`` from ``app.views.people`` doesn't
help: you only get a 404 in the browser because Django stops resolving
URLs at the first match.

Well, ``django-multiurl`` solves this problem. Just 
``pip install django-multiurl``, then do this::

    from multiurl import multiurl

    urlpatterns = [
        multiurl(
            url('/app/(\w+)/$', app.views.people),
            url('/app/(\w+)/$', app.views.place),
        )
    ]

Now in your views, raise ``multiurl.ContinueResolving`` anywhere you'd like
to break out of the view and keep resolving. For example, here's what
``app.views.people`` might look like::

    from multiurl import ContinueResolving

    def people(request, name):
        try:
            person = Person.objects.get(name=name)
        except Person.DoesNotExist:
            raise ContinueResolving
        return render(...)

That's it! ``ContinueResolving`` will cause ``multiurl`` to continue onto the
next view (``app.views.place``, in this example).

A few notes to round things out:

* If you don't want to use ``ContinueResolving`` -- perhaps you'd rather
  continue using ``get_object_or_404``, or you're using third-party views
  that you can't modify to raise ``ContinueResolving``, you can pass a
  ``catch`` argument into ``multiurl`` to control which exceptions are
  considered "continue" statements. For example, to allow ``Http404``
  exceptions to continue resolving, do this::

        urlpatterns = [
            multiurl(
                url('/app/(\w+)/$', app.views.people),
                url('/app/(\w+)/$', app.views.place),
                catch = (Http404, ContinueResolving)
            )
        ]

  As you can see, ``catch`` should be a tuple of exceptions. It's probably a
  good idea to always include ``ContinueResolving`` in the tuple.

* If the last view in a ``multiurl`` raises ``ContinueResolving`` (or another
  "continuing" exception), a 404 will be raised instead. That is, if resolving
  "falls off the end" of some multi-urls, you'll get the 404 you expect.

* Reverse URL resolution just works as expected. Name your sub-URLs and then
  reverse your heart out.

Contributing
------------

Development takes place
`on GitHub <http://github.com/jacobian/django-multiurl>`_; pull requests are
welcome. Run tests with `tox <http://tox.readthedocs.org/>`_.
