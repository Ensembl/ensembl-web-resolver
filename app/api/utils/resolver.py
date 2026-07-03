import os

from jinja2 import FileSystemLoader, Environment

from app.core.config import STATIC_PATH


def generate_html_content(response, page):
    templates_path = os.path.join(os.path.dirname(__file__), "../resources/templates")
    env = Environment(loader=FileSystemLoader(templates_path))
    template = env.get_template(f"resolver/{page}")
    content = template.render(response=response, static_path=STATIC_PATH)
    return content


def generate_resolver_id_page(response):
    """Generate the stable ID resolver HTML page.

    Args:
        response: Stable ID resolver response model used by the template.

    Returns:
        Rendered HTML content for the stable ID resolver page.
    """
    return generate_html_content(response, "resolver_id.html")


def generate_resolver_url_page(response):
    """Generate the legacy URL resolver HTML page.

    Args:
        response: Legacy URL resolver response model used by the template.

    Returns:
        Rendered HTML content for the legacy URL resolver page.
    """
    return generate_html_content(response, "resolver_url.html")
