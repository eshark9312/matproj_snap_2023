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

    def _read_json_data_from_file(self, fp : Union[BinaryIO, TextIO]) -> list:
        json_list = []
        json_lines = fp.readlines()
        for line in json_lines:
            json_data = json.loads(line)
            del json_data['_id']
            json_list.append(json_data)
        return json_list

    def add_data_to_db(self,
            path_to_file : str,
            dataType : ExportTypes,
            collection : Collection,
            from_scratch : bool = False
    ) -> None:
        """
            This function reads data from file and add those into db
        """
        if from_scratch:
            collection.drop()
        match dataType:
            case ExportTypes.Json:
                with open(path_to_file, 'r') as f:
                    json_data = self._read_json_data_from_file(f)
                    collection.insert_many(json_data)
            case ExportTypes.Gzip:
                with gzip.open(path_to_file, 'rb') as f:
                    json_data = self._read_json_data_from_file(f)
                    collection.insert_many(json_data)
            case _:
                print("Unsupported file type of data")
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
    #migrate_props(path2props_dir)
    
    # migrate bandstrcture data
    path2bs_dir = 'db_rar/bs_bundle/'
    path2dos_dir = 'db_rar/dos_bundle/'
    path2pdos_dir = 'db_rar/pdos_bundle/'
    #migrate_bundles(path2dir = path2bs_dir, col = Bundle_col.Bandstructure, bundles_list=[0,1])
    #migrate_bundles(path2dir = path2dos_dir, col = Bundle_col.DOS, bundles_list=[0,1])
    migrate_bundles(path2dir = path2pdos_dir, col = Bundle_col.PDOSN, bundles_list=[0,1])

    #migrate_props(path2props_dir=path2props_dir)

if __name__ == "__main__":
    main()