#!/usr/bin/env python3

from pathlib import Path
from rdflib import Graph, URIRef, Literal, BNode
import pydot
import sys

def label(term):
    if isinstance(term, URIRef):
        text = str(term)
        return text.rstrip("/#").split("/")[-1].split("#")[-1]
    if isinstance(term, Literal):
        return str(term)
    if isinstance(term, BNode):
        return "_:" + str(term)
    return str(term)

ttl_file = Path(sys.argv[1])
svg_file = ttl_file.with_suffix(".svg")

g = Graph()
g.parse(ttl_file, format="turtle")

dot = pydot.Dot(graph_type="digraph", rankdir="LR")

nodes = set()
for s, p, o in g:
    nodes.add(s)
    nodes.add(o)

for node in nodes:
    dot.add_node(pydot.Node(
        label(node),
        shape="box" if isinstance(node, Literal) else "ellipse"
    ))

for s, p, o in g:
    dot.add_edge(pydot.Edge(label(s), label(o), label=label(p)))

dot.write_svg(svg_file)
print(f"wrote {svg_file}")

# EOF