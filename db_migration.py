import pymongo
import gzip
import json

from pymongo.collection import Collection
from typing import Union, TextIO, BinaryIO
from arg_enums import ExportTypes, Bundle_col

client = pymongo.MongoClient()
db = client.matproj

class Matproj_db_migrator :
    """
        This class migrates the downloaded database data from files on disk 
        into collections of the mongodb database
    """
    client : None
    db : None

    def __init__(self) -> None:
        """
            Initialize the migrator with db
        """
        self.client = pymongo.MongoClient()
        self.db = self.client.matproj
        return

    def add_data_to_db(self,
            path_to_file : str,
            dataType : ExportTypes,
            collection : Collection,
            from_scratch : bool = False,
            add_by_docs_num : int = 1000
    ) -> None:
        """
            This function reads data from file and add those into db
        """
        if from_scratch:
            collection.drop()
        f = None
        match dataType:
            case ExportTypes.Json:
                f = open(path_to_file, 'r')
            case ExportTypes.Gzip:
                f = gzip.open(path_to_file, 'rb')
            case _:
                print("Unsupported file type of data")
                return
        json_list = []
        num_docs = 0
        for line in f:
            num_docs += 1
            print(f"Number of Imported Documents : {num_docs}\r", end="")
            json_data = json.loads(line)
            del json_data['_id']
            json_list.append(json_data)
            if len(json_list) == add_by_docs_num:
                collection.insert_many(json_list)
                json_list = []
        if len(json_list) > 0:
            collection.insert_many(json_list)
        f.close()
        print("")
        return

def migrate_props(path2props_dir : str) -> None :
    props_list = [
        'summary',
        # 'entries',
        # 'provenance',
        # 'magnetism',
        # 'electronic_structure',
        # 'dielectric',
        # 'piezo',
        # 'elasticity',
        # 'phonon',
        # 'eos'
        ]
    migrator = Matproj_db_migrator()
    for prop in props_list:
        collection = migrator.db[prop]
        path2file = path2props_dir + prop + '.json'
        migrator.add_data_to_db(path2file,ExportTypes.Json,collection,True)
        print("Added data : " + prop)
    return

def migrate_bundles(path2dir : str, col: Bundle_col = Bundle_col.Bandstructure, bundles_list : list = range(91)) -> None :
    migrator = Matproj_db_migrator()
    collection = migrator.db[col.value]
    for i in bundles_list:
        print('Reading ' + col.value + '_bundle_' + str(i))
        file_name = col.value + "_bundle_0" + str(i) + ".gz" if i < 10 else col.value + "_bundle_" + str(i) + ".gz" 
        path2file = path2dir + file_name
        if i == 0 :
            print("Initializing the collection : " + col.value)
            migrator.add_data_to_db(path2file,ExportTypes.Gzip,collection,True)
        else :
            migrator.add_data_to_db(path2file,ExportTypes.Gzip,collection,False)
        print("Added " + col.value + "_bundel_" + str(i) + " into " + col.value)
    return 

def main() : 
    # migrate several props data
    path2props_dir = 'db_rar/'
    migrate_props(path2props_dir)
    
    # migrate bandstrcture data
    path2bs_dir = 'db_rar/bs_bundle/'
    path2dos_dir = 'db_rar/dos_bundle/'
    path2pdos_dir = 'db_rar/pdos_bundle/'
    #migrate_bundles(path2dir = path2bs_dir, col = Bundle_col.Bandstructure, bundles_list=[0,1])
    #migrate_bundles(path2dir = path2dos_dir, col = Bundle_col.DOS, bundles_list=[0,1])
    migrate_bundles(path2dir = path2pdos_dir, col = Bundle_col.PDOS, bundles_list=[0,1])

if __name__ == "__main__":
    main()