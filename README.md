# PyISIS-parallel

This repository contain a jupyter notebook to use pysis library and process in parallel ISIS3+ commands in a docker container.

*Parallelization*: The notebook use *joblib* as a library for parallelization in which instead of running in parallel the same isis command, e.g. lronac2isis, it execute complete sets of commands. e.g. from lronac2isis to gdal_translate.
This introduce a slightly better performance when processing files with different size and thus different processing time, so all files are processed indipendently.


## Requirements

* Docker
* Docker image with ISIS - see [HERE](https://github.com/europlanet-gmap/docker-isis3/tree/master)
* ISIS-DATA

## Usage

Clone this repo and then with a valid with the above docker images available running

```
docker build -t isis-gdal --build-arg BASE_IMAGE=osgeo/gdal --build-arg ISIS_VERSION="5" -f Dockerfile .
```

Then run:

```
docker build -t pysis --build-arg BASE_IMAGE="isis-gdal" -f ParISIS.Dockerfile .
```

And finally:

```
docker run -it --rm --name pysis -v path-to-ISIS_DATA:/isis/data -v path-to-data-to-process:/mnt/data -p 8888:8888 pysis:latest
```

Upon launch jupyter is not automatically run, to grant the possibility to run isis commands indipendently.
To start the jupyter lab run:

```
./PyISIS-Parallel/jupyter.sh
```

## Processing commands

Default isis commands are set for processing LROC-NAC EDR from IMG to JP2

Edit the function to custom processing steps.

To change maptemplate, add to the soruce folder and rebuild the image or mount to docker image upon start, or to data-folder and change the internal path in the notebook
