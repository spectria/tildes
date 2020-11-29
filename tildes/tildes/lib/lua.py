# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions and classes related to Lua scripting."""

from pathlib import Path
from typing import Any, Callable, Optional

from lupa import LuaError, LuaRuntime


LUA_PACKAGES_PATH = Path("/opt/tildes/lua", "?.lua")


def getter_handler(obj: Any, attr_name: str) -> Any:
    """Return the value of an object's attr, if scripts are allowed access.

    Depends on a "gettable_attrs" attribute on the object, which should be a list of
    attr names that scripts are allowed to access.
    """
    gettable_attrs = getattr(obj, "gettable_attrs", [])

    if attr_name not in gettable_attrs:
        raise AttributeError(f"{attr_name}")

    return getattr(obj, attr_name)


def setter_handler(obj: Any, attr_name: str, value: Any) -> None:
    """Set an object's attr to a new value, if scripts are allowed to do so.

    Depends on a "settable_attrs" attribute on the object, which should be a list of
    attr names that scripts are allowed to overwrite the value of.
    """
    settable_attrs = getattr(obj, "settable_attrs", [])

    if attr_name not in settable_attrs:
        raise AttributeError

    setattr(obj, attr_name, value)


class SandboxedLua:
    """A Lua runtime environment that's restricted to a sandbox.

    The sandbox is mostly implemented in Lua itself, and restricts the capabilities
    and data that code will be able to use. There are also some attempts to restrict
    resource usage, but I don't know how effective it is (and should probably be done
    on the OS level as well).
    """

    def __init__(self) -> None:
        """Create a Lua runtime and set up the sandbox environment inside it."""
        self.lua = LuaRuntime(
            register_eval=False,
            register_builtins=False,
            unpack_returned_tuples=True,
            attribute_handlers=(getter_handler, setter_handler),
        )

        self.lua.execute(f"package.path = '{LUA_PACKAGES_PATH}'")
        self.sandbox = self.lua.eval('require("sandbox")')

    def run_code(self, code: str) -> None:
        """Run Lua code inside the sandboxed environment."""
        result = self.sandbox.run(code)

        if result is not True:
            raise LuaError(result[1])

    def get_lua_function(self, name: str) -> Optional[Callable]:
        """Return the named Lua function so it can be called on Python data."""
        return self.sandbox.env[name]

    def run_lua_function(self, name: str, *args: Any) -> None:
        """Run the named Lua function, passing in the remaining args."""
        function = self.get_lua_function(name)
        if not function:
            raise ValueError(f"No Lua function named {name} exists")

        function(*args)
