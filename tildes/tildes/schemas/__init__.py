"""Contains schemas, which define data (e.g. for models) in more depth.

These schemas are currently being used for several purposes:

  - Validation of data for models, such as checking the lengths of strings, ensuring
    that they match a particular regex pattern, etc. Specific errors can be generated
    for any data that is invalid.

  - Similarly, the webargs library uses the schemas to validate pieces of data coming in
    via urls, POST data, etc. It can produce errors if the data is not valid for the
    purpose it's intended for.

  - Serialization of data, which the Pyramid JSON renderer uses to produce data for the
    JSON API endpoints.
"""
