from collections import defaultdict
from dataclasses import dataclass
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
    Tuple,
    Union,
)

from .family_tree import FamilyID, FamilyTree, IndividualID


class Point(NamedTuple):
    x: Union[int, float]
    y: Union[int, float]


Size = Point


def _ftoic(f: Union[int, float]) -> Union[int, float]:
    return int(f) if isinstance(f, float) and f.is_integer() else f  # type: ignore


@dataclass
class Box:
    pos: Point
    size: Point

    @property
    def top(self) -> Point:
        return Point(_ftoic(self.pos.x + self.size.x / 2), _ftoic(self.pos.y))

    @property
    def right(self) -> Point:
        return Point(
            _ftoic(self.pos.x + self.size.x), _ftoic(self.pos.y + self.size.y / 2)
        )

    @property
    def bottom(self) -> Point:
        return Point(
            _ftoic(self.pos.x + self.size.x / 2), _ftoic(self.pos.y + self.size.y)
        )

    @property
    def left(self) -> Point:
        return Point(_ftoic(self.pos.x), _ftoic(self.pos.y + self.size.y / 2))

    @property
    def center(self) -> Point:
        return Point(
            _ftoic(self.pos.x + self.size.x / 2), _ftoic(self.pos.y + self.size.y / 2)
        )


@dataclass
class IndividualLayout(Box):
    alevel: int  # absolute level
    rlevel: int  # relative level
    group: int


@dataclass
class FamilyLayout(Box):
    alevel: int
    rlevel: int
    outermost_parents: Optional[Tuple[IndividualID, IndividualID]]
    outermost_children: Optional[Tuple[IndividualID, IndividualID]]


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

        self.alevels: Dict[IndividualID, int] = {}
        self.min_alevel = 0
        self.max_alevel = 0
        self.level_count = 1

        self.groups: DefaultDict[int, List[IndividualID]] = defaultdict(list)
        self.group_index: Dict[IndividualID, int] = {}
        self.max_group_size = 0

        self._init_levels(starting_at)  # Updates previous three attributes!

        self.individuals: Dict[IndividualID, IndividualLayout] = {}
        self._init_individuals()

        self.families: Dict[FamilyID, FamilyLayout] = {}
        self._init_families()

        self.width = (
            self.padding.x + self.box_size.x
        ) * self.max_group_size + self.padding.x
        self.height = (
            self.level_count * (self.box_size.y + self.padding.y) + self.padding.y
        )

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
            self.alevels[id] = level
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

        all_levels: Set[int] = set(self.alevels.values())
        self.min_alevel = min(all_levels)
        self.max_alevel = max(all_levels)
        self.level_count = self.max_alevel - self.min_alevel + 1

        for group in self.groups.values():
            self.max_group_size = max(self.max_group_size, len(group))
            for index, id in enumerate(group):
                self.group_index[id] = index

    def _init_individuals(self):
        ft = self.family_tree
        for id, individual in ft.individuals.items():
            if id not in self.alevels:
                continue

            level_from_start = self.alevels[id] - self.min_alevel
            pos_x = (self.padding.x + self.box_size.x) * self.group_index.get(
                id, len(self.groups[self.alevels[id]])
            ) + self.padding.x
            pos_y = (
                self.padding.y + self.box_size.y
            ) * level_from_start + self.padding.y

            self.individuals[id] = IndividualLayout(
                alevel=self.alevels[id],
                rlevel=self.alevels[id] - self.min_alevel,
                group=self.group_index[id],
                pos=Point(x=pos_x, y=pos_y),
                size=self.box_size,
            )

    def _init_families(self):
        ft = self.family_tree
        for fid, family in self.family_tree.families.items():
            alevel = None
            spouses = list(ft.family_spouses(fid))
            children = list(ft.family_children(fid))
            if spouses and spouses[0] in self.individuals:
                alevel = self.individuals[spouses[0]].alevel
            elif children and children[0] in self.individuals:
                alevel = self.individuals[children[0]].alevel + 1
            else:
                continue

            def outermost_members(
                alevel: int, members: Iterable[IndividualID]
            ) -> Optional[Tuple[IndividualID, IndividualID]]:
                members = list(
                    filter(lambda id: self.individuals[id].alevel == alevel, members)
                )
                if not members:
                    return None

                indices = list(map(lambda id: (self.group_index[id], id), members))

                leftmost = min(indices, key=lambda tuple: tuple[0])
                rightmost = max(indices, key=lambda tuple: tuple[0])
                return (leftmost[1], rightmost[1])

            outermost_parents = outermost_members(alevel, spouses)
            outermost_children = outermost_members(alevel + 1, children)

            assert outermost_parents or outermost_children

            leftmost_ids = ([outermost_parents[0]] if outermost_parents else []) + (
                [outermost_children[0]] if outermost_children else []
            )
            rightmost_ids = ([outermost_parents[1]] if outermost_parents else []) + (
                [outermost_children[1]] if outermost_children else []
            )

            def center_x(id: IndividualID) -> Union[int, float]:
                return self.individuals[id].center.x

            leftmost_x = min(map(center_x, leftmost_ids))
            rightmost_x = max(map(center_x, rightmost_ids))

            rlevel = alevel - self.min_alevel
            y = _ftoic(
                (self.padding.y + self.box_size.y) * (rlevel + 1) + self.padding.y / 2
            )

            self.families[fid] = FamilyLayout(
                alevel=alevel,
                rlevel=rlevel,
                outermost_parents=outermost_parents,
                outermost_children=outermost_children,
                pos=Point(leftmost_x, y),
                size=Size(rightmost_x - leftmost_x, 0),
            )
