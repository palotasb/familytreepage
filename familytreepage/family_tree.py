from __future__ import annotations

import datetime
from enum import Enum
from typing import Dict, Iterable, List, Literal, NamedTuple, Optional, Union

import networkx as nx
from gedcom.element.element import Element
from gedcom.element.family import FamilyElement
from gedcom.element.individual import IndividualElement
from gedcom.parser import Parser


class UncertainDate(NamedTuple):
    date: datetime.date
    known: Union[Literal["YMD"], Literal["YM"], Literal["Y"], Literal[""]]

    def __str__(self) -> str:
        return (
            f"{self.date.year if 'Y' in self.known else '?'}. "
            f"{self.date.month if 'M' in self.known else '?'}. "
            f"{self.date.day if 'D' in self.known else '?'}."
        )

    def __repr__(self) -> str:
        return (
            f"UncertainDate("
            f"{self.date.year if 'Y' in self.known else '?'}. "
            f"{self.date.month if 'M' in self.known else '?'}. "
            f"{self.date.day if 'D' in self.known else '?'}."
            f")"
        )


class Rel(Enum):
    IsChildOfFamily = "FAMC"
    FamilyChildren = "-FAMC"
    IsSpouseOfFamily = "FAMS"
    FamilySpouses = "-FAMS"
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
    child_of_family: List[str]
    spouse_of_family: List[str]


class Family(NamedTuple):
    """
    :ptr: Pointer to this family
    """

    ptr: str


IndividualID = str

FamilyID = str


class FamilyTree:
    def __init__(self, gedcom_file_path: str):
        self.individuals: Dict[IndividualID, Individual] = {}
        self.families: Dict[FamilyID, Family] = {}

        self.graph = nx.MultiDiGraph()

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

    def parent_families_of(self, individual_id: IndividualID) -> Iterable[FamilyID]:
        all_families = self.graph.edges(
            individual_id, keys=Rel.IsChildOfFamily, data=True
        )
        parent_families = filter(
            lambda family_edge: family_edge[2]["rel"] == Rel.IsChildOfFamily.value,
            all_families,
        )
        return map(lambda family_edge: family_edge[1], parent_families)

    def own_families_of(self, individual_id: IndividualID) -> Iterable[FamilyID]:
        all_families = self.graph.edges(
            individual_id, keys=Rel.IsChildOfFamily, data=True
        )
        parent_families = filter(
            lambda family_edge: family_edge[2]["rel"] == Rel.IsSpouseOfFamily.value,
            all_families,
        )
        return map(lambda family_edge: family_edge[1], parent_families)

    @staticmethod
    def _is_child_of_family(child_element: Element) -> bool:
        return child_element.get_tag() == Rel.IsChildOfFamily.value

    @staticmethod
    def _is_spouse_of_family(child_element: Element) -> bool:
        return child_element.get_tag() == Rel.IsSpouseOfFamily.value

    @staticmethod
    def _is_birth_data(child_element: Element) -> bool:
        return child_element.get_tag() == Rel.BirthDate.value

    @staticmethod
    def _is_death_data(child_element: Element) -> bool:
        return child_element.get_tag() == Rel.DeathDate.value

    @staticmethod
    def _get_date_value(child_element: Element) -> UncertainDate:
        for grandchild_element in child_element.get_child_elements():
            if grandchild_element.get_tag() == Rel.Date.value:
                return grandchild_element.get_value()
        return UncertainDate(datetime.date.min, "")

    def _parse_individual(self, element: IndividualElement):
        individual = Individual(
            ptr=element.get_pointer(),
            name=element.get_name(),
            birth=UncertainDate(datetime.date.min, known=""),
            death=UncertainDate(datetime.date.min, known=""),
            child_of_family=[],
            spouse_of_family=[],
        )
        assert individual.ptr not in self.individuals, individual

        for child_element in element.get_child_elements():
            if self._is_child_of_family(child_element):
                individual.child_of_family.append(child_element.get_value())
            elif self._is_spouse_of_family(child_element):
                individual.spouse_of_family.append(child_element.get_value())
            elif self._is_birth_data(child_element):
                individual = individual._replace(
                    birth=self._get_date_value(child_element)
                )
            elif self._is_death_data(child_element):
                individual = individual._replace(
                    death=self._get_date_value(child_element)
                )

        self.individuals[individual.ptr] = individual
        self.graph.add_node(individual.ptr, individual=individual)
        for family in individual.child_of_family:
            self.graph.add_edge(individual.ptr, family, rel=Rel.IsChildOfFamily.value)
            self.graph.add_edge(family, individual.ptr, rel=Rel.FamilyChildren.value)
        for family in individual.spouse_of_family:
            self.graph.add_edge(individual.ptr, family, rel=Rel.IsSpouseOfFamily.value)
            self.graph.add_edge(family, individual.ptr, rel=Rel.FamilySpouses.value)

    def _parse_family(self, element: FamilyElement):
        family = Family(ptr=element.get_pointer())
        assert family.ptr not in self.families, family
        self.families[family.ptr] = family
        self.graph.add_node(family.ptr, family=family)
