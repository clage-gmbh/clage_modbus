#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rdflib import Graph

g = Graph()
g.parse("clage_modbus_tab.ttl", format="turtle")

# Build UI/control metadata for writable setpoints from the ontology.
q = g.query("""
PREFIX clage: <https://clage.de/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?property ?comment ?actuation ?operation ?signal ?id ?register ?datatype ?unit ?min ?max
       ?rawMin ?rawMax ?scale
       (GROUP_CONCAT(?functionCode; separator=", ") AS ?functionCodes)
WHERE {
  ?property a clage:SetpointProperty ;
            clage:engineeringUnit ?unit ;
            clage:minEngineeringValue ?min ;
            clage:maxEngineeringValue ?max ;
            clage:minRawValue ?rawMin ;
            clage:maxRawValue ?rawMax ;
            clage:scaleFactor ?scale .

  OPTIONAL { ?property rdfs:comment ?comment }

  ?property clage:hasActuationProfile ?actuation ;
            clage:hasWriteOperation ?operation .

  ?operation clage:accessedViaModbusSignal ?signal .

  ?signal clage:mapsToSarefProperty ?property ;
          clage:modbusSignalAddress ?id ;
          clage:historicName ?register ;
          clage:dataType ?datatype ;
          clage:access "read/write" ;
          clage:functionCode ?functionCode .
}
GROUP BY ?property ?comment ?actuation ?operation ?signal ?id ?register ?datatype ?unit
         ?min ?max ?rawMin ?rawMax ?scale
ORDER BY ?property
""")

for row in q:
    print("control: slider")
    print(f"  property: {row.property}")
    if row.comment:
        print(f"  label/comment: {row.comment}")
    print(f"  engineering range: {row.min}..{row.max} {row.unit}")
    print(f"  raw range: {row.rawMin}..{row.rawMax}")
    print(f"  conversion: raw = engineering / {row.scale}")
    print(f"  saref actuation: {row.actuation}")
    print(f"  technical operation: {row.operation}")
    print(f"  modbus register: {row.register}")
    print(f"  modbus signal address: {row.id}")
    print(f"  data type: {row.datatype}")
    print(f"  function codes: {row.functionCodes}")
    print(f"  signal: {row.signal}")

# EOF
