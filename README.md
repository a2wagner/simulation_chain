Simulation Chain
================

These are the scripts which I use to simulate events. Further programs used are the Pluto event generator and the Geant4 simulation code from the A2.

The scripts will run interactive, the only thing is to adapt the paths where the data should be stored as well as where the a2geant package is located and start everything via `./run.py`.

New channels can be added very easy using the same nomenclature for the decays as found in the scripts. By simply commenting the lines belonging to certain channels at the beginning of the `run.py` their terminal prompt will be skipped.


Prerequisites
-------------

The following programs have to be installed and set up properly:

- [ROOT framework](http://root.cern.ch/ "ROOT")
- [Pluto event generator](http://www-hades.gsi.de/?q=pluto "Pluto")
- For the detector simulation:
	- [Geant4](http://geant4.cern.ch/ "Geant4")
	- [A2 Geant4 package](https://github.com/A2-Collaboration/a2geant "A2 package")

In order to run the detector simulation with Geant4, the file `vis.mac` has to be placed in the macros folder where the A2 Geant4 package had been installed.

Converting the files generated with Pluto to use them within Geant4, the pluto2mkin converter, written by Dominik Werthmüller, is needed. It should be located in the A2 Geant directory.


###Path changes in the scripts

Some paths must be changed according to the output directories where the data should be stored as well as where the A2 Geant package is located. In the beginning of the file `run.py` there are all paths in capital letters marked which has to be changed in order to run the automated simulation chain.

Besides this Python script the Geant4 macro `vis.mac` inside the macros folder of the A2 package must be replaced by the one from this repository. In the file `vis.mac` the only not commented line `/control/execute macros/g4run_multi.mac` should work without changing anything when the a2geant package is installed without modifications.

By default the Pluto generated data will be stored in the directory sim_data and the detector simulated data will be stored in g4_sim. The folder g4run contains the per channel information for the particles to be tracked within Geant4. The tracking information can easily be accessed by running the `pluto2mkin` converter which displays the needed information.

