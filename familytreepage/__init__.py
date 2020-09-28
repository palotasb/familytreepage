import argparse
import sys

import gedcom
import matplotlib.pyplot as plt
import networkx as nx

from .family_tree import FamilyTree

argp = argparse.ArgumentParser(__name__)
argp.add_argument("gedfile", type=str, help=".ged GEDCOM file to use as input")


def generate():
    args = argp.parse_args(sys.argv[1:])
    print("gedfile:", args.gedfile)

    family_tree = FamilyTree(args.gedfile)

    print("Individuals:")
    for individual in family_tree.individuals.values():
        print(individual)

    nx.draw(
        family_tree.graph,
        labels=dict(
            **{
                ptr: " ".join(item.name)
                for ptr, item in family_tree.individuals.items()
            }
        ),
    )
    plt.draw()
    plt.show()
