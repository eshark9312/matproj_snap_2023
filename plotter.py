from pymatgen.electronic_structure.bandstructure import BandStructureSymmLine
from pymatgen.electronic_structure.dos import CompleteDos, Dos
from pymatgen.electronic_structure.plotter import  BSPlotter, DosPlotter
from pymatgen.core.periodic_table import Element
from pymatgen.electronic_structure.core import OrbitalType

import pymongo
client = pymongo.MongoClient()
db = client.matproj

def bs_dict_plotter(bs_dict : dict) -> BSPlotter :
    bs_obj = BandStructureSymmLine.from_dict(bs_dict)
    return BSPlotter(bs_obj)

def get_cdos_obj_from_dos_doc(dos_doc : dict) -> CompleteDos :
    dos_dict = dos_doc['dos']
    dos_dict['pdos'] = _get_pdos_from_material_id(dos_doc['material_id'])
    return CompleteDos.from_dict(dos_dict)

def _get_pdos_from_material_id(mp_id : str) -> list :
    pdos_col = db['pdos']
    query = {"material_id" : mp_id}
    pdos_result = pdos_col.find(query).sort('site_index',1)
    pdos_list = []
    for pdos in pdos_result:
        pdos_list.append(pdos['pdos'])
    return pdos_list

def add_element_spd_dos(dos_plotter : DosPlotter, cdos_obj:CompleteDos) -> None :
    element_dos = cdos_obj.get_element_dos()
    for element in element_dos:
        element_spd_dos = cdos_obj.get_element_spd_dos(element)
        for orbital_type in element_spd_dos:
            pdos_label = str(element) + '(' + str(orbital_type) + ')' 
            dos_plotter.add_dos(pdos_label, element_spd_dos[orbital_type])
    return 

def add_specific_orbital_dos(dos_plotter: DosPlotter, 
                             cdos_obj: CompleteDos, 
                             element: Element,
                             orbital_type: OrbitalType) -> None :
    element_spd_dos = cdos_obj.get_element_spd_dos(element)
    pdos_label = str(element) + '(' + str(orbital_type) + ')'
    dos_plotter.add_dos(pdos_label, element_spd_dos[orbital_type])
    return

def test_bs_plotter() -> None:
    bs_col = db['bandstructure']
    query = {"bandstructure.is_spin_polarized":True} # query for spin_polarized bs
    projection = {"material_id":1, "bandstructure":1, "_id":0}
    bs = bs_col.find_one(query,projection)
    bs_dict = bs['bandstructure']
    print(bs['material_id'])
    bs_plotter = bs_dict_plotter(bs_dict)
    bs_plotter.show()
    return 

def test_dos_plotter() -> None:
    dos_col = db['dos']
    query = {"material_id":"mp-10004"}
    projection = {"material_id":1, "dos":1, "_id":0}
    dos_doc = dos_col.find_one(query,projection)
    cdos_obj = get_cdos_obj_from_dos_doc(dos_doc)
    dos_plotter = DosPlotter()
    # adding TDOS
    dos_plotter.add_dos('TDOS', cdos_obj)
    ## adding Elemental PDOS
    dos_plotter.add_dos_dict(cdos_obj.get_element_dos())
    ## adding Elemental_spd PDOS
    # add_element_spd_dos(dos_plotter, cdos_obj)
    ## adding Specifi Elemental Orbital PDOS
    add_specific_orbital_dos(dos_plotter, cdos_obj, Element.Mo, OrbitalType.s)
    add_specific_orbital_dos(dos_plotter, cdos_obj, Element.Mo, OrbitalType.p)
    add_specific_orbital_dos(dos_plotter, cdos_obj, Element.Mo, OrbitalType.d)
    dos_plotter.show([-7,7],[0,30])
    return

def main() -> None :
    test_bs_plotter()
    # test_dos_plotter()
    return 

if __name__ == "__main__":
    main()