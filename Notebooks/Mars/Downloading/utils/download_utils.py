#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: giacomo.nodjoumi@hyranet.info - g.nodjoumi@jacobs-university.de
"""
from bs4 import BeautifulSoup as BS
from gpt import log
from gpt.search import ode
import geoviews as gv
import itertools
import os
import urllib.request as ulr
import pathlib
import psutil
from rasterio.coords import BoundingBox as BB
import requests
import rioxarray as riox
from tqdm import tqdm
from utils.utils import wcs_get

def getFileUrl(df_url, ext):        
    u = ulr.urlopen(df_url)
    page = u.read().decode('utf-8')
    soup = BS(page, 'html.parser')
    FUrl= [node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]
    return(FUrl)

def getFile(url):
    fname = pathlib.Path(url).name
    savename = fname
    v = 0
    while os.path.exists(savename):        
        v = v+1
        savename = str(v) +'_'+fname
        ulr.urlretrieve(url, fname)
    else:
        ulr.urlretrieve(url, savename)
        
def answer(question):
    answ = None
    while answ not in ['yes','y','no','n']:
        print("Please enter yes/y or no/n.")    
        answ = input(question+': ')
    return(answ)        

def orbits2urls(gdf):
    download_urls = []
    download_size = 0
    with tqdm(total=len(gdf),
              desc = 'Creating file urls',
              unit='File') as pbar:
        for url in gdf.FilesURL:                        
            # print(df_url)
            rgram_imgUrl = getFileUrl(url,'rgram.img')
            rgram_lblUrl = getFileUrl(url,'rgram.lbl')
            rgram_tiffUrl = getFileUrl(url,'rgram.tiff')
            track = os.path.basename(rgram_imgUrl[0]).split('_rgram')[0]
            ssim_base_url = 'https://pds-geosciences.wustl.edu/mro/urn-nasa-pds-mro_sharad_simulations/data/'
            ssim_lblUrl = f'{ssim_base_url}/{track[0:6]}xx/{track}/{track}_sim.xml'
            ssim_imgUrl = f'{ssim_base_url}/{track[0:6]}xx/{track}/{track}_sim.img'
            download_urls.append(rgram_imgUrl[0])
            download_urls.append(rgram_lblUrl[0])
            download_urls.append(rgram_tiffUrl)
            download_urls.append(ssim_imgUrl)
            download_urls.append(ssim_lblUrl)
            pbar.update(1)                 
    return(download_urls)


def download(url,ddir):
    name = pathlib.Path(url).name
    filepath = f'{ddir}/{name}'  
    try:
        if os.path.isfile(filepath):
            print('File exists')
        else:        
            ulr.urlretrieve(url, filepath)             
    except Exception as e:
        print(e, url)
        pass        

def is_downloaded(url, filename): #from https://github.com/chbrandt/gpt
    if not os.path.isfile(filename):
        log.debug("File '{}' does not exist.".format(filename))
        return False

    log.debug("File '{}' exist.".format(filename))
    try:
        r = requests.get(url, stream=True)
        remote_size = int(r.headers['Content-Length'])
        local_size = int(os.path.getsize(filename))
    except Exception as err:
        log.error(err)
        return False
    log.debug("Remote file size: " + str(remote_size))
    log.debug("Local file size: " + str(local_size))
    return local_size == remote_size

def download_checker(file_list,ddir):
    todownload_urls = []
    for url in file_list:
        local_name = f'./{ddir}/{os.path.basename(url)}'
        if is_downloaded(url, local_name) ==False:
            todownload_urls.append(url)
    return(todownload_urls)

def user_filter(track_names, file_list):
    filtered=[]
    for uf in track_names:
        for i in file_list:
            if uf in i:
                filtered.append(i)
    return(filtered)


def chunks_generator(item_list, chunksize):
    it = iter(item_list)
    while True:
        chunk = tuple(itertools.islice(it, chunksize))
        if not chunk:
            break
        yield chunk

def chunk_creator(dlist):
    
    JOBS=psutil.cpu_count(logical=False)
    # Create chunks for parallel processing
    filerange = len(dlist)
    chunksize = round(filerange/JOBS)
    if chunksize <1:
        chunksize=1
        JOBS = filerange
    chunks = []
    for c in chunks_generator(dlist, JOBS):
        chunks.append(c)
    return(chunks, JOBS)


def downloader_basemap_prep(wcs_url, layerid, ddir, min_Lon, min_Lat, max_Lon, max_Lat, plot_height,resx,resy):
    #min_Lon = track_gdf.bounds.minx.min()
    #min_Lat = track_gdf.bounds.miny.min()
    #max_Lat = track_gdf.bounds.maxy.max()
    #max_Lon = track_gdf.bounds.maxx.max()
    #gdf_bounding_box = BB(min_Lon, min_Lat, max_Lon, max_Lat)
    bounding_box = [min_Lon, min_Lat, max_Lon, max_Lat]
    bmap_savename = f"{ddir}/{layerid}-_bb_{min_Lon}-{min_Lat}-Min-{max_Lon}-{max_Lat}-Max_basemap.tiff"
    map_error = None
    if not os.path.isfile(bmap_savename):        
        try:                       
            wcs_get(wcs_url, layerid, bounding_box, bmap_savename, resx=resx, resy=resy)
        except Exception as e:
            map_error = e
            bmap_savename = None
            pass        
    ximg = riox.open_rasterio(bmap_savename)
    import math
    src_width =ximg.shape[2]
    src_height=ximg.shape[1]
    #plot_height = 1000a
    plot_width = math.ceil((src_width*plot_height/src_height))
    rgb = gv.RGB(
        (
            ximg['x'],
            ximg['y'],
            ximg.data[0,:,:],
            ximg.data[1,:,:],
            ximg.data[2,:,:]
        ),
        vdims=list('RGB')
    )
    return(bmap_savename, ximg, plot_width, rgb,map_error)


def get_products(bounding_box, Orbiter, Instrument, Data,download_simulations):
    Body = 'Mars'
    #Orbiter = 'MRO'
    #Instrument = 'SHARAD'
    #Data = data_type
    ssim_base_url = 'https://pds-geosciences.wustl.edu/mro/urn-nasa-pds-mro_sharad_simulations/data/'
    results = ode.search(bounding_box, dataset=f'{Body}/{Orbiter}/{Instrument}/{Data}', match='all')
    products = ode.parse_products(results, 
                                      data_selectors={'Type':['product','browse'], 'FileName': ['JPEG$','TIF$','IMG$','DAT$','JP2$']}, 
                                      data_select_how='all')
    gdf = ode.to_geodataframe(products, geometry_field='Footprint_C0_geometry')
    file_list = []
    for prd in products:
        for p in prd['product_files']:
            file_list.append(p['URL'])
        file_list.append(prd['LabelURL'])    
        try:
            file_list.append(prd['product_files'][1]['URL'])
        except:
            pass
        if download_simulations == True:
            track = os.path.basename(prd['product_files'][0]['URL']).split('_rgram')[0]            
            file_list.append(f'{ssim_base_url}/{track[0:6]}xx/{track}/{track}_sim.xml')
            file_list.append(f'{ssim_base_url}/{track[0:6]}xx/{track}/{track}_sim.img')
    return(file_list, gdf)

def geom_splitter(track_gdf):
    geoms = []
    for geom in track_gdf.geometry:
        try:
            for g in geom.geoms:
                geoms.append(g)            

        except:
            geoms.append(geom)
    tracks_geom=[]
    for geom in geoms:
        try:
            tracks_geom.append(gv.Shape(geom))
        except Exception as e:
            print(e)        
    #tracks_num = len(tracks_geom)
    return(tracks_geom)
    
    
