import subprocess
import gzip
import os
from typing import Optional
import json
import numpy as np
import uuid

import pymongo 
from pymongo.collection import Collection
from emmet.core.summary import HasProps
from mp_api.client import MPRester as mp; 

from arg_enums import Props, ExportTypes, MPCollections

class NumpyEncoder(json.JSONEncoder):
    """
        helper class for converting np.int64 into normal int
    """
    def default(self, obj):
        if isinstance(obj, np.int64):
            return int(obj)
        return json.JSONEncoder.default(self, obj)
    
class LocalMP_downloader :
    """
        This class downloads the database from Materials Project for offline use
        by means fo mp_api, then store them into local mongodb. 
    """
    mpr : None
    client : None
    db : None

    def __init__(self) -> None:
        """
            initialize the mprester api and the db connection 
        """
        self.mpr = mp(api_key="ZTv7bTga2WEwfu0N7MttGvNnVWJU60bU")
        self.client = pymongo.MongoClient() 
        self.db = self.client.matproj
        return
    
    def get_all_summary(self) -> None:
        """
            Download all the summary doc from MP, then store them into matproj.summary
        """
        collection = self.db.summary
        collection.delete_many({})
        entries = self.mpr.summary.search(fields=[
                "material_id", 
                "formula_pretty", 
                "nsites", 
                "volume", 
                "density", 
                "symmetry", 
                "formation_energy_per_atom", 
                "energy_above_hull", 
                "is_stable", 
                "band_gap", 
                "is_gap_direct", 
                "is_metal", 
                "ordering", 
                "total_magnetization", 
                "k_voigt", 
                "k_reuss", 
                "k_vrh", 
                "g_voigt", 
                "g_reuss", 
                "g_vrh", 
                "universal_anisotropy", 
                "e_total", 
                "e_ionic", 
                "e_ij_max", 
                "weighted_surface_energy", 
                "weighted_work_function", 
                "surface_anisotropy", 
                "shape_factor", 
                "theoretical",
                "has_props"
                ]) 
        i = 0
        j = 0
        total = len(entries)
        for e in entries: 
            i = i + 1
            if (i == 500 ):
                print("="*3 + " " + str(j * 500 + i) + "/" + str(total) + " " + "="*3)
                j = j + 1
                i = 0
            props_list = [props.name for props in e.has_props]
            e.has_props = props_list
            e.symmetry.crystal_system = e.symmetry.crystal_system.value
            e.symmetry = e.symmetry.dict()
            e_dict = e.__dict__
            del e_dict['fields_not_requested']
            collection.insert_one(e_dict) 
        print("="*3 + " all done : " + str(j * 500 + i) + "entries " + "="*3)
        return

    def get_all_entries(self) -> None: 
        """
            Reads all the material_ids from local_db_collection 'summary'
            then request for entries_doc of them in bundles of material_ids of size 5000
        """
        mp_ids = self._get_mpid_from_local()
        # bundling mp_ids
        total = len(mp_ids)
        mp_bundles = []
        bundle = []
        i = 0; j = 0
        for mp_id in mp_ids:
            i = i + 1 
            bundle.append(mp_id)
            if i == 5000 :
                print("="*3 + " " + str(j * 5000 + i) + "/" + str(total) + " " + "="*3)
                j = j + 1
                i = 0
                mp_bundles.append(bundle.copy())
                bundle.clear()
        mp_bundles.append(bundle.copy())
        bundle.clear()
        print("size of mp_bundles" + str(len(mp_bundles)))

        # retreiving the data in bundles 
        collection = self.db.entries 
        collection.delete_many({})
        for mp_ids in mp_bundles:
            entries = self.mpr.get_entries(chemsys_formula_mpids=mp_ids)
            docs = [e.as_dict() for e in entries] 
            collection.insert_many(docs) 
        return

    def get_all_provenance(self) -> None:
        """
            Downloads all the provenance data from materials Project 
        """
        collection = self.db.provenance 
        collection.delete_many({})
        provs = self.mpr.search({},
            fields=['material_id', 
                    'database_IDs', 
                    'references', 
                    'theoretical',
                    'origins',
                    'authors',
                    'formula_pretty'])
        doc_entries = []
        for prov in provs: 
            e = prov.dict()
            dbIDs = e['database_IDs']
            icsd = [{key.value : value} for key, value in dbIDs.items()]
            e['database_IDs'] = icsd
            del e['fields_not_requested']
            doc_entries.append(e)
        collection.insert_many(doc_entries)
        return

    def get_all_prop(self, prop : Props = Props.EOS) -> None:
        """
            Downloads all the props from MP then store into collection with its own prop. 
            available props by this method
               * elasticity
               * dielectric
               * piezoelectric
               * eos
               * magnetism
               * electronic_structure
        """
        prop_mpr = getattr(self.mpr, prop.value)
        docs_prop = prop_mpr.search({})
        collection = self.db[prop.value]
        collection.delete_many({})
        # save to db in bundles of 1000
        print("saving into db in bundles of 1000")
        i = 0; j = 0; docs = []
        for doc in docs_prop:
            i = i + 1
            doc_dict = doc.dict()
            del doc_dict['fields_not_requested']
            docs.append(doc_dict)
            if ( i == 1000 ) :
                i = 0
                j = j + 1
                collection.insert_many(docs)
                docs = []
        collection.insert_many(docs)
        return

    def _get_mpid_from_local(self, 
                             col_name : str = "summary", 
                             field_name : str = "material_id", 
                             sorted : bool = False, 
                             sort_field : str = "material_id") -> list :
        """
            Read local db for material_ids and returns the list of them
        """
        collection = self.db[col_name]
        projection = { field_name : 1, "_id" : 0}
        query_result = collection.find({}, projection).sort(sort_field) if sorted else collection.find({}, projection)
        mp_ids = []
        for document in query_result:
            mp_ids.append(document[field_name])
        return mp_ids

    def _get_prop_id(self, prop : HasProps = HasProps.bandstructure) -> None:
        """
            get all the mp_ids which as certain prop , then save into db
            for latter download of the main data for that prop.
        """
        mpid_BS = self.mpr.summary.search(
            has_props = [prop], 
            fields = ["material_id"])
        collection = self.db["mpid_" + prop.value]
        collection.delete_many({}) 
        collection.insert_many([{'material_id':str(mpid.material_id)} for mpid in mpid_BS])
        return

    def export_collection(self, 
                         collection : str = "summary", 
                         as_type : ExportTypes = ExportTypes.Json,
                         out_name : Optional[str] = None) -> None :
        """
            Exports the collection as json/dump/gz format
        """
        if out_name == None:
            out_name = collection
        if as_type == ExportTypes.Json:
            command = [
                'mongoexport',
                '--db', 'matproj',
                '--collection', collection,
                '--out', out_name + '.json'
            ]
        elif as_type == ExportTypes.Dump:
            command = [
                'mongodump',
                '--db', 'matproj',
                '--collection', collection
            ]
        elif as_type == ExportTypes.Gzip:
            tmp_name = str(uuid.uuid1())
            self.export_collection(out_name = tmp_name, as_type=ExportTypes.Json, collection=collection)
            with open( tmp_name + ".json", "rb") as fin:
                with gzip.open(out_name + ".gz", "wb") as fout:
                    fout.writelines(fin)
            os.remove(tmp_name + ".json")
            return
        # Execute the command
        subprocess.call(command)

    def __convert_numpy_ints(self, obj):
        """
            This function recursively traverses the nested JSON object 
            and converts any np.int64 instances it encounters 
            into a normal int.
        """
        if isinstance(obj, np.int64):
            return int(obj)
        elif isinstance(obj, list):
            return [self.__convert_numpy_ints(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self.__convert_numpy_ints(value) for key, value in obj.items()}
        else:
            return obj
        
    def _bs2db(self, mp_id : str, collection : Collection) -> None :
        """
            This function retrieves bs_doc by mp_id, then save into the collection of mongodb
        """
        bs_doc = self.mpr.get_bandstructure_by_material_id(mp_id)
        bs_doc.projections = {}
        bs_json = self.__convert_numpy_ints(bs_doc.as_dict())
        collection.insert_one({"material_id": mp_id, "bandstructure":bs_json})
        return

    def _bs2json(self, mp_id : str) -> None :
        """
            This function retrieves bs_doc by mp_id, then save into the json file with the name of bs_[mp_id].json
        """
        bs_doc = self.mpr.get_bandstructure_by_material_id(mp_id)
        bs_doc.projections = {}
        bs_json = self.__convert_numpy_ints(bs_doc.as_dict())
        file_name = 'bs_' + mp_id + '.json'
        with open(file_name, 'w') as f:
            json.dump(bs_json, f)
        
        f.close()
        return

    def get_bundle_prop_bs(self, bundle : int = 0, chunk_size : int = 1000, from_scratch : bool = False) -> None :
        """
            This function retrieves bs_docs by mp_ids in mp_bundle of chunk_size 
            and save them into collection of mongodb
            when it encounters memory overflow, this function can be called with from_scratch = False
            to skip download that mp_id, logging into 'dw_log.txt' at the same time.
        """
        mp_ids = self._get_mpid_from_local(col_name = "mpid_bandstructure", sorted = True)
        start_index = bundle * chunk_size
        last_index = bundle * chunk_size + chunk_size
        total = len(mp_ids)
        if start_index > total : 
            print("Invalid bundle number")
            return
        elif start_index >= 0 and last_index < total :
            mp_bundle = mp_ids[start_index:last_index]
        elif start_index >= 0 and last_index > total :
            mp_bundle = mp_ids[start_index:]
        else :
            print("Invalid bundle number")
            return
        collection_name = "bs_bundle_0" + str(bundle) if bundle < 10 else "bs_bundle_" + str(bundle)
        collection = self.db[collection_name]
        if from_scratch :
            collection.delete_many({})
            nDocs = 0
        else : 
            nDocs = collection.count_documents({})
            print(str(nDocs) + " documents already stored in the collection : " + collection_name)
        
        i = 0
        for mp_id in mp_bundle:
            i = i + 1
            if from_scratch or i > nDocs + 1 or nDocs == 0:
                print("-"*3 + " Bundle: " + str(bundle) + ", Number: " + str(i) + "-"*3 + mp_id + "-"*10)
                self._bs2db(mp_id, collection)
            elif i == nDocs + 1:
                print("skip downloading " + mp_id + " because of memory overflow")
                collection.insert_one({"material_id": mp_id, "exception":"memoryError"})
                with open('dw_log.txt', 'a') as f:
                    # Write the text to the file
                    f.write("skip downloading " + mp_id + " to bundle#" + str(bundle) + " because of memory overflow\n")

        return

    def _dos2db(self, mp_id : str, collection : Collection) -> None :
        """
            This function retrieves dos_doc by mp_id, then save into the collection of mongodb
        """
        dos_doc = self.mpr.get_dos_by_material_id(mp_id)
        dos_dict = dos_doc.as_dict()
        dos_pdoss = dos_doc['pdos']
        del dos_dict['pdos']
        # dos_json = self.__convert_numpy_ints(dos_doc.as_dict())
        collection.insert_one({"material_id": mp_id, "dos":dos_dict})
        self.__pdos2db(mp_id, dos_pdoss)
        return

    def __pdos2db(self, mp_id: str, dos_pdoss: list) -> None :
        pdoss = []
        for index in range(len(dos_pdoss)):
            pdos = {}
            pdos['material_id'] = mp_id
            pdos['site_index'] = index
            pdos['pdos'] = dos_pdoss[index]
            pdoss.append(pdos)
        col_pdos = self.db['pdos']
        col_pdos.insert_many(pdoss)

        return

    def get_bundle_prop_dos(self, bundle : int = 0, chunk_size : int = 1000, from_scratch : bool = False) -> None :
        """
            This function retrieves dos_docs by mp_ids in mp_bundle of chunk_size 
            and save them into collection of mongodb
            when it encounters memory overflow, this function can be called with from_scratch = False
            to skip download that mp_id, logging into 'dw_log.txt' at the same time.
        """
        mp_ids = self._get_mpid_from_local(col_name = "mpid_dos", sorted = True)
        start_index = bundle * chunk_size
        last_index = bundle * chunk_size + chunk_size
        total = len(mp_ids)
        if start_index > total : 
            print("Invalid bundle number")
            return
        elif start_index >= 0 and last_index < total :
            mp_bundle = mp_ids[start_index:last_index]
        elif start_index >= 0 and last_index > total :
            mp_bundle = mp_ids[start_index:]
        else :
            print("Invalid bundle number")
            return
        collection_name = "dos_bundle_0" + str(bundle) if bundle < 10 else "dos_bundle_" + str(bundle)
        collection = self.db[collection_name]
        if from_scratch :
            collection.delete_many({})
            nDocs = 0
        else : 
            nDocs = collection.count_documents({})
            print(str(nDocs) + " documents already stored in the collection : " + collection_name)
        
        i = 0
        for mp_id in mp_bundle:
            i = i + 1
            if from_scratch or i > nDocs + 1 or nDocs == 0:
                print("-"*3 + " Bundle: " + str(bundle) + ", Number: " + str(i) + "-"*3 + mp_id + "-"*10)
                self._dos2db(mp_id, collection)
            elif i == nDocs + 1:
                print("skip downloading " + mp_id + " because of memory overflow")
                collection.insert_one({"material_id": mp_id, "exception":"memoryError"})
                with open('dw_log.txt', 'a') as f:
                    # Write the text to the file
                    f.write("skip downloading " + mp_id + " to bundle#" + str(bundle) + " because of memory overflow\n")

        return

    def get_all_prop_bs(self) -> None:
        mp_ids = self._get_mpid_from_local(col_name = "mpid_bandstructure", sorted = True)
        for mp_id in mp_ids[0:10]:
            print(mp_id)
            # bs_doc = self.mpr.get_bandstructure_by_material_id(mp_id)
            # bs_doc.projections = {}
            # bs_json = {"material_id": mp_id, "bandstructure":bs_doc.as_dict()}
            # json_str = json.dumps(bs_json, cls=NumpyEncoder)
            # with gzip.GzipFile("bs-" + mp_id + ".gz", "wb") as gz:
                # gz.write(json_str.encode('utf-8'))
        return