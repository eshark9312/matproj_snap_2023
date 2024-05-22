
This repo contains materials project database on Mongodb, python modules for plotting and self-developed python scripts for local implementation of DB and explorer. 

## How to set up repo on windows machine
- Set up python3.11+
- Set up mongodb
- Set up virtual environment for the repo
    ```
    python -m venv matproj
    ```
- Activate virtual environment by running following psl script
    - In order to run this script you should change ExecutionPolicy by running following command on CMD (one-time action on Windows machine)
        ```
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
        ```
    - After changing ExectionPolicy, you can activate the virtual environment 
        ```
        ./matproj/Scripts/activate
        ```
- Now, you should install required pyton modules
    ```
    pip install --no-index --find-links /path_to_download_wheelhouse_dir -r requirements.txt
    ```
    **/path_to_download_wheelhouse_dir** refers to directory where are all the *.whl files

## Repo contents
```
📁 Project Directory
├── 📁 db_rar
│   ├── 📁 bs_bundle
│   │   ├── 📄 bs_bundle_00.gz
│   │   ├── 📄 ...
│   ├── 📁 dos_bundle
│   │   ├── 📄 dos_bundle_00.gz
│   │   ├── 📄 ...
│   ├── 📁 pdos_bundle
│   │   ├── 📄 pdos_bundle_00.gz
│   │   ├── 📄 ...
│   ├── 📄 01_summary.rar
│   ├── 📄 02_entries.rar
│   ├── 📄 ...
├── 📁 wheelhouse
│   ├── 📄 pymatgen-2024.5.1-cp311-cp311-win_amd64.whl
│   ├── 📄 ... 
│   ├── 📄 requirements.txt
├── 📄 db_migration.py
├── 📄 local_mpr.py
├── 📄 phase_diagram.py
├── 📄 plotter.py
└── 📄 README.md
```

`db_rar` contains *.rar or *.gz files exported from Mongodb, which are required for db_migration

`wheelhose` contains *.whl files required for installing python modules

`db_migration.py` python script for migrating required db files

`local_mpr.py` LocalMP class for exploring local db

`phase_diagram.py` python script for retrieving entries from local db and showing phase diagram

`plotter.py` python script for plotting dos, pdos, bandstructure

## How to run repository
- Start mongodb local service
    ```
    mongod --dbpath localmp
    ```
    You can browse mongodb database / collection / documents with `MongoDB Compass` by connecting 
    ```
    mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false
    ```
- Migrate db
    You should modify `db_migration.py` script to import certain db files and run the following
    ```
    python db_migration.py
    ```
- Plotting Phase Diagram
    - Migrate `summaries`, `entries` collections
    - Add required properties to `entries` collection to get modified one `entries_mod`
    ```
    python local_mpr.py
    ```
    - Now you can query local_db and plot phasediagram
    ```
    python phase_diagram.py
    ```
- Plotting Electronic Structure
    - Migrate `bs_bundles`, `dos_bundles`, `pdos_bundles`
    - Now you can query local_db and plot electronic structures
    ```
    python plotter.py
    ```
