"""Offline Pango/Cairo renderer for the limited markup in docs/course/proposal.html."""

from html import escape
from html.parser import HTMLParser
import re

import ctypes as C


def bind(library, name, result, *arguments):
    function = getattr(library, name)
    function.restype, function.argtypes = result, arguments
    return function


_cairo = C.CDLL("libcairo.so.2")
_pango = C.CDLL("libpango-1.0.so.0")
_pc = C.CDLL("libpangocairo-1.0.so.0")
_gobject = C.CDLL("libgobject-2.0.so.0")
ptr, num, integer, string = C.c_void_p, C.c_double, C.c_int, C.c_char_p
pdf_surface = bind(_cairo, "cairo_pdf_surface_create", ptr, string, num, num)
metadata = bind(_cairo, "cairo_pdf_surface_set_metadata", None, ptr, integer, string)
create = bind(_cairo, "cairo_create", ptr, ptr)
color = bind(_cairo, "cairo_set_source_rgb", None, ptr, num, num, num)
move = bind(_cairo, "cairo_move_to", None, ptr, num, num)
line = bind(_cairo, "cairo_line_to", None, ptr, num, num)
line_width = bind(_cairo, "cairo_set_line_width", None, ptr, num)
stroke = bind(_cairo, "cairo_stroke", None, ptr)
rectangle = bind(_cairo, "cairo_rectangle", None, ptr, num, num, num, num)
fill = bind(_cairo, "cairo_fill", None, ptr)
show_page = bind(_cairo, "cairo_show_page", None, ptr)
finish = bind(_cairo, "cairo_surface_finish", None, ptr)
destroy_surface = bind(_cairo, "cairo_surface_destroy", None, ptr)
destroy_context = bind(_cairo, "cairo_destroy", None, ptr)
create_layout = bind(_pc, "pango_cairo_create_layout", ptr, ptr)
show_layout = bind(_pc, "pango_cairo_show_layout", None, ptr, ptr)
font_new = bind(_pango, "pango_font_description_from_string", ptr, string)
font_size = bind(_pango, "pango_font_description_set_absolute_size", None, ptr, num)
font_free = bind(_pango, "pango_font_description_free", None, ptr)
set_font = bind(_pango, "pango_layout_set_font_description", None, ptr, ptr)
set_width = bind(_pango, "pango_layout_set_width", None, ptr, integer)
set_wrap = bind(_pango, "pango_layout_set_wrap", None, ptr, integer)
set_spacing = bind(_pango, "pango_layout_set_line_spacing", None, ptr, C.c_float)
set_markup = bind(_pango, "pango_layout_set_markup", None, ptr, string, integer)
get_size = bind(_pango, "pango_layout_get_size", None, ptr, C.POINTER(integer), C.POINTER(integer))
unref = bind(_gobject, "g_object_unref", None, ptr)


class Node:
    def __init__(self, tag, attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def find(self, tag):
        result = []
        for child in self.children:
            if isinstance(child, Node):
                if child.tag == tag:
                    result.append(child)
                result.extend(child.find(tag))
        return result

    def markup(self):
        text = "".join(c.markup() if isinstance(c, Node) else escape(c) for c in self.children)
        if self.tag == "br":
            return "\n"
        if self.tag == "strong":
            return f"<b>{text}</b>"
        if self.tag == "sup":
            return f"<sup>{text}</sup>"
        return text


class Document(HTMLParser):
    def __init__(self, content):
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {"br", "meta", "link", "img", "hr", "input"}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        if self.stack[-1].tag != tag:
            raise ValueError(f"Unexpected closing tag: {tag}")
        self.stack.pop()

    def handle_data(self, data):
        self.stack[-1].children.append(re.sub(r"\s+", " ", data))


class Renderer:
    WIDTH, HEIGHT = 595.276, 841.890
    LEFT, RIGHT, TOP, FOOTER = 48.19, 547.09, 42.52, 798.0

    def __init__(self, path):
        self.surface = pdf_surface(str(path).encode(), self.WIDTH, self.HEIGHT)
        metadata(self.surface, 0, "Spire2Lab — Final Project Proposal".encode())
        self.context = create(self.surface)
        self.layout = create_layout(self.context)
        set_wrap(self.layout, 2)
        set_spacing(self.layout, 1.30)
        self.y = self.TOP

    def close(self):
        finish(self.surface)
        unref(self.layout)
        destroy_context(self.context)
        destroy_surface(self.surface)

    def text(self, markup, x=None, y=None, width=None, size=9.5, draw=True):
        x = self.LEFT if x is None else x
        y = self.y if y is None else y
        width = self.RIGHT - self.LEFT if width is None else width
        font = font_new(b"Noto Sans CJK SC")
        font_size(font, size * 1024)
        set_font(self.layout, font)
        font_free(font)
        set_width(self.layout, round(width * 1024))
        markup = re.sub(r"[ \t]+", " ", markup).strip()
        set_markup(self.layout, markup.encode(), -1)
        actual_width, height = integer(), integer()
        get_size(self.layout, C.byref(actual_width), C.byref(height))
        if actual_width.value / 1024 > width + .5:
            raise RuntimeError("Text exceeds its column width.")
        if draw:
            color(self.context, .09, .13, .18)
            move(self.context, x, y)
            show_layout(self.context, self.layout)
        return height.value / 1024

    def rule(self, y):
        color(self.context, .72, .77, .82)
        line_width(self.context, .55)
        move(self.context, self.LEFT, y)
        line(self.context, self.RIGHT, y)
        stroke(self.context)

    def table(self, node):
        widths = [83, self.RIGHT - self.LEFT - 83]
        for row in node.find("tr"):
            cells = [c for c in row.children if isinstance(c, Node) and c.tag in {"th", "td"}]
            heights = [self.text(c.markup(), width=w-10, size=8.5, draw=False) for c, w in zip(cells, widths)]
            height = max(heights) + 7
            if cells[0].tag == "th":
                color(self.context, .94, .96, .97)
                rectangle(self.context, self.LEFT, self.y, sum(widths), height)
                fill(self.context)
            x = self.LEFT
            for cell, width in zip(cells, widths):
                self.text(cell.markup(), x=x+5, y=self.y+3, width=width-10, size=8.5)
                x += width
            self.y += height
            self.rule(self.y)
        self.y += 4

    def block(self, node, references=False):
        if node.tag == "section":
            for child in node.children:
                if isinstance(child, Node):
                    self.block(child, node.attrs.get("class") == "references")
            return
        if node.tag == "table":
            self.table(node)
            return
        kind = node.attrs.get("class", node.tag)
        if kind == "footer":
            return
        sizes = {"eyebrow": 8.0, "h1": 20, "subtitle": 12.5, "meta": 8.5, "h2": 10.8, "flow": 9}
        if node.tag == "h2":
            self.y += 6
        if kind == "h1":
            self.y += 7
        text = node.markup()
        size = sizes.get(kind, 7.9 if references else 9.5)
        if kind in {"h1", "h2", "subtitle"}:
            text = f"<b>{text}</b>"
        if kind == "flow":
            height = self.text(text, width=self.RIGHT-self.LEFT-16, size=size, draw=False)
            color(self.context, .94, .96, .97)
            rectangle(self.context, self.LEFT, self.y, self.RIGHT-self.LEFT, height+10)
            fill(self.context)
            self.text(text, x=self.LEFT+8, y=self.y+5, width=self.RIGHT-self.LEFT-16, size=size)
            self.y += height + 15
        else:
            self.y += self.text(text, size=size) + (3 if references else 4)
        if kind == "eyebrow":
            self.rule(self.y)
            self.y += 3

    def render(self, doc):
        pages = doc.root.find("article")
        if len(pages) != 2:
            raise ValueError("Proposal must contain exactly two page articles.")
        layout = []
        for index, page in enumerate(pages, 1):
            self.y = self.TOP
            for child in page.children:
                if isinstance(child, Node):
                    self.block(child)
            layout.append({"page": index, "content_bottom_pt": round(self.y, 2), "footer_top_pt": self.FOOTER})
            if self.y > self.FOOTER - 12:
                self.close()
                raise RuntimeError(f"Page {index} content overlaps footer: {layout}")
            self.rule(self.FOOTER)
            self.text("Spire2Lab · Build Track · 2026", y=self.FOOTER+6, size=7.7)
            self.text(f"{index} / 2", x=self.RIGHT-25, y=self.FOOTER+6, width=25, size=7.7)
            show_page(self.context)
        self.close()
        return layout
