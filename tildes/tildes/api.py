"""Versioned API classes (wrappers around cornice.Service)."""

from typing import Any

from cornice import Service
import venusian


class APIv0(Service):
    """Service wrapper class for v0 of the API."""

    name_prefix = "apiv0_"
    base_path = "/api/v0"

    def __init__(self, name: str, path: str, **kwargs: Any) -> None:
        """Create a new service."""
        name = self.name_prefix + name
        path = self.base_path + path

        super().__init__(name=name, path=path, **kwargs)

        # Service.__init__ does this setup to support config.scan(), but it doesn't seem
        # to inherit properly, so it needs to be done again here
        def callback(context: Any, name: Any, obj: Any) -> None:
            # pylint: disable=unused-argument
            config = context.config.with_package(info.module)  # noqa

            # TEMP: disable API until I can fix the private-fields issue
            # config.add_cornice_service(self)

        info = venusian.attach(self, callback, category="pyramid")
