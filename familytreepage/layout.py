from collections import defaultdict
from typing import DefaultDict, Dict, List, NamedTuple, Optional

from .family_tree import AnyID, FamilyTree, IndividualID


class Point(NamedTuple):
    x: int
    y: int


Size = Point


class LayoutInfo(NamedTuple):
    level: int
    pos: Point


class Layout:
    def __init__(
        self,
        family_tree: FamilyTree,
        starting_at: IndividualID,
        box_size: Size = Size(150, 30),
        padding: Size = Size(20, 20),
    ):
        self.family_tree = family_tree
        self.box_size = box_size
        self.padding = padding

        self.levels: Dict[IndividualID, int] = {starting_at: 0}
        self.min_level = 0
        self.max_level = 0
        self._init_levels(starting_at)  # Updates previous three attributes!
        self.level_count = self.max_level - self.min_level + 1

        self.groups: DefaultDict[int, List[IndividualID]] = defaultdict(list)
        self.group_index: Dict[IndividualID, int] = {}
        self._init_groups(starting_at)

        self.width = 600
        self.height = (
            self.level_count * (self.box_size.y + self.padding.y) + self.padding.y
        )

    def __getitem__(self, id: IndividualID) -> LayoutInfo:
        level_from_start = self.levels[id] - self.min_level
        pos_x = (self.padding.x + self.box_size.x) * self.group_index.get(
            id, len(self.groups[self.levels[id]])
        )
        pos_y = (self.padding.y + self.box_size.y) * level_from_start + self.padding.y

        return LayoutInfo(
            level=self.levels[id],
            pos=Point(x=pos_x, y=pos_y),
        )

    def __contains__(self, id: IndividualID) -> bool:
        return id in self.levels

    def _init_levels(self, at: IndividualID):
        flatten = lambda lists: [item for sublist in lists for item in sublist]
        this_level = self.levels[at]

        def level_relation(family_to_person, person_to_family, delta_level):
            relations = flatten(map(family_to_person, person_to_family(at)))
            new_relations = list(filter(lambda id: id not in self.levels, relations))

            relation_level = this_level + delta_level
            for relation in new_relations:
                self.levels[relation] = relation_level

            if new_relations:
                self.min_level = min(self.min_level, relation_level)
                self.max_level = max(self.max_level, relation_level)

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

    def _init_groups(self, at: IndividualID):
        ft = self.family_tree

        flatten = lambda lists: [item for sublist in lists for item in sublist]

        self.groups[self.levels[at]].append(at)

        def handle_parents(at):
            parents = flatten(map(ft.spouses_of_family, ft.parent_families_of(at)))
            # TODO sort by sex

            for parent in parents:
                self.groups[self.levels[parent]].append(parent)

            for parent in parents:
                handle_parents(parent)

        handle_parents(at)

        def handle_children(at):
            children = flatten(map(ft.children_of_family, ft.own_families_of(at)))
            # TODO sort by age

            for child in children:
                self.groups[self.levels[child]].append(child)

            for child in children:
                handle_children(child)

        handle_children(at)

        for group in self.groups.values():
            for index, individual in enumerate(group):
                self.group_index[individual] = index
