from typing import Dict, NamedTuple, Optional

from .family_tree import FamilyTree, IndividualID


class LayoutInfo(NamedTuple):
    level: int


class Layout:
    def __init__(self, family_tree: FamilyTree, starting_at: IndividualID):
        self.family_tree = family_tree
        self.levels = self._init_levels(starting_at)

    def __getitem__(self, id: IndividualID) -> Optional[LayoutInfo]:
        if id in self:
            return LayoutInfo(
                level=self.levels[id],
            )
        else:
            return None

    def __hasattr__(self, id: IndividualID) -> bool:
        return id in self

    def __getattr__(self, id: IndividualID) -> Optional[LayoutInfo]:
        return self[id]

    def __contains__(self, id: IndividualID) -> bool:
        return id in self.levels

    def _init_levels_internal(
        self, at: IndividualID, level_dict: Dict[IndividualID, int]
    ) -> None:
        flatten = lambda lists: [item for sublist in lists for item in sublist]
        this_level = level_dict[at]

        def level_relation(family_to_person, person_to_family, delta_level):
            relations = flatten(map(family_to_person, person_to_family(at)))
            new_relations = list(filter(lambda id: id not in level_dict, relations))

            for relation in new_relations:
                level_dict[relation] = this_level + delta_level

            return new_relations

        ft = self.family_tree
        spouses = level_relation(ft.spouses_of_family, ft.own_families_of, 0)
        parents = level_relation(ft.spouses_of_family, ft.parent_families_of, -1)
        children = level_relation(ft.children_of_family, ft.own_families_of, 1)

        # It is important that this loop is after the other loops and we visit
        # individuals breadth-first and not depth-first as it will result it more
        # consistent levels
        for id in spouses + parents + children:
            self._init_levels_internal(id, level_dict)

    def _init_levels(self, starting_at: IndividualID) -> Dict[IndividualID, int]:
        level_dict = {starting_at: 0}
        self._init_levels_internal(starting_at, level_dict)
        return level_dict
