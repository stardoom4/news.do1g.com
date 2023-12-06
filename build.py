#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path

PAGE = """\
<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { background: #fafaff; }
main {
    font-family: helvetica, sans-serif;
    font-size: 1.3rem;
    max-width: 60ch;
    margin: 0 auto;
}
section {
    border: 1px solid #000;
    border-radius: 0.25em;
}
h2 { font-size: 2rem; }
ul {
    list-style: none;
    margin: 0;
    padding: 0;
}
a, a:visited { color: #166491; }
a:active, a:focus, a:hover{ color: #2197db; }
</style>
<main>
<h1>Recent Updates for @duckinator</h1>

{{ posts | postify-each | join-lines }}
</main>
"""

POST = """\
<section>
<p>{{ text }}</p>
<time datetime="{{ datetime }}">{{ datetime | friendly-datetime }}</time>
</section>
"""


class Template:
    def __init__(self, template: str):
        self.template = template

    def _parse(self, text: str) -> tuple:
        parts = []
        i = 0
        length = len(text)

        start = 0
        end = 0
        while i < length:
            if text[i] == "{" and text[i + 1] == "{":
                parts.append(("text", text[start:end]))
                start = i + 2

                i = start
                while text[i] != "}" or text[i + 1] != "}":
                    i += 1
                end = i

                parts.append(("key", text[start:end]))

                start = i + 2
                end = start
                i = start
            else:
                i += 1
                end += 1

        parts.append(("text", text[start:end]))

        return parts

    def apply_part(self, part: str, variables: dict) -> str:
        (kind, item) = part
        if kind == "text":
            return item
        elif kind == "key":
            key, *functions = [x.strip() for x in item.split("|")]
            value = variables[key]
            for function in functions:
                value = variables[function](value)
            return str(value)
        else:
            exit("Expected \"text\" or \"key\", got " + repr(kind))

    def apply(self, variables: dict) -> str:
        parts = self._parse(self.template)
        return "".join([self.apply_part(part, variables) for part in parts])


# FIXME: Once Netlify supports Py3.9+, change {**a, **b} and similar to a | b.

functions = {
    "join-lines": lambda l: "\n".join(l),
    "friendly-datetime": lambda dt: datetime.strptime(dt, "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y %I:%M%p"),
    "postify-each": lambda l: [Template(POST).apply({**post, **functions}) for post in l],
}

posts = [{"datetime": p.stem.replace(".", ":").replace("_", " "), "text": p.read_text()} for p in Path("posts").glob("*.txt")]
results = Template(PAGE).apply({"posts": posts, **functions})

site = Path("_site")
site.mkdir(exist_ok=True)

(site / "index.html").write_text(results)
