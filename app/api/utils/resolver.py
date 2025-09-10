import os

from jinja2 import FileSystemLoader, Environment


def generate_html_content(response, page):
    templates_path = os.path.join(os.path.dirname(__file__), "../resources/templates")
    env = Environment(loader=FileSystemLoader(templates_path))
    template = env.get_template(f"resolver/{page}")
    content = template.render(response=response)
    return content


def generate_resolver_id_page(response):
    return generate_html_content(response, "resolver_id.html")
