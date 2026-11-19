import django
from django.conf import settings


def pytest_configure() -> None:
    if not settings.configured:
        settings.configure(
            ROOT_URLCONF="tests",
            ALLOWED_HOSTS=["testserver"],
            SECRET_KEY="django-multiurl-tests",
            MIDDLEWARE=[],
            USE_I18N=True,
        )
        django.setup()
