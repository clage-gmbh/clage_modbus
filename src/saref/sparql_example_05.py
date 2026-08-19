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
        "https://clage.de/ontology/value/": "clage-value:",
        "https://clage.de/ontology/": "clage:",
    }
    for iri, prefix in prefixes.items():
        if text.startswith(iri):
            return f"{prefix}{text.removeprefix(iri)}"
    return text


def literal_decimal(value):
    return Decimal(str(value))


def step_size(current_value, fine_min, fine_max, fine_step, coarse_step):
    if fine_min <= current_value < fine_max:
        return fine_step
    return coarse_step


def raw_flow_value(engineering_value):
    return int(engineering_value * Decimal("10"))


# Find a relative flow-limit adjustment by meaning, not by CLAGE name.
stepper_query = g.query("""
PREFIX clage: <https://clage.de/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?adjustment ?comment ?target ?command ?operation ?signal ?id ?register ?datatype
       ?stepUnit ?fineStep ?fineMin ?fineMax ?coarseStep ?coarseMin ?coarseMax
       ?positiveEffect ?negativeEffect ?panelFunction
       (GROUP_CONCAT(?functionCode; separator=", ") AS ?functionCodes)
WHERE {
  ?adjustment a clage:RelativeAdjustmentProperty ;
              clage:valueRole clage:AdjustmentRole ;
              clage:quantityKind clage:FlowRateAdjustment ;
              clage:adjustsProperty ?target ;
              clage:stepEngineeringUnit ?stepUnit ;
              clage:fineStepEngineeringValue ?fineStep ;
              clage:fineStepMinEngineeringValue ?fineMin ;
              clage:fineStepMaxEngineeringValue ?fineMax ;
              clage:coarseStepEngineeringValue ?coarseStep ;
              clage:coarseStepMinEngineeringValue ?coarseMin ;
              clage:coarseStepMaxEngineeringValue ?coarseMax ;
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
         ?stepUnit ?fineStep ?fineMin ?fineMax ?coarseStep ?coarseMin ?coarseMax
         ?positiveEffect ?negativeEffect ?panelFunction
ORDER BY ?adjustment
""")

for row in stepper_query:
    fine_min = literal_decimal(row.fineMin)
    fine_max = literal_decimal(row.fineMax)
    fine_step = literal_decimal(row.fineStep)
    coarse_step = literal_decimal(row.coarseStep)

    print("control: flow-limit stepper")
    print(f"  adjustment property: {compact(row.adjustment)}")
    print(f"  adjusts limit: {compact(row.target)}")
    if row.comment:
        print(f"  comment: {row.comment}")
    print(f"  panel equivalent: {row.panelFunction}")
    print(f"  positive write: {row.positiveEffect}")
    print(f"  negative write: {row.negativeEffect}")
    print(f"  fine step: {fine_step} {row.stepUnit} from {row.fineMin} to {row.fineMax}")
    print(f"  coarse step: {coarse_step} {row.stepUnit} from {row.coarseMin} to {row.coarseMax}")
    print(f"  command: {compact(row.command)}")
    print(f"  operation: {compact(row.operation)}")
    print(f"  modbus register: {row.register}")
    print(f"  modbus signal address: {row.id}")
    print(f"  data type: {row.datatype}")
    print(f"  function codes: {row.functionCodes}")
    print(f"  signal: {compact(row.signal)}")

    print("  example UI actions:")
    for current_value, write_value in [
        (Decimal("4.5"), Decimal("1")),
        (Decimal("9.5"), Decimal("1")),
        (Decimal("10.0"), Decimal("1")),
        (Decimal("11.0"), Decimal("-1")),
    ]:
        direction = 1 if write_value > 0 else -1
        size = step_size(current_value, fine_min, fine_max, fine_step, coarse_step)
        next_value = current_value + (size * direction)
        print(
            f"    current {current_value} l/min, write {write_value}: "
            f"next limit approx. {next_value} l/min"
        )


# Find absolute flow-limit controls and their special API values.
selector_query = g.query("""
PREFIX clage: <https://clage.de/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?limit ?comment ?command ?operation ?signal ?id ?register ?datatype
       ?min ?max ?rawMin ?rawMax ?scale ?unit
       ?specialValue ?specialRaw ?specialEngineering ?display ?meaning ?prioritizes ?disables
       (GROUP_CONCAT(?functionCode; separator=", ") AS ?functionCodes)
WHERE {
  ?limit a clage:LimitProperty ;
         clage:quantityKind clage:FlowRate ;
         clage:constrainsProperty ?limitedProperty ;
         clage:engineeringUnit ?unit ;
         clage:scaleFactor ?scale ;
         clage:minEngineeringValue ?min ;
         clage:maxEngineeringValue ?max ;
         clage:minRawValue ?rawMin ;
         clage:maxRawValue ?rawMax ;
         clage:hasWriteCommand ?command ;
         clage:hasWriteOperation ?operation .

  OPTIONAL { ?limit rdfs:comment ?comment }

  ?operation clage:accessedViaModbusSignal ?signal .

  ?signal clage:mapsToSarefProperty ?limit ;
          clage:modbusSignalAddress ?id ;
          clage:historicName ?register ;
          clage:dataType ?datatype ;
          clage:access "read/write" ;
          clage:functionCode ?functionCode .

  OPTIONAL {
    ?limit clage:hasSpecialValue ?specialValue .
    ?specialValue clage:rawValue ?specialRaw ;
                  clage:engineeringValue ?specialEngineering ;
                  clage:displayLabel ?display ;
                  clage:valueMeaning ?meaning .
    OPTIONAL { ?specialValue clage:prioritizesProperty ?prioritizes }
    OPTIONAL { ?specialValue clage:disablesLimitationOfProperty ?disables }
  }
}
GROUP BY ?limit ?comment ?command ?operation ?signal ?id ?register ?datatype
         ?min ?max ?rawMin ?rawMax ?scale ?unit
         ?specialValue ?specialRaw ?specialEngineering ?display ?meaning ?prioritizes ?disables
ORDER BY ?limit ?specialRaw
""")

selector_rows = list(selector_query)
if selector_rows:
    first = selector_rows[0]
    print()
    print("control: flow-limit selector")
    print(f"  limit property: {compact(first.limit)}")
    if first.comment:
        print(f"  comment: {first.comment}")
    print(f"  engineering range: {first.min}..{first.max} {first.unit}")
    print(f"  raw range: {first.rawMin}..{first.rawMax}")
    print(f"  raw conversion: raw = l/min / {first.scale}")
    print(f"  command: {compact(first.command)}")
    print(f"  operation: {compact(first.operation)}")
    print(f"  modbus register: {first.register}")
    print(f"  modbus signal address: {first.id}")
    print(f"  data type: {first.datatype}")
    print(f"  function codes: {first.functionCodes}")
    print(f"  signal: {compact(first.signal)}")

    print("  regular selectable values:")
    for engineering_value in [Decimal("4.5"), Decimal("5.0"), Decimal("10.0"), Decimal("14.0")]:
        print(f"    {engineering_value} l/min -> raw {raw_flow_value(engineering_value)}")

    print("  special selectable values:")
    for row in selector_rows:
        if not row.specialValue:
            continue
        print(
            f"    {row.display}: raw {row.specialRaw}, engineering {row.specialEngineering} l/min"
        )
        print(f"      meaning: {row.meaning}")
        if row.prioritizes:
            print(f"      prioritizes: {compact(row.prioritizes)}")
        if row.disables:
            print(f"      disables limitation of: {compact(row.disables)}")


# EOF
