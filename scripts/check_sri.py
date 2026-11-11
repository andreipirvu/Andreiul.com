"""Fail if an HTML page loads a third-party script or stylesheet without Subresource
Integrity (R-03). Google Fonts CSS is exempt: it is generated per browser, so it has
no stable hash. Usage: python scripts/check_sri.py site/*.html
"""
import sys
from html.parser import HTMLParser

EXEMPT = ("https://fonts.googleapis.com/",)


class Finder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.problems = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        url = a.get("src") if tag == "script" else a.get("href") if tag == "link" and a.get("rel") == "stylesheet" else None
        if not url or not url.startswith(("http://", "https://", "//")) or url.startswith(EXEMPT):
            return
        line = self.getpos()[0]
        if not a.get("integrity"):
            self.problems.append(f"line {line}: {url} has no integrity attribute")
        elif a.get("crossorigin") is None:
            self.problems.append(f"line {line}: {url} has integrity but no crossorigin")


def main(paths):
    failed = False
    for path in paths:
        finder = Finder()
        with open(path, encoding="utf-8") as f:
            finder.feed(f.read())
        for problem in finder.problems:
            print(f"{path}: {problem}")
            failed = True
    if not failed:
        print(f"OK: every third-party script/stylesheet in {len(paths)} file(s) is pinned with SRI")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
