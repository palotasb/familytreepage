from typing import Dict

from .family_tree import FamilyTree, IndividualID


def _levels(
    ft: FamilyTree, at: IndividualID, level_dict: Dict[IndividualID, int]
) -> None:
    flatten = lambda lists: [item for sublist in lists for item in sublist]
    this_level = level_dict[at]

    def level_relation(family_to_person, person_to_family, delta_level):
        relations = flatten(map(family_to_person, person_to_family(at)))
        new_relations = list(filter(lambda id: id not in level_dict, relations))

        for relation in new_relations:
            level_dict[relation] = this_level + delta_level

        return new_relations

    spouses = level_relation(ft.spouses_of_family, ft.own_families_of, 0)
    parents = level_relation(ft.spouses_of_family, ft.parent_families_of, -1)
    children = level_relation(ft.children_of_family, ft.own_families_of, 1)

    # It is important that this loop is after the other loops and we visit
    # individuals breadth-first and not depth-first as it will result it more
    # consistent levels
    for id in spouses + parents + children:
        _levels(ft, id, level_dict)


def family_tree_levels(
    family_tree: FamilyTree, starting_at: IndividualID
) -> Dict[IndividualID, int]:
    level_dict = {starting_at: 0}
    _levels(family_tree, starting_at, level_dict)
    return level_dict
