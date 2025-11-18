from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.types import WidgetData

# setup jinja2 environment
template_dir = Path(__file__).parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(template_dir), autoescape=select_autoescape(["html", "xml"])
)


def render_widget(data: WidgetData) -> str:
    template = jinja_env.get_template("widget.html")
    return template.render(**data)
