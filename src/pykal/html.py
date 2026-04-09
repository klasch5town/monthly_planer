from __future__ import annotations

import html
from pathlib import Path


class HtmlTag:
    def __init__(self, tag_name: str, tag_text: str = "") -> None:
        self.tag_name = tag_name
        self.tag_text = tag_text
        self._attributes: dict[str, str] = {}
        self._sub_tags: list[HtmlTag] = []

    def add_attribute(self, name: str, value: str) -> None:
        if name in self._attributes:
            self._attributes[name] += " " + value
        else:
            self._attributes[name] = value

    def add_class(self, class_name: str) -> None:
        self.add_attribute("class", class_name)

    def set_text(self, text: str) -> None:
        self.tag_text = text

    def add_sub_tag(self, tag: HtmlTag) -> None:
        self._sub_tags.append(tag)

    def _write_open(self, out: object) -> None:
        out.write("<" + self.tag_name)
        for attr, value in self._attributes.items():
            out.write(f' {attr}="{value}"')
        out.write(">")

    def _write_close(self, out: object) -> None:
        out.write(f"</{self.tag_name}>\n")

    def write_tag(self, out: object) -> None:
        self._write_open(out)
        out.write(html.escape(self.tag_text))
        for sub_tag in self._sub_tags:
            sub_tag.write_tag(out)
        self._write_close(out)


class DivTag(HtmlTag):
    def __init__(self, tag_text: str = "", css_class: str = "") -> None:
        super().__init__("div", tag_text)
        if css_class:
            self.add_class(css_class)


class RawDivTag(HtmlTag):
    """DivTag whose content is written verbatim (no HTML escaping) — use for pre-built HTML snippets."""

    def __init__(self, raw_html: str = "", css_class: str = "") -> None:
        super().__init__("div", "")
        self._raw_html = raw_html
        if css_class:
            self.add_class(css_class)

    def write_tag(self, out: object) -> None:
        self._write_open(out)
        out.write(self._raw_html)
        for sub_tag in self._sub_tags:
            sub_tag.write_tag(out)
        self._write_close(out)


class _CssLinkTag(HtmlTag):
    def __init__(self, css_file: str, media_type: str = "all") -> None:
        super().__init__("link")
        self.add_attribute("rel", "stylesheet")
        self.add_attribute("type", "text/css")
        self.add_attribute("href", css_file)
        self.add_attribute("media", media_type)

    def write_tag(self, out: object) -> None:
        self._write_open(out)
        # <link> is a void element — no closing tag
        out.write("\n")


class HtmlFile:
    def __init__(self, file_name: str, target_dir: Path | str = ".") -> None:
        self.file_name = file_name
        self.target_dir = Path(target_dir)
        self._body_tags: list[HtmlTag] = []

    def add_tag(self, tag: HtmlTag) -> None:
        self._body_tags.append(tag)

    def save(self) -> None:
        file_path = self.target_dir / (self.file_name + ".html")
        with file_path.open("w", encoding="utf-8") as f:
            self._write(f)

    def _write(self, out: object) -> None:
        out.write("<!doctype html>\n<html>\n")

        out.write("<head>\n")
        css_tag = _CssLinkTag("stylesheet.css")
        css_tag.write_tag(out)
        title_tag = HtmlTag("title", self.file_name)
        title_tag.write_tag(out)
        out.write("</head>\n")

        out.write("<body>\n")
        for tag in self._body_tags:
            tag.write_tag(out)
        out.write("</body>\n</html>\n")
