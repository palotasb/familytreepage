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


def random_positions_for(
    individuals: Dict[str, Individual], width: int, height: int
) -> Dict[str, Tuple[int, int]]:
    return {id: (0, 0) for id in individuals.keys()}


def render(family_tree: FamilyTree, file, template: str = "default.html.jinja"):

    width, height = 600, 400
    layout = Layout(family_tree, "@R1@")
    levelrange = set(layout.levels.values())
    params = dict(
        family_tree=family_tree,
        individuals=family_tree.individuals,
        individual_positions=random_positions_for(
            family_tree.individuals, width, height
        ),
        individuals_parent_families={
            id: family_tree.parent_families_of(id)
            for id in family_tree.individuals.keys()
        },
        individuals_own_families={
            id: family_tree.own_families_of(id) for id in family_tree.individuals.keys()
        },
        family_spouses={
            id: family_tree.spouses_of_family(id) for id in family_tree.families.keys()
        },
        family_children={
            id: family_tree.children_of_family(id) for id in family_tree.families.keys()
        },
        layout=layout,
        minlevel=min(levelrange),
        maxlevel=max(levelrange),
        families=family_tree.families,
        graphic_size=(width, height),
    )

    renderer = env.get_template(template)
    renderer.stream(params).dump(file)
