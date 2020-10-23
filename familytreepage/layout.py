from collections import defaultdict
from functools import partial
from itertools import chain
from typing import (
    Callable,
    DefaultDict,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Set,
)

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
        box_size: Size = Size(140, 36),
        padding: Size = Size(20, 30),
    ):
        self.family_tree = family_tree
        self.box_size = box_size
        self.padding = padding

        self.levels: Dict[IndividualID, int] = {}
        self.min_level = 0
        self.max_level = 0
        self.level_count = 1

        self.groups: DefaultDict[int, List[IndividualID]] = defaultdict(list)
        self.group_index: Dict[IndividualID, int] = {}
        self.max_group_size = 0

        self._init_levels(starting_at)  # Updates previous three attributes!

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

    def _init_levels(self, id: IndividualID):
        ft = self.family_tree

        # 1. Layout spouses
        # 2. Layout siblings
        # 3. Layout ancestors
        # 4. Layout descendants
        # 5. Continue breadth-first

        # For breadth-first iteration
        queue: List[IndividualID] = []
        # --
        handled: Set[IndividualID] = set()
        tasks: Dict[IndividualID, Callable[[], None]] = {}

        is_handled: Callable[[IndividualID], bool] = lambda iid: iid in handled

        def task(id: IndividualID, level: int, right: bool):
            self.levels[id] = level
            if right:
                self.groups[level].append(id)
            else:
                self.groups[level].insert(0, id)

            def handle_relatives(relatives: Iterable[IndividualID], level: int):
                for relative in relatives:
                    if not is_handled(relative):
                        queue.append(relative)
                        handled.add(relative)
                        tasks[relative] = partial(task, relative, level, right)

            handle_relatives(ft.spouses(id), level=level)
            handle_relatives(ft.siblings(id), level=level)
            handle_relatives(ft.parents(id), level=level - 1)
            handle_relatives(ft.children(id), level=level + 1)

        queue.append(id)
        handled.add(id)
        tasks[id] = partial(task, id, level=0, right=True)

        for id in queue:
            individual_task = tasks[id]
            del tasks[id]
            individual_task()

        all_levels: Set[int] = set(self.levels.values())
        self.min_level = min(all_levels)
        self.max_level = max(all_levels)
        self.level_count = self.max_level - self.min_level + 1

        for group in self.groups.values():
            self.max_group_size = max(self.max_group_size, len(group))
            for index, id in enumerate(group):
                self.group_index[id] = index

    def _init_families(self):
        ft = self.family_tree
        for fid, family in self.family_tree.families.items():
            level = None
            spouses = list(ft.family_spouses(fid))
            children = list(ft.family_children(fid))
            if spouses and spouses[0] in self:
                level = self[spouses[0]].level - self.min_level
            elif level is None and children and children[0] in self:
                level = self[children[0]].level - self.min_level
            else:
                continue

            group = 0  # TODO discard this, doesn't make sense for Family layout

            all_members = list(filter(lambda iid: iid in self, spouses + children))

            leftmost_x = self[
                min(all_members, key=lambda iid: self[iid].left.x)
            ].center.x
            rightmost_x = self[
                max(all_members, key=lambda iid: self[iid].right.x)
            ].center.x
            y = (self.padding.y + self.box_size.y) * (level + 1) + self.padding.y // 2

            self.families[fid] = LayoutInfo(
                level=level,
                group=group,
                pos=Point(leftmost_x, y),
                size=Size(rightmost_x - leftmost_x, 0),
            )
