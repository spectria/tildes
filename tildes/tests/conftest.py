# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from http.cookiejar import CookieJar

from pyramid import testing
from pyramid.paster import get_app, get_appsettings
from pytest import fixture
from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from testing.redis import RedisServer
from webtest import TestApp

from scripts.initialize_db import create_tables
from tildes.models.group import Group
from tildes.models.user import User


# include the fixtures defined in fixtures.py
pytest_plugins = ["tests.fixtures"]


# Extra environment setup for webtest TestApps:
#   - wsgi.url_scheme: needed for secure cookies from the session library
#   - tm.active: setting to True effectively disables pyramid_tm, which fixes an issue
#     with webtest fixtures failing to rollback data after the tests are complete
#   - REMOTE_ADDR: must be defined for logging to work
WEBTEST_EXTRA_ENVIRON = {
    "wsgi.url_scheme": "https",
    "tm.active": True,
    "REMOTE_ADDR": "0.0.0.0",
}


class NestedSessionWrapper(Session):
    """Wrapper that starts a new nested transaction on commit/rollback."""

    def commit(self):
        """Commit the transaction, then start a new nested one."""
        super().commit()
        self.begin_nested()

    def rollback(self):
        """Rollback the transaction, then start a new nested one."""
        super().rollback()
        self.begin_nested()

    def rollback_all_nested(self):
        """Rollback all nested transactions to return to "top-level"."""
        while self.transaction.parent:
            super().rollback()


@fixture(scope="session", autouse=True)
def pyramid_config():
    """Set up the Pyramid environment."""
    settings = get_appsettings("development.ini")
    config = testing.setUp(settings=settings)
    config.include("tildes.auth")

    yield config

    testing.tearDown()


@fixture(scope="session", autouse=True)
def overall_db_session(pyramid_config):
    """Handle setup and teardown of test database for testing session."""
    # read the database url from the pyramid INI file, and replace the db name
    sqlalchemy_url = pyramid_config.registry.settings["sqlalchemy.url"]
    parsed_url = make_url(sqlalchemy_url)
    parsed_url.database = "tildes_test"

    engine = create_engine(parsed_url)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    create_tables(session.connection())

    # SQL init scripts need to be executed "manually" instead of using psql like the
    # normal database init process does, since the tables only exist inside this
    # transaction
    init_scripts_dir = "sql/init/"
    for root, _, files in os.walk(init_scripts_dir):
        sql_files = [filename for filename in files if filename.endswith(".sql")]
        for sql_file in sql_files:
            with open(os.path.join(root, sql_file)) as current_file:
                session.execute(current_file.read())

    # convert the Session to the wrapper class to enforce staying inside nested
    # transactions in the test functions
    session.__class__ = NestedSessionWrapper

    yield session

    # "Teardown" code at the end of testing session
    session.__class__ = Session
    session.rollback()


@fixture(scope="session")
def sdb(overall_db_session):
    """Testing-session-level db session with a nested transaction."""
    overall_db_session.begin_nested()

    yield overall_db_session

    overall_db_session.rollback_all_nested()


@fixture(scope="function")
def db(overall_db_session):
    """Function-level db session with a nested transaction."""
    overall_db_session.begin_nested()

    yield overall_db_session

    overall_db_session.rollback_all_nested()


@fixture(scope="session", autouse=True)
def overall_redis_session():
    """Create a session-level connection to a temporary redis server."""
    # list of redis modules that need to be loaded (would be much nicer to do this
    # automatically somehow, maybe reading from the real redis.conf?)
    redis_modules = ["/opt/redis-cell/libredis_cell.so"]

    with RedisServer() as temp_redis_server:
        redis = Redis(**temp_redis_server.dsn())

        for module in redis_modules:
            redis.execute_command("MODULE LOAD", module)

        yield redis


@fixture(scope="function")
def redis(overall_redis_session):
    """Create a function-level redis connection that wipes the db after use."""
    yield overall_redis_session

    overall_redis_session.flushdb()


@fixture(scope="session", autouse=True)
def session_user(sdb):
    """Create a user named 'SessionUser' in the db for test session."""
    # note that some tests may depend on this username/password having these specific
    # values, so make sure to search for and update those tests if you change the
    # username or password for any reason
    user = User("SessionUser", "session user password")
    sdb.add(user)
    sdb.commit()

    yield user


@fixture(scope="session", autouse=True)
def session_user2(sdb):
    """Create a second user named 'OtherUser' in the db for test session.

    This is useful for cases where two different users are needed, such as when testing
    private messages.
    """
    user = User("OtherUser", "other user password")
    sdb.add(user)
    sdb.commit()

    yield user


@fixture(scope="session", autouse=True)
def session_group(sdb):
    """Create a group named 'sessiongroup' in the db for test session."""
    group = Group("sessiongroup")
    sdb.add(group)
    sdb.commit()

    yield group


@fixture(scope="session")
def base_app(overall_redis_session, sdb):
    """Configure a base WSGI app that webtest can create TestApps based on."""
    testing_app = get_app("development.ini")

    # replace the redis connection used by the redis-sessions library with a connection
    # to the temporary server for this test session
    testing_app.app.registry._redis_sessions = overall_redis_session

    def redis_factory(request):
        return overall_redis_session

    testing_app.app.registry["redis_connection_factory"] = redis_factory

    # replace the session factory function with one that will return the testing db
    # session (inside a nested transaction)
    def session_factory():
        return sdb

    testing_app.app.registry["db_session_factory"] = session_factory

    yield testing_app


@fixture(scope="session")
def webtest(base_app):
    """Create a webtest TestApp and log in as the SessionUser account in it."""
    app = TestApp(base_app, extra_environ=WEBTEST_EXTRA_ENVIRON, cookiejar=CookieJar())

    # fetch the login page, fill in the form, and submit it (sets the cookie)
    login_page = app.get("/login")
    login_page.form["username"] = "SessionUser"
    login_page.form["password"] = "session user password"
    login_page.form.submit()

    yield app


@fixture(scope="session")
def webtest_loggedout(base_app):
    """Create a logged-out webtest TestApp (no cookies retained)."""
    yield TestApp(base_app, extra_environ=WEBTEST_EXTRA_ENVIRON)
