import pymongo
import itertools

from pymatgen.entries.computed_entries import ComputedStructureEntry

class LocalMP:
    def __init__(self) -> None:
        client = pymongo.MongoClient()
        db = client.matproj
        self.entry_col = db['entries']
        self.entry_mod_col = db['entries_mod_new']
    
    def get_entries_in_chemsys(
        self,
        elements,
        inc_structure = True,
        additional_criteria = None
    ):
        if isinstance(elements, str):
            elements = elements.split("-")
        all_chemsyses = []
        for i in range(len(elements)):
            for ele in itertools.combinations(elements, i + 1):
                all_chemsyses.append("-".join(sorted(ele)))
        criteria = {"chemsys": {"$in": all_chemsyses}}
        if additional_criteria:
            criteria.update(additional_criteria)
        entries = []
        for r in self.entry_mod_col.find(criteria):
            entries.append(ComputedStructureEntry.from_dict(r))
        return entries

    def add_props_into_entries(self) -> None:
        self.entry_mod_col.delete_many({})

        batch_size = 1000
        cursor = self.entry_col.find().batch_size(batch_size)
        total_entries = self.entry_col.estimated_document_count()
        entries_processed = 0
        entry_docs_batch = []
        i = 0
        for entry in cursor:
            i += 1
            print(i, entry['composition'])
            e = ComputedStructureEntry.from_dict(entry)
            comp = e.composition
            elements = sorted(e.composition.keys())
            elements_str = sorted([el.symbol for el in elements])
            entry["pretty_formula"] = comp.reduced_formula
            entry["elements"] = elements_str
            entry["nelements"] = len(comp)
            entry["chemsys"] = "-".join(elements_str)
            entry_docs_batch.append(entry)
            entries_processed += 1
            if entries_processed % batch_size == 0:
                self.entry_mod_col.insert_many(entry_docs_batch)
                print(f"Processed {entries_processed}/{total_entries} entries")
                entry_docs_batch = []
                
        self.entry_mod_col.insert_many(entry_docs_batch)
        print(f"Processed {entries_processed}/{total_entries} entries")
        cursor.close()
        return

def main() -> None :
    mpr = LocalMP()
    mpr.add_props_into_entries()
    return 

if __name__ == "__main__":
    main()