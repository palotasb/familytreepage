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
        individuals_parent_families={
            id: list(family_tree.individual_parent_families(id))
            for id in family_tree.individuals.keys()
        },
        individuals_own_families={
            id: list(family_tree.individual_own_families(id))
            for id in family_tree.individuals.keys()
        },
        family_spouses={
            id: list(family_tree.family_spouses(id))
            for id in family_tree.families.keys()
        },
        family_children={
            id: list(family_tree.family_children(id))
            for id in family_tree.families.keys()
        },
        layout=layout,
    )

    renderer = env.get_template(template)
    renderer.stream(params).dump(file)
