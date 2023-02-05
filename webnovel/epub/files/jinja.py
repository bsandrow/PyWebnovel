from jinja2 import Environment, PackageLoader, select_autoescape

JINJA = Environment(loader=PackageLoader("webnovel.epub"), autoescape=select_autoescape())
