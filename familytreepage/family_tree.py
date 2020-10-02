from __future__ import annotations

import datetime
from enum import Enum
from functools import partial
from typing import Dict, Iterable, List, Literal, NamedTuple, Optional, Union

import networkx as nx
from gedcom.element.element import Element
from gedcom.element.family import FamilyElement
from gedcom.element.individual import IndividualElement
from gedcom.parser import Parser

UncertainDate = Optional[str]


class Rel(Enum):
    Children = "FAMC"
    Spouses = "FAMS"


class Tag(Enum):
    BirthDate = "BIRT"
    DeathDate = "DEAT"
    Date = "DATE"


class Individual(NamedTuple):
    """
    :ptr: Pointer to this individual
    :name: The name of this individual
    """

    ptr: str
    name: str
    birth: UncertainDate
    death: UncertainDate


class Family(NamedTuple):
    """
    :ptr: Pointer to this family
    """

    ptr: str


IndividualID = str

FamilyID = str

AnyID = Union[IndividualID, FamilyID]


class FamilyTree:
    def __init__(self, gedcom_file_path: str):
        self.individuals: Dict[IndividualID, Individual] = {}
        self.families: Dict[FamilyID, Family] = {}

        self.graph = nx.Graph()

        self.parse(gedcom_file_path)

    def parse(self, gedcom_file_path: str):
        parser = Parser()
        parser.parse_file(gedcom_file_path)
        root = parser.get_root_child_elements()

        for element in root:
            if isinstance(element, IndividualElement):
                self._parse_individual(element)
            elif isinstance(element, FamilyElement):
                self._parse_family(element)

    def _traverse(self, id: AnyID, rel: Rel) -> Iterable[AnyID]:
        edges = self.graph.edges(id, data=True)
        edges = filter(lambda edge: edge[2]["rel"] == rel.value, edges)
        return map(lambda edge: edge[1], edges)

    def parent_families_of(self, individual_id: IndividualID) -> Iterable[FamilyID]:
        return self._traverse(individual_id, rel=Rel.Children)

    def own_families_of(self, individual_id: IndividualID) -> Iterable[FamilyID]:
        return self._traverse(individual_id, rel=Rel.Spouses)

    def spouses_of_family(self, family_id: FamilyID) -> Iterable[IndividualID]:
        return self._traverse(family_id, rel=Rel.Spouses)

    def children_of_family(self, family_id: FamilyID) -> Iterable[IndividualID]:
        return self._traverse(family_id, rel=Rel.Children)

    def _levels(self, at: IndividualID, level_dict: Dict[IndividualID, int]) -> None:
        flatten = lambda lists: [item for sublist in lists for item in sublist]
        this_level = level_dict[at]

        def level_relation(family_to_person, person_to_family, delta_level):
            relations = flatten(map(family_to_person, person_to_family(at)))
            new_relations = list(filter(lambda id: id not in level_dict, relations))

            for relation in new_relations:
                level_dict[relation] = this_level + delta_level

            return new_relations

        spouses = level_relation(self.spouses_of_family, self.own_families_of, 0)
        parents = level_relation(self.spouses_of_family, self.parent_families_of, -1)
        children = level_relation(self.children_of_family, self.own_families_of, 1)

        # It is important that this loop is after the other loops and we visit
        # individuals breadth-first and not depth-first as it will result it more
        # consistent levels
        for id in spouses + parents + children:
            self._levels(id, level_dict)

    def levels(self, starting_at: IndividualID) -> Dict[IndividualID, int]:
        level_dict = {starting_at: 0}
        self._levels(starting_at, level_dict)
        return level_dict

    @staticmethod
    def _is_child_of_family(child_element: Element) -> bool:
        return child_element.get_tag() == Rel.Children.value

    @staticmethod
    def _is_spouse_of_family(child_element: Element) -> bool:
        return child_element.get_tag() == Rel.Spouses.value

    @staticmethod
    def _is_birth_data(child_element: Element) -> bool:
        return child_element.get_tag() == Tag.BirthDate.value

    @staticmethod
    def _is_death_data(child_element: Element) -> bool:
        return child_element.get_tag() == Tag.DeathDate.value

    @staticmethod
    def _get_date_value(child_element: Element) -> UncertainDate:
        for grandchild_element in child_element.get_child_elements():
            if grandchild_element.get_tag() == Tag.Date.value:
                return grandchild_element.get_value()
        return None

    def _parse_individual(self, element: IndividualElement):
        ptr = element.get_pointer()
        name = element.get_name()
        birth = None
        death = None
        child_of_family = []
        spouse_of_family = []
        assert ptr not in self.individuals, (ptr, name)

        for child_element in element.get_child_elements():
            if self._is_child_of_family(child_element):
                child_of_family.append(child_element.get_value())
            elif self._is_spouse_of_family(child_element):
                spouse_of_family.append(child_element.get_value())
            elif self._is_birth_data(child_element):
                birth = self._get_date_value(child_element)
            elif self._is_death_data(child_element):
                death = self._get_date_value(child_element)

        self.individuals[ptr] = Individual(ptr, name, birth, death)
        self.graph.add_node(ptr)
        for family in child_of_family:
            self.graph.add_edge(ptr, family, rel=Rel.Children.value)
        for family in spouse_of_family:
            self.graph.add_edge(ptr, family, rel=Rel.Spouses.value)

    def _parse_family(self, element: FamilyElement):
        family = Family(ptr=element.get_pointer())
        assert family.ptr not in self.families, family
        self.families[family.ptr] = family
        self.graph.add_node(family.ptr, family=family)
