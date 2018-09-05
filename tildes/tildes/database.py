# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the database-related config updates and request methods."""

from typing import Callable, Type

from pyramid.config import Configurator
from pyramid.request import Request
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from sqlalchemy.pool import NullPool
from transaction._manager import ThreadTransactionManager
from zope.sqlalchemy import register

from tildes.lib.database import obtain_transaction_lock
from tildes.models import DatabaseModel, ModelQuery
from tildes.models.comment import (
    Comment,
    CommentNotification,
    CommentNotificationQuery,
    CommentQuery,
)
from tildes.models.group import Group, GroupQuery
from tildes.models.topic import Topic, TopicQuery


def obtain_lock(request: Request, lock_space: str, lock_value: int) -> None:
    """Obtain a lock on the combination of lock_space and lock_value."""
    obtain_transaction_lock(request.db_session, lock_space, lock_value)


def query_factory(request: Request, model_cls: Type[DatabaseModel]) -> ModelQuery:
    """Return a ModelQuery or subclass depending on model_cls specified."""
    if model_cls == Comment:
        return CommentQuery(request)
    if model_cls == CommentNotification:
        return CommentNotificationQuery(request)
    elif model_cls == Group:
        return GroupQuery(request)
    elif model_cls == Topic:
        return TopicQuery(request)

    return ModelQuery(model_cls, request)


def get_tm_session(
    session_factory: Callable, transaction_manager: ThreadTransactionManager
) -> Session:
    """Return a db session being managed by the transaction manager."""
    db_session = session_factory()
    register(db_session, transaction_manager=transaction_manager)
    return db_session


def includeme(config: Configurator) -> None:
    """Update the config to attach database-related methods to the request.

    Currently adds:

    * request.db_session - db session for the current request, managed by pyramid_tm.
    * request.query() - a factory method that will return a ModelQuery or subclass for
      querying the model class supplied. This will generally be used generatively,
      similar to standard SQLALchemy session.query(...).
    * request.obtain_lock() - obtains a transaction-level advisory lock from PostgreSQL.
    """
    settings = config.get_settings()

    # Enable pyramid_tm's default_commit_veto behavior, which will abort the transaction
    # if the response code starts with 4 or 5. The main benefit of this is to avoid
    # aborting on exceptions that don't actually indicate a problem, such as a HTTPFound
    # 302 redirect.
    settings["tm.commit_veto"] = "pyramid_tm.default_commit_veto"

    config.include("pyramid_tm")

    # disable SQLAlchemy connection pooling since pgbouncer will handle it
    settings["sqlalchemy.poolclass"] = NullPool

    engine = engine_from_config(settings, "sqlalchemy.")

    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    config.registry["db_session_factory"] = session_factory

    # attach the session to each request as request.db_session
    config.add_request_method(
        lambda request: get_tm_session(
            config.registry["db_session_factory"], request.tm
        ),
        "db_session",
        reify=True,
    )

    config.add_request_method(query_factory, "query")

    config.add_request_method(obtain_lock, "obtain_lock")
