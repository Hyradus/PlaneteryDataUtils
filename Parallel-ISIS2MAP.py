#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 19:41:33 2021

@author: hyradus
"""

from pysis.isis import lronac2isis, spiceinit, cam2map, lronaccal
import os
from osgeo import gdal
from argparse import ArgumentParser
from tkinter import Tk,filedialog
from utils.GenUtils import make_folder, get_paths, chunk_creator, folder_file_size, question
# import shutil


def cub2map(src):
    dst = src.split('.IMG')[0]+'.cub'
    print('Creating cube')
    lronac2isis(from_=src, to=dst)
    spiceinit(from_=dst, web='yes')
    dst_cal = dst.split('.cub')[0]+'_cal.cub'
    print('Calibrating')
    lronaccal(from_=dst,to=dst_cal)
    map_template = '/media/hyradus/DATA/Syncthing/SyncData/PyS/LROC/Parallel-ISIS2MAP/maptemplate/map_template_moon_eqc.map'
    dst_map = dst_cal.split('.cub')[0]+'_map_5m.cub'
    print('Projectin cube to map')
    cam2map(from_=dst_cal, to=dst_map, map_=map_template)
    
    src_map = gdal.Open(dst_map)
    # format = 'GTiff'
    # driver = gdal.GetDriverByName(format)
    dst_gtiff = dst_map.split('.cub')[0]+'.JP2'
    # isis2std(from_=dst_map, to=dst_gtiff,mode='grayscale',format='TIFF',bittype='8BIT',stretch='linear', minpercent=0.2, maxpercent=99.8)
    opts = f'-a_nodata none -mask none -scale -ot Byte'
    print('Exporting map')
    gdal.Translate(dst_gtiff,src_map,options=opts)
    try:
        os.remove(dst)
    except Exception as e:
        print(e)
    try:
        os.remove(dst_cal)
    except Exception as e:
        print(e)
    try:
        os.remove(src_map)
    except Exception as e:
        print(e)
    
    
def parallel_cub2map(files, JOBS):
    from joblib import Parallel, delayed
    Parallel (n_jobs=JOBS)(delayed(cub2map)(files[i])
                            for i in range(len(files)))
   
def main():
    # PATH = '/mnt/DATS-NFS'
    # ixt = 'img'
    
    
    image_list = get_paths(PATH, ixt) 
    total_size, max_size, av_fsize = folder_file_size(PATH,image_list)

    from tqdm import tqdm
    import psutil
    
    avram=psutil.virtual_memory().total >> 30
    avcores=psutil.cpu_count(logical=False)
    avthreads=psutil.cpu_count(logical=True)
    ram_thread = avram/avthreads
    req_mem = avthreads*max_size
    if req_mem > avcores and req_mem > avram:
        JOBS = avcores
    else:
        JOBS = avcores
    
        
    if ram_thread > 2:
        JOBS=avthreads
    
        
    with tqdm(total=len(image_list),
             desc = 'Generating Images',
             unit='File') as pbar:
        
        filerange = len(image_list)
        chunksize = round(filerange/JOBS)
        if chunksize <1:
            chunksize=1
            JOBS = filerange
        chunks = []
        for c in chunk_creator(image_list, JOBS):
            chunks.append(c)
    
        for i in range(len(chunks)):
            files = chunks[i]
            parallel_cub2map(files, JOBS)
            pbar.update(JOBS)
            

     

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument('--PATH', help='Directory with the files to be cropped as square')
    parser.add_argument('--ixt', help='output file format (tiff,png,jpg')

    args = parser.parse_args()  
    PATH = args.PATH
    ixt = args.ixt
     
    if PATH is None:
        root = Tk()
        root.withdraw()
        PATH = filedialog.askdirectory(parent=root,initialdir=os.getcwd(),title="Please select the folder with the files to be cropped as square")
        print('Working folder:', PATH)
    if ixt is None:
        while ixt not in ['TIFF','tiff','PNG','png','JPG','jpg','JP2','jp2','IMG','img']:
         print('Please enter TIFF or tiff, PNG or png or JPG or jpg')    
         ixt = input('Enter input image format: ')
  
    
    # dst_folder = make_folder(PATH,'processed')
    main()
