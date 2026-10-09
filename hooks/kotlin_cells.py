"""MkDocs hook: highlight %%kotlin notebook cells as Kotlin.

mkdocs-jupyter highlights every code cell with the notebook's kernel language (Python).
A cell that starts with %%kotlin holds Kotlin, so we re-highlight those cells.
"""
import html
import re

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

BLOCK = re.compile(
    r'<div class="highlight-ipynb hl-python[^"]*"><pre>.*?</pre></div>(\s*<div class="clipboard-copy-txt" id="cell-\d+">)(.*?)(</div>)',
    re.S,
)


def on_post_page(output, page, config):
    if "highlight-ipynb" not in output:
        return output

    def swap(match):
        source = html.unescape(match.group(2))
        if not source.lstrip().startswith("%%kotlin"):
            return match.group(0)
        body = source.split("\n", 1)[1] if "\n" in source else ""
        shown = "// %%kotlin  (runs in Colab)\n" + body
        formatter = HtmlFormatter(cssclass="highlight-ipynb hl-kotlin")
        return highlight(shown, get_lexer_by_name("kotlin"), formatter) + match.group(1) + match.group(2) + match.group(3)

    return BLOCK.sub(swap, output)
