from collections import defaultdict
from itertools import chain
from typing import DefaultDict, Dict, Iterable, List, NamedTuple, Optional, Set

from .family_tree import AnyID, FamilyID, FamilyTree, IndividualID


class Point(NamedTuple):
    x: int
    y: int


Size = Point


class LayoutInfo(NamedTuple):
    level: int
    group: int
    pos: Point
    size: Point

    @property
    def top(self) -> Point:
        return Point(self.pos.x + self.size.x // 2, self.pos.y)

    @property
    def right(self) -> Point:
        return Point(self.pos.x + self.size.x, self.pos.y + self.size.y // 2)

    @property
    def bottom(self) -> Point:
        return Point(self.pos.x + self.size.x // 2, self.pos.y + self.size.y)

    @property
    def left(self) -> Point:
        return Point(self.pos.x, self.pos.y + self.size.y // 2)

    @property
    def center(self) -> Point:
        return Point(self.pos.x + self.size.x // 2, self.pos.y + self.size.y // 2)


class Layout:
    def __init__(
        self,
        family_tree: FamilyTree,
        starting_at: IndividualID,
        box_size: Size = Size(175, 50),
        padding: Size = Size(15, 15),
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
        self.max_group_size = 0
        self._init_groups(starting_at)

        self.families: Dict[FamilyID, LayoutInfo] = {}
        self._init_families()

        self.width = (
            self.padding.x + self.box_size.x
        ) * self.max_group_size + self.padding.x
        self.height = (
            self.level_count * (self.box_size.y + self.padding.y) + self.padding.y
        )

    def __getitem__(self, id: IndividualID) -> LayoutInfo:
        level_from_start = self.levels[id] - self.min_level
        pos_x = (self.padding.x + self.box_size.x) * self.group_index.get(
            id, len(self.groups[self.levels[id]])
        ) + self.padding.x
        pos_y = (self.padding.y + self.box_size.y) * level_from_start + self.padding.y

        return LayoutInfo(
            level=self.levels[id],
            group=self.group_index[id],
            pos=Point(x=pos_x, y=pos_y),
            size=self.box_size,
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

    def _init_groups(self, id: IndividualID):
        ft = self.family_tree
        flatten = lambda lists: [item for sublist in lists for item in sublist]

        def get_spouses(id: IndividualID) -> Iterable[IndividualID]:
            spouses = flatten(map(ft.spouses_of_family, ft.own_families_of(id)))
            # TODO sort by something?
            return spouses

        def get_parents(id: IndividualID) -> Iterable[IndividualID]:
            parents = flatten(map(ft.spouses_of_family, ft.parent_families_of(id)))
            # TODO sort by sex
            return parents

        def get_children(id: IndividualID) -> Iterable[IndividualID]:
            children = flatten(map(ft.children_of_family, ft.own_families_of(id)))
            # TODO sort by age
            return children

        grouped: Set[IndividualID] = set()
        is_not_grouped = lambda individual: individual not in grouped

        def group_self_and_spouses_very_first(id: IndividualID):
            self_and_spouses = list(filter(is_not_grouped, get_spouses(id)))

            for self_or_spouse in self_and_spouses:
                self.groups[self.levels[self_or_spouse]].append(self_or_spouse)
                grouped.add(self_or_spouse)

        group_self_and_spouses_very_first(id)

        def group_direct_ancestors_first(id: IndividualID):
            parents = list(filter(is_not_grouped, get_parents(id)))

            for parent in parents:
                self.groups[self.levels[parent]].append(parent)
                grouped.add(parent)

            for parent in parents:
                group_direct_ancestors_first(parent)

        group_direct_ancestors_first(id)

        def group_direct_descendants_first(id: IndividualID):
            children = list(filter(is_not_grouped, get_children(id)))

            for child in children:
                self.groups[self.levels[child]].append(child)
                grouped.add(child)

            for child in children:
                group_direct_descendants_first(child)

        group_direct_descendants_first(id)

        def get_relatives(id: IndividualID) -> Iterable[IndividualID]:
            return chain(get_spouses(id), get_parents(id), get_children(id))

        handled: Set[IndividualID] = set()
        is_not_handled = lambda individual: individual not in handled

        def family_tree_breadth_first(id: IndividualID) -> List[IndividualID]:

            relatives = [id]
            handled.add(id)

            for relative in relatives:
                second_relatives = filter(is_not_handled, get_relatives(relative))
                for second_relative in second_relatives:
                    handled.add(second_relative)
                    relatives.append(second_relative)

            return relatives

        other_relatives = filter(is_not_grouped, family_tree_breadth_first(id))

        for relative in other_relatives:
            self.groups[self.levels[relative]].append(relative)

        for group in self.groups.values():
            for index, individual in enumerate(group):
                self.group_index[individual] = index

            self.max_group_size = max(self.max_group_size, len(group))

    def _init_families(self):
        ft = self.family_tree
        for fid, family in self.family_tree.families.items():
            level = None
            spouses = list(ft.spouses_of_family(fid))
            children = list(ft.children_of_family(fid))
            if spouses and spouses[0] in self:
                level = self[spouses[0]].level
            elif level is None and children and children[0] in self:
                level = self[children[0]].level
            else:
                continue

            group = 0  # TODO discard this, doesn't make sense for Family layout

            all_members = list(filter(lambda iid: iid in self, spouses + children))

            leftmost_x = self[min(all_members, key=lambda iid: self[iid].left.x)].left.x
            rightmost_x = self[
                max(all_members, key=lambda iid: self[iid].right.x)
            ].right.x
            y = (self.padding.y + self.box_size.y) * (level + 1) - self.padding.y // 2

            self.families[fid] = LayoutInfo(
                level=level,
                group=group,
                pos=Point(leftmost_x, y),
                size=Size(rightmost_x - leftmost_x, 0),
            )
