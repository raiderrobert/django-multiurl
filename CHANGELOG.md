# Changelog

## [2.0.0](https://github.com/raiderrobert/django-multiurl/compare/v1.5.0...v2.0.0) (2026-11-20)


### ⚠ BREAKING CHANGES

* requires Python >= 3.10 and Django >= 4.2; `multiurl()` rejects keyword arguments other than `catch`. Version 2.0.0.

### Bug Fixes

* make view dispatch match Django's resolver semantics ([#48](https://github.com/raiderrobert/django-multiurl/issues/48)) ([04e2a4e](https://github.com/raiderrobert/django-multiurl/commit/04e2a4e3bb1ef4c4cbd64e0eb4dc868983fcd724))
* support Django 4.1+ resolver match attributes ([#45](https://github.com/raiderrobert/django-multiurl/issues/45)) ([6ad4246](https://github.com/raiderrobert/django-multiurl/commit/6ad4246c305a95ca309fbd11199e936333b37fbc))


### Build System

* fix packaging and move tooling to uv, pytest, ruff, ty ([#46](https://github.com/raiderrobert/django-multiurl/issues/46)) ([831c79a](https://github.com/raiderrobert/django-multiurl/commit/831c79ab41d69e51bfea509c5f408ca54bb7a392))
