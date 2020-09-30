import argparse
import sys

import gedcom
import networkx as nx

from .family_tree import FamilyTree
from .render import render

argp = argparse.ArgumentParser(__name__)
argp.add_argument("gedfile", type=str, help=".ged GEDCOM file to use as input")
argp.add_argument(
    "--output",
    "-o",
    type=argparse.FileType("w"),
    default="familytree.html",
    help="Output HTML file for family tree",
)


def generate():
    args = argp.parse_args(sys.argv[1:])
    print("gedfile:", args.gedfile)
    print("output:", args.output.name)

    family_tree = FamilyTree(args.gedfile)
    render(family_tree, args.output)
