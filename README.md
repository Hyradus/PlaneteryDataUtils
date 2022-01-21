# PyISIS-parallel


This repository contain a jupyter notebook to use pysis library and process in parallel ISIS3+ commands in a docker container.

*Parallelization*: The notebook use *joblib* as a library for parallelization in which instead of running in parallel the same isis command, e.g. lronac2isis, it execute complete sets of commands. e.g. from lronac2isis to gdal_translate.
This introduce a slightly better performance when processing files with different size and thus different processing time, so all files are processed indipendently.

**Major change: from Pysis to Kalasiris**

## Requirements

* Docker
* ISIS-DATA
* Docker image with ISIS - see [HERE](https://github.com/europlanet-gmap/docker-isis3/tree/hyradus)

## Usage
* Build *isis5-asp3:jupyter-gispy* from [HERE](https://github.com/europlanet-gmap/docker-isis3/tree/hyradus) (Just run ./ImageBuilder.sh)
* Clone this repo and then mount as external data to /home/jovyan/work/data e.g.

```
docker run -it --rm --name python-isis -v path-to-isis-data/:/isis/data -v path-to-user-data/:/home/jovyan/work/data -v path-to-pyisis-git-folder:/home/jovyan/work/PyISIS-Parallel -p 8888:8888 isis5-asp3:jupyter-gispy
```

Then open PyISIS-Parallel notebook
## Processing commands

Edit config by using the following as *inst* :
```
* **lronac** for Lunar Reconnaissance Orbiter Narrow Angle Camera
* **lrowac for** Lumar Reconnaissance Orbiter Wide Angle Camera
* **m3** for Chandraayan1 - Moon Mineralogy Mapper
```

optionally change *maptemplate* path if using custom maptemplate file

*the maptemplate file should be copied inside maptemplate folder located inside the cloned git folder*

## Customization of processing

The core processing functions are inside PyISIS-Parallel/utils/KalaUtils.py file. and are imported in the main Notebook after evaluating the config *inst*.

It is possible to:
* customize each instrument functions by adding/removing steps or parameters.
* add new instruments functions in the same file and changing the *inst* evaluation in the main notebook
