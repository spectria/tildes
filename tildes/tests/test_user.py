# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from marshmallow.exceptions import ValidationError
from pyramid.security import principals_allowed_by_permission
from pytest import raises
from sqlalchemy.exc import IntegrityError

from tildes.models.user import User
from tildes.schemas.user import PASSWORD_MIN_LENGTH, UserSchema


def test_creation_validates_schema(mocker):
    """Ensure that model creation goes through schema validation."""
    mocker.spy(UserSchema, "validate")
    User("testing", "testpassword")
    call_args = [call[0] for call in UserSchema.validate.call_args_list]
    expected_args = {"username": "testing", "password": "testpassword"}
    assert any(expected_args in call for call in call_args)


def test_too_short_password():
    """Ensure a new user can't be created with a too-short password."""
    password = "x" * (PASSWORD_MIN_LENGTH - 1)
    with raises(ValidationError):
        User("ShortPasswordGuy", password)


def test_matching_password_and_username():
    """Ensure a new user can't be created with same username and password."""
    with raises(ValidationError):
        User("UnimaginativePassword", "UnimaginativePassword")


def test_username_and_password_differ_in_casing():
    """Ensure a user can't be created with name/pass the same except case."""
    with raises(ValidationError):
        User("NobodyWillGuess", "nobodywillguess")


def test_username_contained_in_password():
    """Ensure a user can't be created with the username in the password."""
    with raises(ValidationError):
        User("MyUsername", "iputmyusernameinmypassword")


def test_password_contained_in_username():
    """Ensure a user can't be created with the password in the username."""
    with raises(ValidationError):
        User("PasswordIsVeryGood", "VeryGood")


def test_user_password_check():
    """Ensure checking the password for a new user works correctly."""
    new_user = User("myusername", "mypassword")
    assert new_user.is_correct_password("mypassword")


def test_duplicate_username(db):
    """Ensure two users with the same name can't be created."""
    original = User("Inimitable", "securepassword")
    db.add(original)
    duplicate = User("Inimitable", "adifferentpassword")
    db.add(duplicate)

    with raises(IntegrityError):
        db.commit()


def test_duplicate_username_case_insensitive(db):
    """Ensure usernames only differing in casing can't be created."""
    test_username = "test_user"
    original = User(test_username.lower(), "hackproof")
    db.add(original)
    duplicate = User(test_username.upper(), "sosecure")
    db.add(duplicate)

    with raises(IntegrityError):
        db.commit()


def test_change_password():
    """Ensure changing a user password works as expected."""
    new_user = User("A_New_User", "lovesexsecretgod")

    new_user.change_password("lovesexsecretgod", "lovesexsecretgod1")

    # the old one shouldn't work
    assert not new_user.is_correct_password("lovesexsecretgod")

    # the new one should
    assert new_user.is_correct_password("lovesexsecretgod1")


def test_change_password_to_same(session_user):
    """Ensure users can't "change" to the same password."""
    password = "session user password"
    with raises(ValueError):
        session_user.change_password(password, password)


def test_change_password_wrong_old_one(session_user):
    """Ensure changing password doesn't work if the old one is wrong."""
    with raises(ValueError):
        session_user.change_password("definitely not right", "some new one")


def test_change_password_too_short(session_user):
    """Ensure users can't change password to a too-short one."""
    new_password = "x" * (PASSWORD_MIN_LENGTH - 1)
    with raises(ValidationError):
        session_user.change_password("session user password", new_password)


def test_change_password_to_username(session_user):
    """Ensure users can't change password to the same as their username."""
    with raises(ValidationError):
        session_user.change_password("session user password", session_user.username)


def test_deleted_user_no_message_permission():
    """Ensure nobody can message a deleted user."""
    deleted_user = User("Deleted_User", "password")
    deleted_user.is_deleted = True

    principals = principals_allowed_by_permission(deleted_user, "message")
    assert not principals


def test_banned_user_no_message_permission():
    """Ensure nobody can message a banned user."""
    banned_user = User("Banned_User", "password")
    banned_user.is_banned = True

    principals = principals_allowed_by_permission(banned_user, "message")
    assert not principals


def test_only_admin_has_ban_permission():
    """Ensure only admins have ban permissions."""
    user = User("Test_User", "password")

    principals = principals_allowed_by_permission(user, "ban")
    assert principals == {"admin"}
