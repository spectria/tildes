# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Classes and constants related to rate-limited actions."""

from datetime import timedelta
from ipaddress import ip_address
from typing import Any, List, Optional, Sequence

from pyramid.response import Response
from redis import Redis

from tildes.lib.datetime import utc_now


class RateLimitError(Exception):
    """Exception class for errors related to rate-limiting."""

    pass


class RateLimitResult:
    """The result from a rate-limit check.

    Includes data relating to whether the action should be allowed or blocked, how much
    of the limit is remaining, how long until the action can be retried, etc.
    """

    def __init__(
        self,
        is_allowed: bool,
        total_limit: int,
        remaining_limit: int,
        time_until_max: timedelta,
        time_until_retry: Optional[timedelta] = None,
    ):
        """Initialize a RateLimitResult."""
        # pylint: disable=too-many-arguments
        if is_allowed and time_until_retry is not None:
            raise ValueError("time_until_retry must be None if is_allowed is True")

        self.is_allowed = is_allowed
        self.total_limit = total_limit
        self.remaining_limit = remaining_limit
        self.time_until_max = time_until_max
        self.time_until_retry = time_until_retry

    def __eq__(self, other: Any) -> bool:
        """Return whether the other object is an identical result."""
        if not isinstance(other, RateLimitResult):
            return NotImplemented

        return (
            self.is_allowed == other.is_allowed
            and self.total_limit == other.total_limit
            and self.remaining_limit == other.remaining_limit
            and self.time_until_max == other.time_until_max
            and self.time_until_retry == other.time_until_retry
        )

    @classmethod
    def unlimited_result(cls) -> "RateLimitResult":
        """Return a "blank" result representing an unlimited action."""
        return cls(
            is_allowed=True,
            total_limit=0,
            remaining_limit=0,
            time_until_max=timedelta(0),
        )

    @classmethod
    def from_redis_cell_result(cls, result: List[int]) -> "RateLimitResult":
        """Convert the response from CL.THROTTLE command to a RateLimitResult.

        CL.THROTTLE responds with an array of 5 integers:
            1. Whether the action was limited (0 = allowed, 1 = blocked)
            2. Total limit for key (max burst + 1)
            3. Remaining limit for key
            4. Seconds until user should retry (-1 if action was allowed)
            5. Seconds until limit will reset to max capacity
        """
        is_allowed = not bool(result[0])
        total_limit = result[1]
        remaining_limit = result[2]

        if result[3] == -1:
            time_until_retry = None
        else:
            time_until_retry = timedelta(seconds=result[3])

        time_until_max = timedelta(seconds=result[4])

        return cls(
            is_allowed=is_allowed,
            total_limit=total_limit,
            remaining_limit=remaining_limit,
            time_until_max=time_until_max,
            time_until_retry=time_until_retry,
        )

    @classmethod
    def merged_result(cls, results: Sequence["RateLimitResult"]) -> "RateLimitResult":
        """Merge any number of RateLimitResults into a single result.

        Basically, the merged result should be the "most restrictive" combination of all
        the source results. That is, it should only allow the action if *all* of the
        source results would allow it, the limit counts should be the lowest of the set,
        and the waiting times should be the highest of the set.

        Note: I think the behavior for time_until_max is not truly correct, but it
        should be reasonable for now. Consider a situation like two "overlapping" limits
        of 10/min and 100/hour and what the time_until_max value of the combination
        should be. It might be a bit tricky.
        """
        # if there's only one result, just return that one
        if len(results) == 1:
            return results[0]

        # time_until_retry is a bit trickier than the others because some/all of the
        # source values might be None
        if all(r.time_until_retry is None for r in results):
            time_until_retry = None
        else:
            time_until_retry = max(
                r.time_until_retry for r in results if r.time_until_retry
            )

        return cls(
            is_allowed=all(r.is_allowed for r in results),
            total_limit=min(r.total_limit for r in results),
            remaining_limit=min(r.remaining_limit for r in results),
            time_until_max=max(r.time_until_max for r in results),
            time_until_retry=time_until_retry,
        )

    def add_headers_to_response(self, response: Response) -> Response:
        """Add the relevant ratelimiting headers to a Response."""
        # Retry-After: seconds the client should wait until retrying
        if self.time_until_retry:
            retry_seconds = int(self.time_until_retry.total_seconds())
            response.headers["Retry-After"] = str(retry_seconds)

        # X-RateLimit-Limit: the total action limit (including used)
        response.headers["X-RateLimit-Limit"] = str(self.total_limit)

        # X-RateLimit-Remaining: remaining actions before client hits the limit
        response.headers["X-RateLimit-Remaining"] = str(self.remaining_limit)

        # X-RateLimit-Reset: epoch timestamp when limit will be back to full
        reset_time = utc_now() + self.time_until_max
        reset_timestamp = int(reset_time.timestamp())
        response.headers["X-RateLimit-Reset"] = str(reset_timestamp)

        return response


class RateLimitedAction:
    """Represents a particular action and the limits on its usage.

    This class uses the redis-cell Redis module to implement a Generic Cell Rate
    Algorithm (GCRA) for rate-limiting, which includes several desirable characteristics
    including a rolling time window and support for "bursts".
    """

    def __init__(
        self,
        name: str,
        period: timedelta,
        limit: int,
        max_burst: Optional[int] = None,
        by_user: bool = True,
        by_ip: bool = True,
        redis: Optional[Redis] = None,
    ):
        """Initialize the limits on a particular action.

        The action will be limited to a maximum of `limit` calls over the time period
        specified in `period`. By default, up to half of the actions inside a period may
        be used in a "burst", in which no specific time restrictions are applied.  This
        behavior is controlled by the `max_burst` argument, which can range from 1 (no
        burst allowed, requests must wait at least `period / limit` time between them),
        up to the same value as `limit` (the full limit may be used at any rate, but
        never more than `limit` inside any given period).
        """
        # pylint: disable=too-many-arguments
        if max_burst and not 1 <= max_burst <= limit:
            raise ValueError("max_burst must be at least 1 and <= limit")

        if not (by_user or by_ip):
            raise ValueError("At least one of by_user or by_ip must be True")

        self.name = name
        self.period = period
        self.limit = limit

        if max_burst:
            self.max_burst = max_burst
        else:
            # if a max burst wasn't specified, set it to half the limit
            self.max_burst = limit // 2

        self.by_user = by_user
        self.by_ip = by_ip

        # if a redis connection wasn't specified, it will need to be initialized before
        # any checks or resets for this action can be done
        self._redis = redis

    @property
    def redis(self) -> Redis:
        """Return the redis connection."""
        if not self._redis:
            raise RateLimitError("No redis connection set")

        return self._redis

    @redis.setter
    def redis(self, redis_connection: Redis) -> None:
        """Set the redis connection."""
        self._redis = redis_connection

    def _build_redis_key(self, by_type: str, value: Any) -> str:
        """Build the Redis key where this rate limit is maintained."""
        parts = ["ratelimit", self.name, by_type, str(value)]

        return ":".join(parts)

    def _call_redis_command(self, key: str) -> List[int]:
        """Call the redis-cell CL.THROTTLE command for this action."""
        return self.redis.execute_command(
            "CL.THROTTLE",
            key,
            self.max_burst - 1,
            self.limit,
            int(self.period.total_seconds()),
        )

    def check_for_user_id(self, user_id: int) -> RateLimitResult:
        """Check whether a particular user_id can perform this action."""
        if not self.by_user:
            raise RateLimitError("check_for_user_id called on non-user-limited action")

        key = self._build_redis_key("user", user_id)
        result = self._call_redis_command(key)

        return RateLimitResult.from_redis_cell_result(result)

    def reset_for_user_id(self, user_id: int) -> None:
        """Reset the ratelimit on this action for a particular user_id."""
        if not self.by_user:
            raise RateLimitError("reset_for_user_id called on non-user-limited action")

        key = self._build_redis_key("user", user_id)
        self.redis.delete(key)

    def check_for_ip(self, ip_str: str) -> RateLimitResult:
        """Check whether a particular IP can perform this action."""
        if not self.by_ip:
            raise RateLimitError("check_for_ip called on non-IP-limited action")

        # check if ip_str is a valid address, will ValueError if not
        ip_address(ip_str)

        key = self._build_redis_key("ip", ip_str)
        result = self._call_redis_command(key)

        return RateLimitResult.from_redis_cell_result(result)

    def reset_for_ip(self, ip_str: str) -> None:
        """Reset the ratelimit on this action for a particular IP."""
        if not self.by_ip:
            raise RateLimitError("reset_for_ip called on non-user-limited action")

        # check if ip_str is a valid address, will ValueError if not
        ip_address(ip_str)

        key = self._build_redis_key("ip", ip_str)
        self.redis.delete(key)


# the actual list of actions with rate-limit restrictions
# each action must have a unique name to prevent key collisions
_RATE_LIMITED_ACTIONS = (
    RateLimitedAction("donate", timedelta(hours=1), 5, max_burst=5, by_user=False),
    RateLimitedAction("login", timedelta(hours=1), 20),
    RateLimitedAction("login_two_factor", timedelta(hours=1), 20),
    RateLimitedAction("register", timedelta(hours=1), 50),
    RateLimitedAction("topic_post", timedelta(hours=1), 6, max_burst=4),
    RateLimitedAction("comment_post", timedelta(hours=1), 30, max_burst=20),
)

# (public) dict to be able to look up the actions by name
RATE_LIMITED_ACTIONS = {action.name: action for action in _RATE_LIMITED_ACTIONS}
