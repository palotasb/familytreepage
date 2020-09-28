import argparse
import sys
from enum import Enum
from typing import Dict, List, NamedTuple, Optional, Union

import gedcom
import matplotlib.pyplot as plt
import networkx as nx
from gedcom.element.element import Element
from gedcom.element.family import FamilyElement
from gedcom.element.individual import IndividualElement
from gedcom.parser import Parser

argp = argparse.ArgumentParser(__name__)
argp.add_argument("gedfile", type=str, help=".ged GEDCOM file to use as input")


class Rel(Enum):
    IsChildOfFamily = "FAMC"
    FamilyChildren = "-FAMC"
    IsSpouseOfFamily = "FAMS"
    FamilySpouses = "-FAMS"


class Individual(NamedTuple):
    """
    :ptr: Pointer to this individual
    :name: The name of this individual
    """

    ptr: str
    name: str
    child_of_family: List[str]
    spouse_of_family: List[str]


class Family(NamedTuple):
    """
    :ptr: Pointer to this family
    """

    ptr: str


class FamilyTree:
    def __init__(self, gedcom_file_path: str):
        self.individuals: Dict[str, Individual] = {}
        self.families: Dict[str, Family] = {}

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

    @staticmethod
    def _is_child_of_family(child_element: Element) -> bool:
        return child_element.get_tag() == Rel.IsChildOfFamily.value

    @staticmethod
    def _is_spouse_of_family(child_element: Element) -> bool:
        return child_element.get_tag() == Rel.IsSpouseOfFamily.value

    def _parse_individual(self, element: IndividualElement):
        individual = Individual(
            ptr=element.get_pointer(),
            name=element.get_name(),
            child_of_family=[],
            spouse_of_family=[],
        )
        assert individual.ptr not in self.individuals, individual

        for child_element in element.get_child_elements():
            if self._is_child_of_family(child_element):
                individual.child_of_family.append(child_element.get_value())
            if self._is_spouse_of_family(child_element):
                individual.spouse_of_family.append(child_element.get_value())

        self.individuals[individual.ptr] = individual
        self.graph.add_node(individual.ptr, individual=individual)
        for family in individual.child_of_family:
            self.graph.add_edge(individual.ptr, family, key=Rel.IsChildOfFamily)
            self.graph.add_edge(family, individual.ptr, key=Rel.FamilyChildren)
        for family in individual.spouse_of_family:
            self.graph.add_edge(individual.ptr, family, key=Rel.IsSpouseOfFamily)
            self.graph.add_edge(family, individual.ptr, key=Rel.FamilySpouses)

    def _parse_family(self, element: FamilyElement):
        family = Family(ptr=element.get_pointer())
        assert family.ptr not in self.families, family
        self.families[family.ptr] = family
        self.graph.add_node(family.ptr, family=family)


def generate():
    args = argp.parse_args(sys.argv[1:])
    print("gedfile:", args.gedfile)

    family_tree = FamilyTree(args.gedfile)

    print("Individuals:")
    for individual in family_tree.individuals.values():
        print(individual)

    nx.draw(
        family_tree.graph,
        labels=dict(**{
            ptr: " ".join(item.name) for ptr, item in family_tree.individuals.items()
        }),
    )
    plt.draw()
    plt.show()

    # input()

    # print("Families:")
    # for family in family_tree.families.values():
    #     print(family)
