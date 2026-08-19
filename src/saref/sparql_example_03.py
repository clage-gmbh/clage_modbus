#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rdflib import Graph

g = Graph()
g.parse("clage_modbus_tab.ttl", format="turtle")

# Look for writable temperature setpoints by semantic meaning, not by name.
q = g.query("""
PREFIX clage: <https://clage.de/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?property ?comment ?command ?operation ?signal ?id ?register ?access ?scale ?min ?max
       (GROUP_CONCAT(?functionCode; separator=", ") AS ?functionCodes)
WHERE {
  ?property clage:valueRole clage:SetpointRole ;
            clage:quantityKind clage:Temperature ;
            clage:scaleFactor ?scale ;
            clage:minEngineeringValue ?min ;
            clage:maxEngineeringValue ?max .

  OPTIONAL { ?property rdfs:comment ?comment }
  OPTIONAL {
    ?property clage:hasWriteCommand ?command ;
              clage:hasWriteOperation ?operation .
    ?operation clage:accessedViaModbusSignal ?signal .
    ?signal clage:mapsToSarefProperty ?property ;
            clage:modbusSignalAddress ?id ;
            clage:historicName ?register ;
            clage:access ?access ;
            clage:functionCode ?functionCode .
  }
}
GROUP BY ?property ?comment ?command ?operation ?signal ?id ?register ?access ?scale ?min ?max
""")

for row in q:
    print(f"{row.property}")
    if row.comment:
        print(f"  comment: {row.comment}")
    print(f"  engineering range: {row.min}..{row.max}")
    print(f"  raw value: engineering value / {row.scale}")
    if row.signal:
        print(f"  saref command: {row.command}")
        print(f"  technical operation: {row.operation}")
        print(f"  modbus signal address: {row.id}")
        print(f"  modbus register: {row.register}")
        print(f"  access: {row.access}")
        print(f"  function codes: {row.functionCodes}")
        print(f"  signal: {row.signal}")

# EOF
