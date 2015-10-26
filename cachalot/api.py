# coding: utf-8

from __future__ import unicode_literals

from django.conf import settings
from django.db import connections
from django.utils.six import string_types

from .cache import cachalot_caches
from .utils import _get_table_cache_key, _invalidate_table_cache_keys


__all__ = ('invalidate', 'get_last_invalidation')


def _get_table_cache_keys_per_cache_and_db(tables, cache_alias, db_alias):
    no_tables = not tables
    cache_aliases = settings.CACHES if cache_alias is None else (cache_alias,)
    db_aliases = settings.DATABASES if db_alias is None else (db_alias,)
    for db_alias in db_aliases:
        if no_tables:
            tables = connections[db_alias].introspection.table_names()
        for cache_alias in cache_aliases:
            table_cache_keys = [
                _get_table_cache_key(db_alias, t) for t in tables]
            if table_cache_keys:
                yield cache_alias, db_alias, table_cache_keys


def _get_tables(tables_or_models):
    return [o if isinstance(o, string_types) else o._meta.db_table
            for o in tables_or_models]


def invalidate(*tables_or_models, **kwargs):
    """
    Clears what was cached by django-cachalot implying one or more SQL tables
    or models from ``tables_or_models``.
    If ``tables_or_models`` is not specified, all tables found in the database
    (including those outside Django) are invalidated.

    If ``cache_alias`` is specified, it only clears the SQL queries stored
    on this cache, otherwise queries from all caches are cleared.

    If ``db_alias`` is specified, it only clears the SQL queries executed
    on this database, otherwise queries from all databases are cleared.

    :arg tables_or_models: SQL tables names or models (or combination of both)
    :type tables_or_models: tuple of strings or models
    :arg cache_alias: Alias from the Django ``CACHES`` setting
    :type cache_alias: string or NoneType
    :arg db_alias: Alias from the Django ``DATABASES`` setting
    :type db_alias: string or NoneType
    :returns: Nothing
    :rtype: NoneType
    """
    # TODO: Replace with positional arguments when we drop Python 2 support.
    cache_alias = kwargs.pop('cache_alias', None)
    db_alias = kwargs.pop('db_alias', None)
    for k in kwargs:
        raise TypeError(
            "invalidate() got an unexpected keyword argument '%s'" % k)

    table_cache_keys_per_cache = _get_table_cache_keys_per_cache_and_db(
        _get_tables(tables_or_models), cache_alias, db_alias)
    for cache_alias, db_alias, table_cache_keys in table_cache_keys_per_cache:
        _invalidate_table_cache_keys(
            cachalot_caches.get_cache(cache_alias, db_alias), table_cache_keys)


def get_last_invalidation(*tables_or_models, **kwargs):
    """
    Returns the timestamp of the most recent invalidation of the given
    ``tables_or_models``.  If ``tables_or_models`` is not specified,
    all tables found in the database (including those outside Django) are used.

    If ``cache_alias`` is specified, it only fetches invalidations
    in this cache, otherwise invalidations in all caches are fetched.

    If ``db_alias`` is specified, it only fetches invalidations
    for this database, otherwise invalidations for all databases are fetched.

    :arg tables_or_models: SQL tables names or models (or combination of both)
    :type tables_or_models: tuple of strings or models
    :arg cache_alias: Alias from the Django ``CACHES`` setting
    :type cache_alias: string or NoneType
    :arg db_alias: Alias from the Django ``DATABASES`` setting
    :type db_alias: string or NoneType
    :returns: The timestamp of the most recent invalidation
    :rtype: float
    """
    # TODO: Replace with positional arguments when we drop Python 2 support.
    cache_alias = kwargs.pop('cache_alias', None)
    db_alias = kwargs.pop('db_alias', None)
    for k in kwargs:
        raise TypeError("get_last_invalidation() got an unexpected "
                        "keyword argument '%s'" % k)

    last_invalidation = 0.0
    table_cache_keys_per_cache = _get_table_cache_keys_per_cache_and_db(
        _get_tables(tables_or_models), cache_alias, db_alias)
    for cache_alias, db_alias, table_cache_keys in table_cache_keys_per_cache:
        invalidations = cachalot_caches.get_cache(
            cache_alias, db_alias).get_many(table_cache_keys).values()
        if invalidations:
            current_last_invalidation = max(invalidations)
            if current_last_invalidation > last_invalidation:
                last_invalidation = current_last_invalidation
    return last_invalidation
