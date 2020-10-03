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
    Children = "FAMC"
    Spouses = "FAMS"
    BirthDate = "BIRT"
    DeathDate = "DEAT"
    Date = "DATE"
    Sex = "SEX"


class Sex(Enum):
    Male = "M"
    Female = "F"
    Intersex = "X"
    Unknown = "U"
    NotRecorded = "N"


class Individual(NamedTuple):
    """
    :ptr: Pointer to this individual
    :name: The name of this individual
    """

    ptr: str
    name: str
    birth: UncertainDate
    death: UncertainDate
    sex: Sex


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

    @staticmethod
    def _has_tag(element: Element, tag: Tag) -> bool:
        return element.get_tag() == tag.value

    @staticmethod
    def _get_date_value(element: Element) -> UncertainDate:
        for sub_element in element.get_child_elements():
            if FamilyTree._has_tag(sub_element, Tag.Date):
                return sub_element.get_value()
        return None

    def _parse_individual(self, element: IndividualElement):
        ptr = element.get_pointer()
        name = element.get_name()
        birth = None
        death = None
        sex = Sex.Unknown
        child_of_family = []
        spouse_of_family = []
        assert ptr not in self.individuals, (ptr, name)

        for sub_element in element.get_child_elements():
            if self._has_tag(sub_element, Tag.Children):
                child_of_family.append(sub_element.get_value())
            elif self._has_tag(sub_element, Tag.Spouses):
                spouse_of_family.append(sub_element.get_value())
            elif self._has_tag(sub_element, Tag.BirthDate):
                birth = self._get_date_value(sub_element)
            elif self._has_tag(sub_element, Tag.DeathDate):
                death = self._get_date_value(sub_element)
            elif self._has_tag(sub_element, Tag.Sex):
                sex = Sex(sub_element.get_value())

        self.individuals[ptr] = Individual(ptr, name, birth, death, sex)
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
