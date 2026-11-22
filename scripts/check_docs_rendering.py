"""Fail when icon shortcodes leak into the built documentation as text."""

import argparse
from pathlib import Path

SHORTCODE_PREFIXES = (":material-", ":fontawesome-", ":octicons-", ":simple-")


def find_unrendered(site_dir):
    problems = []
    for page in Path(site_dir).rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        for prefix in SHORTCODE_PREFIXES:
            if prefix in text:
                problems.append(str(page) + ": " + prefix)
    return problems


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    args = parser.parse_args()
    problems = find_unrendered(args.site_dir)
    if problems:
        raise SystemExit("Unrendered icon shortcodes:\n" + "\n".join(problems))
    print("All icon shortcodes rendered.")


if __name__ == "__main__":
    main()
