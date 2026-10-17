"""Compile every packaged Jinja template, including branches exercised by page tests."""

from importlib.resources import files

from anthropic_readiness.web.pages import ASSETS, ENVIRONMENT


def main() -> int:
    templates = ENVIRONMENT.list_templates(extensions=("html",))
    if set(templates) != {"base.html", "configure.html", "run.html", "history.html"}:
        raise ValueError("unexpected_template_inventory")
    for name in templates:
        ENVIRONMENT.get_template(name)
    for asset in ASSETS:
        if not files("anthropic_readiness").joinpath("resources/" + asset).is_file():
            raise ValueError("missing_web_asset")
    print(f"compiled {len(templates)} templates; verified {len(ASSETS)} assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
