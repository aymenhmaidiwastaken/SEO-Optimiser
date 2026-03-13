from jinja2 import Environment, FileSystemLoader
from pathlib import Path

templates_dir = Path(__file__).parent.parent.parent / "templates"


def render_html_report(report_data: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    template = env.get_template("export_report.html")
    return template.render(**report_data)
