#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rdflib import Graph

g = Graph()
g.parse("clage_modbus_tab.ttl", format="turtle")


DISPLAY_PREFIXES = {
    "https://clage.de/ontology/modbus/signal/": "modbus-signal:",
    "https://clage.de/ontology/modbus/": "modbus:",
    "https://clage.de/ontology/": "clage:",
}


def compact(value):
    text = str(value)
    for iri, prefix in DISPLAY_PREFIXES.items():
        if text.startswith(iri):
            return f"{prefix}{text.removeprefix(iri)}"
    return text


def sorted_function_codes(value):
    return ", ".join(sorted(str(value).split(", ")))


def print_table(records):
    headers = {
        "id": "id",
        "register": "register",
        "access": "access",
        "datatype": "type",
        "function_codes": "function codes",
        "property": "property",
        "signal": "signal",
    }
    columns = list(headers)
    widths = {
        column: max(len(headers[column]), *(len(record[column]) for record in records))
        for column in columns
    }

    header = "  ".join(headers[column].ljust(widths[column]) for column in columns)
    ruler = "  ".join("-" * widths[column] for column in columns)
    print(header)
    print(ruler)
    for record in records:
        print("  ".join(record[column].ljust(widths[column]) for column in columns))


# List the complete Modbus register map with its semantic property.
rows = g.query("""
PREFIX clage: <https://clage.de/ontology/>

SELECT ?id ?register ?access ?datatype ?property ?signal
       (GROUP_CONCAT(?functionCode; separator=", ") AS ?functionCodes)
WHERE {
  ?signal clage:mapsToSarefProperty ?property ;
          clage:modbusSignalAddress ?id ;
          clage:historicName ?register ;
          clage:dataType ?datatype ;
          clage:access ?access ;
          clage:functionCode ?functionCode .
}
GROUP BY ?id ?register ?access ?datatype ?property ?signal
ORDER BY ?register ?id ?property
""")

records = [
    {
        "id": str(row.id),
        "register": str(row.register),
        "access": str(row.access),
        "datatype": str(row.datatype),
        "function_codes": sorted_function_codes(row.functionCodes),
        "property": compact(row.property),
        "signal": compact(row.signal),
    }
    for row in rows
]

print_table(records)


# EOF
