"""Contains the application's views."""

from pyramid.response import Response


# Intercooler uses an empty response as a no-op and won't replace anything.
# 204 would probably be more correct than 200, but Intercooler errors on it
IC_NOOP = Response(status_int=200)
IC_NOOP_404 = Response(status_int=404)

# Because of the above, in order to deliberately cause Intercooler to replace an element
# with whitespace, the response needs to contain at least two spaces
IC_EMPTY = Response("  ")
