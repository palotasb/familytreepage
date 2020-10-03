from typing import Dict, NamedTuple, Optional, Tuple

from .family_tree import FamilyTree, IndividualID

Point = Tuple[int, int]

Size = Point


def _x(p: Point) -> int:
    return p[0]


def _y(p: Point) -> int:
    return p[1]


class LayoutInfo(NamedTuple):
    level: int


class Layout:
    def __init__(
        self, family_tree: FamilyTree, starting_at: IndividualID, box_size: Size = 0
    ):
        self.family_tree = family_tree
        self.box_size = box_size

        self.levels = {starting_at: 0}
        self.min_level = 0
        self.max_level = 0
        self._init_levels(starting_at)

    def __getitem__(self, id: IndividualID) -> Optional[LayoutInfo]:
        if id in self:
            return LayoutInfo(
                level=self.levels[id],
            )
        else:
            return None

    def __contains__(self, id: IndividualID) -> bool:
        return id in self.levels

    def _init_levels(self, at: IndividualID):
        flatten = lambda lists: [item for sublist in lists for item in sublist]
        this_level = self.levels[at]

        def level_relation(family_to_person, person_to_family, delta_level):
            relations = flatten(map(family_to_person, person_to_family(at)))
            new_relations = list(filter(lambda id: id not in self.levels, relations))

            for relation in new_relations:
                self.levels[relation] = this_level + delta_level

            if new_relations:
                self.min_level = min(self.min_level, this_level + delta_level)
                self.max_level = max(self.max_level, this_level + delta_level)

            return new_relations

        ft = self.family_tree
        spouses = level_relation(ft.spouses_of_family, ft.own_families_of, 0)
        parents = level_relation(ft.spouses_of_family, ft.parent_families_of, -1)
        children = level_relation(ft.children_of_family, ft.own_families_of, 1)

        # It is important that this loop is after the other loops and we visit
        # individuals breadth-first and not depth-first as it will result it more
        # consistent levels
        for id in spouses + parents + children:
            self._init_levels(id)
