# PyISIS-parallel


This repository contain a jupyter notebook to use pysis library and process in parallel ISIS3+ commands in a docker container.

*Parallelization*: The notebook use *joblib* as a library for parallelization in which instead of running in parallel the same isis command, e.g. lronac2isis, it execute complete sets of commands. e.g. from lronac2isis to gdal_translate.
This introduce a slightly better performance when processing files with different size and thus different processing time, so all files are processed indipendently.

The work is based on [USGS ISIS](https://github.com/USGS-Astrogeology/ISIS3), [NASA AMES STEREO PIPELINE](https://github.com/NeoGeographyToolkit/StereoPipeline) and their corresponding python packages [KALASIRIS](https://github.com/rbeyer/kalasiris) and [ASAP-STEREO](https://github.com/AndrewAnnex/asap_stereo/).

## Requirements

* Docker
* ISIS-DATA
* Docker image with ISIS - see [HERE](https://github.com/europlanet-gmap/docker-isis3/tree/standalone)

## Usage

* Build *isis5-asp3:jupyter-gispy* from [HERE](https://github.com/europlanet-gmap/docker-isis3/tree/standalone) (Just run ./ImageBuilder.sh) or pull from [dockerhub](https://hub.docker.com/r/hyradus/isis-asp3-gispy)
* Clone this repo into your data folder then using command line:

```
cd your-data-folder
```

```
git clone git@github.com:europlanet-gmap/PyISIS-Parallel.git
```

```
docker run -it --name isis-asp-gispy --rm -e NB_UID=$UID -e NB_GID=$UID -e CHOWN_HOME=yes -e CHOWN_HOME_OPTS='-R' --user root -v $PWD:/home/jovyan/Data -v /mnt/isis-data:/isis/data -p 8888:8888 isis-asp3-gispy:lab
```

**Then open PyISIS-Parallel notebook**

## Processing Notebooks
### Mars

#### **HiRISE_L0toL2_processing.ipynb**

With this notebook is possible to process HiRISE EDR (RAW) CCD to obtain a map projected tiff.

*This notebook performs the same operations of hieder2mosaic.py in a jupyter environment plus the map projection using cam2map*

### Moon
#### **LROC_NAC-WAC_L0toL2_processing_WIP.ipynb**

**Work in progress**

With this notebook is possible to process LROC NAC/WAC and Chandrayaan-1 M3 RAW to obtain a map projected tiff.

This notebook will be replaced by dedicated notebook for each instrument with the same structure of HiRISE notebook.


## Customization of processing

The core processing functions are inside PyISIS-Parallel/utils/KalaUtils.py file. and are imported in the main Notebook after evaluating the config *inst*.

It is possible to:
* customize each instrument functions by adding/removing steps or parameters.
* add new instruments functions in the same file and changing the *inst* evaluation in the main notebook

## References

Beyer, R. A. 2020. Kalasiris, a Python Library for Calling ISIS Programs. 51st Lunar and Planetary Science Conference, not held due to COVID-19, Abstract #2441. [ADS URL](https://ui.adsabs.harvard.edu/abs/2020LPI....51.2441B)

Beyer, Ross A., Oleg Alexandrov, and Scott McMichael. 2018. The Ames Stereo Pipeline: NASA's open source software for deriving and processing terrain data, Earth and Space Science, 5. [https://doi.org/10.1029/2018EA000409](https://doi.org/10.1029/2018EA000409).

Laura, Jason, Acosta, Alex, Addair, Travis, Adoram-Kershner, Lauren, Alexander, James, Alexandrov, Oleg, Alley, Stacey, Anderson, Don, Anderson, James, Anderson, Jeff, Annex, Andrew, Archinal, Brent, Austin, Christopher, Backer, Jeanie, Barrett, Janet, Bauck, Kirsten, Bauers, Joni, Becker, Kris, Becker, Tammy, … Young, Aaron. (2022). Integrated Software for Imagers and Spectrometers (7.1.0). Zenodo. https://doi.org/10.5281/zenodo.7106128

## Funding
*This study is within the Europlanet 2024 RI and EXPLORE project, and it has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 871149 and No 101004214.*
