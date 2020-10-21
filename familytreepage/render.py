from typing import Dict, Tuple

from jinja2 import Environment, PackageLoader, select_autoescape

from .family_tree import FamilyTree, Individual
from .layout import Layout

env = Environment(
    autoescape=select_autoescape(["html", "xml"]),
    extensions=["jinja2.ext.debug"],
    loader=PackageLoader("familytreepage", "templates"),
    lstrip_blocks=True,
    trim_blocks=True,
)


def render(family_tree: FamilyTree, file, template: str = "default.html.jinja"):

    layout = Layout(family_tree, "@R1@")
    params = dict(
        family_tree=family_tree,
        individuals=family_tree.individuals,
        families=family_tree.families,
        layout=layout,
    )

    renderer = env.get_template(template)
    renderer.stream(params).dump(file)
