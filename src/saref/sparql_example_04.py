#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from decimal import Decimal

from rdflib import Graph

g = Graph()
g.parse("clage_modbus_tab.ttl", format="turtle")


def compact(value):
    text = str(value)
    prefixes = {
        "https://clage.de/ontology/modbus/signal/": "modbus-signal:",
        "https://clage.de/ontology/modbus/operation/write/": "modbus-write:",
        "https://clage.de/ontology/command/write/": "clage-write:",
        "https://clage.de/ontology/": "clage:",
    }
    for iri, prefix in prefixes.items():
        if text.startswith(iri):
            return f"{prefix}{text.removeprefix(iri)}"
    return text


def literal_decimal(value):
    return Decimal(str(value))


def step_size(current_value, fine_min, fine_max, fine_step, coarse_step):
    if fine_min <= current_value <= fine_max:
        return fine_step
    return coarse_step


# Find relative temperature adjustment controls by meaning, not by CLAGE name.
q = g.query("""
PREFIX clage: <https://clage.de/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?adjustment ?comment ?target ?command ?operation ?signal ?id ?register ?datatype
       ?stepUnit ?coarseStep ?fineStep ?fineMin ?fineMax ?positiveEffect ?negativeEffect
       ?panelFunction
       (GROUP_CONCAT(?functionCode; separator=", ") AS ?functionCodes)
WHERE {
  ?adjustment a clage:RelativeAdjustmentProperty ;
              clage:valueRole clage:AdjustmentRole ;
              clage:quantityKind clage:TemperatureAdjustment ;
              clage:adjustsProperty ?target ;
              clage:stepEngineeringUnit ?stepUnit ;
              clage:coarseStepEngineeringValue ?coarseStep ;
              clage:fineStepEngineeringValue ?fineStep ;
              clage:fineStepMinEngineeringValue ?fineMin ;
              clage:fineStepMaxEngineeringValue ?fineMax ;
              clage:positiveDeltaEffect ?positiveEffect ;
              clage:negativeDeltaEffect ?negativeEffect ;
              clage:equivalentPanelFunction ?panelFunction ;
              clage:hasWriteCommand ?command ;
              clage:hasWriteOperation ?operation .

  OPTIONAL { ?adjustment rdfs:comment ?comment }

  ?operation clage:accessedViaModbusSignal ?signal .

  ?signal clage:mapsToSarefProperty ?adjustment ;
          clage:modbusSignalAddress ?id ;
          clage:historicName ?register ;
          clage:dataType ?datatype ;
          clage:access "read/write" ;
          clage:functionCode ?functionCode .
}
GROUP BY ?adjustment ?comment ?target ?command ?operation ?signal ?id ?register ?datatype
         ?stepUnit ?coarseStep ?fineStep ?fineMin ?fineMax ?positiveEffect ?negativeEffect
         ?panelFunction
ORDER BY ?adjustment
""")

for row in q:
    fine_min = literal_decimal(row.fineMin)
    fine_max = literal_decimal(row.fineMax)
    fine_step = literal_decimal(row.fineStep)
    coarse_step = literal_decimal(row.coarseStep)

    print("control: temperature stepper")
    print(f"  adjustment property: {compact(row.adjustment)}")
    print(f"  adjusts setpoint: {compact(row.target)}")
    if row.comment:
        print(f"  comment: {row.comment}")
    print(f"  panel equivalent: {row.panelFunction}")
    print(f"  positive write: {row.positiveEffect}")
    print(f"  negative write: {row.negativeEffect}")
    print(f"  coarse step: {coarse_step} {row.stepUnit}")
    print(f"  fine step: {fine_step} {row.stepUnit} from {fine_min} to {fine_max} deg C")
    print(f"  command: {compact(row.command)}")
    print(f"  operation: {compact(row.operation)}")
    print(f"  modbus register: {row.register}")
    print(f"  modbus signal address: {row.id}")
    print(f"  data type: {row.datatype}")
    print(f"  function codes: {row.functionCodes}")
    print(f"  signal: {compact(row.signal)}")

    print("  example UI actions:")
    for current_value, write_value in [
        (Decimal("34.0"), Decimal("1")),
        (Decimal("40.0"), Decimal("1")),
        (Decimal("40.0"), Decimal("-1")),
        (Decimal("44.0"), Decimal("-1")),
    ]:
        direction = 1 if write_value > 0 else -1
        size = step_size(current_value, fine_min, fine_max, fine_step, coarse_step)
        next_value = current_value + (size * direction)
        print(
            f"    current {current_value} deg C, write {write_value}: "
            f"next setpoint approx. {next_value} deg C"
        )


# EOF
