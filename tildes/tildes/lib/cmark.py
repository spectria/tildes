"""Set up the shared libcmark-gfm library and extensions."""
# pylint: disable=invalid-name

from ctypes import c_char_p, c_int, c_size_t, c_void_p, CDLL


CMARK_DLL = CDLL("/usr/local/lib/libcmark-gfm.so")
CMARK_EXT_DLL = CDLL("/usr/local/lib/libcmark-gfm-extensions.so")

# Enable the --hardbreaks and --unsafe options for cmark
# Can we import these somehow? They're defined in cmark.h as:
# CMARK_OPT_HARDBREAKS (1 << 2)
# CMARK_OPT_UNSAFE (1 << 17)
CMARK_OPTS = (1 << 2) | (1 << 17)

CMARK_EXTENSIONS = (b"autolink", b"strikethrough", b"table")

cmark_parser_new = CMARK_DLL.cmark_parser_new
cmark_parser_new.restype = c_void_p
cmark_parser_new.argtypes = (c_int,)

cmark_parser_feed = CMARK_DLL.cmark_parser_feed
cmark_parser_feed.restype = None
cmark_parser_feed.argtypes = (c_void_p, c_char_p, c_size_t)

cmark_parser_finish = CMARK_DLL.cmark_parser_finish
cmark_parser_finish.restype = c_void_p
cmark_parser_finish.argtypes = (c_void_p,)

cmark_parser_attach_syntax_extension = CMARK_DLL.cmark_parser_attach_syntax_extension
cmark_parser_attach_syntax_extension.restype = c_int
cmark_parser_attach_syntax_extension.argtypes = (c_void_p, c_void_p)

cmark_parser_get_syntax_extensions = CMARK_DLL.cmark_parser_get_syntax_extensions
cmark_parser_get_syntax_extensions.restype = c_void_p
cmark_parser_get_syntax_extensions.argtypes = (c_void_p,)

cmark_parser_free = CMARK_DLL.cmark_parser_free
cmark_parser_free.restype = None
cmark_parser_free.argtypes = (c_void_p,)

cmark_node_free = CMARK_DLL.cmark_node_free
cmark_node_free.restype = None
cmark_node_free.argtypes = (c_void_p,)

cmark_find_syntax_extension = CMARK_DLL.cmark_find_syntax_extension
cmark_find_syntax_extension.restype = c_void_p
cmark_find_syntax_extension.argtypes = (c_char_p,)

cmark_render_html = CMARK_DLL.cmark_render_html
cmark_render_html.restype = c_char_p
cmark_render_html.argtypes = (c_void_p, c_int, c_void_p)

register = CMARK_EXT_DLL.cmark_gfm_core_extensions_ensure_registered
register.restype = None
register.argtypes = ()
register()
