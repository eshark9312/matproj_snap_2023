from enum import Enum

class Props(Enum):
    Elastiicity = "elasticity"
    Dielectric = "dielectric"
    Piezoelectric = "piezoelectric"
    EOS = "eos"
    Magnetism ="magnetism"
    Electronic_structure = "electronic_structure"

class ExportTypes(Enum):
    Dump = "dump"
    Json = "json"
    Gzip = "gzip"

class MPCollections(Enum):
    Summary = "summary"
    Entries = "entries"
    Provenance = "provenance"
    Elastiicity = "elasticity"
    Dielectric = "dielectric"
    Piezoelectric = "piezoelectric"
    EOS = "eos"
    Magnetism ="magnetism"
    Electronic_structure = "electronic_structure"

class Bundle_col(Enum):
    Bandstructure = "bs"
    DOS = "dos"
    PDOS = "pdos"
    PDOSN = "pdos_new"
    