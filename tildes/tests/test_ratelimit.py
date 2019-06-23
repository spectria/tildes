# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import timedelta
from itertools import permutations
from random import randint

from pytest import raises

from tildes.lib.ratelimit import (
    RATE_LIMITED_ACTIONS,
    RateLimitedAction,
    RateLimitError,
    RateLimitResult,
)


def test_all_rate_limited_action_names_unique():
    """Ensure all the RATE_LIMITED_ACTIONS defined have unique names."""
    seen_names = set()

    for action in RATE_LIMITED_ACTIONS.values():
        assert action.name not in seen_names
        seen_names.add(action.name)


def test_action_with_all_types_disabled():
    """Ensure RateLimitedAction can't have both by_user and by_ip disabled."""
    with raises(ValueError):
        RateLimitedAction("test", timedelta(hours=1), 5, by_user=False, by_ip=False)


def test_check_by_user_id_disabled():
    """Ensure non-by_user RateLimitedAction can't be checked by user_id."""
    action = RateLimitedAction("test", timedelta(hours=1), 5, by_user=False)

    with raises(RateLimitError):
        action.check_for_user_id(1)


def test_check_by_ip_disabled():
    """Ensure non-by_ip RateLimitedAction can't be checked by ip."""
    action = RateLimitedAction("test", timedelta(hours=1), 5, by_ip=False)

    with raises(RateLimitError):
        action.check_for_ip("123.123.123.123")


def test_simple_rate_limiting_by_user_id(redis):
    """Ensure simple rate-limiting by user_id is working."""
    limit = 5
    user_id = 1

    # define an action with max_burst equal to the full limit
    action = RateLimitedAction(
        "testaction", timedelta(hours=1), limit, max_burst=limit, redis=redis
    )

    # run the action the full number of times, should all be allowed
    for _ in range(limit):
        result = action.check_for_user_id(user_id)
        assert result.is_allowed

    # try one more time, should be rejected
    result = action.check_for_user_id(user_id)
    assert not result.is_allowed


def test_different_user_ids_limited_separately(redis):
    """Ensure one user being rate-limited doesn't affect a different one."""
    limit = 5
    user_id = 1

    action = RateLimitedAction("test", timedelta(hours=1), limit, redis=redis)

    # check the action for the first user_id until it's blocked
    result = action.check_for_user_id(user_id)
    while result.is_allowed:
        result = action.check_for_user_id(user_id)

    # it should still be allowed for a different user_id
    assert action.check_for_user_id(user_id + 1)


def test_max_burst_defaults_to_half(redis):
    """Ensure that unspecified max_burst on a RateLimitedAction allows half."""
    limit = 10
    user_id = 1

    action = RateLimitedAction("test", timedelta(days=1), limit, redis=redis)

    # see how many times we can do the action until it gets blocked
    count = 0
    while True:
        result = action.check_for_user_id(user_id)
        if result.is_allowed:
            count += 1
        else:
            break

    assert count == limit // 2


def test_time_until_retry(redis):
    """Ensure an unbursted limit's time_until_retry is the expected value."""
    user_id = 1
    period = timedelta(seconds=60)
    limit = 2

    # create an action with no burst allowed, which will force the actions to be spaced
    # "evenly" across the limit
    action = RateLimitedAction(
        "test", period=period, limit=limit, max_burst=1, redis=redis
    )

    # first usage should be fine
    result = action.check_for_user_id(user_id)
    assert result.is_allowed

    # second should fail, and require a wait of (period / limit) - 1 sec
    result = action.check_for_user_id(user_id)
    assert not result.is_allowed
    assert result.time_until_retry == (period / limit) - timedelta(seconds=1)


def test_remaining_limit(redis):
    """Ensure a limit's "remaining limit" decreases as expected."""
    user_id = 1
    limit = 10

    # create an action allowing the full limit as a burst
    action = RateLimitedAction(
        "test", timedelta(days=1), limit, max_burst=limit, redis=redis
    )

    for count in range(1, limit + 1):
        result = action.check_for_user_id(user_id)
        assert result.remaining_limit == limit - count


def test_simple_rate_limiting_by_ip(redis):
    """Ensure simple rate-limiting by IP address is working."""
    limit = 5
    ip = "123.123.123.123"

    # define an action with max_burst equal to the full limit
    action = RateLimitedAction(
        "testaction", timedelta(hours=1), limit, max_burst=limit, redis=redis
    )

    # run the action the full number of times, should all be allowed
    for _ in range(limit):
        result = action.check_for_ip(ip)
        assert result.is_allowed

    # try one more time, should be rejected
    result = action.check_for_ip(ip)
    assert not result.is_allowed


def test_check_for_ip_invalid_address():
    """Ensure RateLimitedAction.check_for_ip can't take an invalid IP."""
    ip = "123.456.789.123"

    action = RateLimitedAction("testaction", timedelta(hours=1), 10)

    with raises(ValueError):
        action.check_for_ip(ip)


def test_reset_for_ip_invalid_address():
    """Ensure RateLimitedAction.reset_for_ip can't take an invalid IP."""
    ip = "123.456.789.123"

    action = RateLimitedAction("testaction", timedelta(hours=1), 10)

    with raises(ValueError):
        action.reset_for_ip(ip)


def test_merged_results_single():
    """Ensure "merging" a single result just returns the same one."""
    result = RateLimitResult(
        is_allowed=True,
        total_limit=50,
        remaining_limit=22,
        time_until_max=timedelta(seconds=256),
    )

    assert RateLimitResult.merged_result([result]) == result


def test_merged_results():
    """Ensure merging RateLimitResults gives the expected result."""
    results = [
        RateLimitResult(
            is_allowed=True,
            total_limit=20,
            remaining_limit=15,
            time_until_max=timedelta(seconds=90),
        ),
        RateLimitResult(
            is_allowed=False,
            total_limit=10,
            remaining_limit=0,
            time_until_max=timedelta(seconds=30),
            time_until_retry=timedelta(seconds=10),
        ),
        RateLimitResult(
            is_allowed=True,
            total_limit=30,
            remaining_limit=20,
            time_until_max=timedelta(seconds=60),
        ),
    ]

    expected_merged_result = RateLimitResult(
        is_allowed=False,
        total_limit=10,
        remaining_limit=0,
        time_until_max=timedelta(seconds=90),
        time_until_retry=timedelta(seconds=10),
    )

    # try merging all permutations to ensure ordering isn't a factor
    for permutation in permutations(results):
        merged_result = RateLimitResult.merged_result(permutation)
        assert merged_result == expected_merged_result


def test_merged_all_allowed():
    """Ensure a merged result from all allowed results is also allowed."""

    def random_allowed_result():
        """Return a RateLimitResult with is_allowed=True, otherwise random."""
        return RateLimitResult(
            is_allowed=True,
            total_limit=randint(1, 100),
            remaining_limit=randint(1, 100),
            time_until_max=timedelta(randint(1, 100)),
        )

    # try merging a few different sets of different sizes
    for num_results in range(2, 6):
        results = [random_allowed_result() for _ in range(num_results)]
        assert RateLimitResult.merged_result(results).is_allowed
