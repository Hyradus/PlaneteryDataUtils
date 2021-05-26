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
    
    src_basename = os.path.basename(src).split('.IMG')[0]
    dst_basename = DPATH+'/'+src_basename
    dst_basefpath = DPATH+'/'+src_basename
    print(dst_basename)
    if os.path.isfile(dst_basename+'_cal_map.JP2'):
        print ("File exist")
    elif os.path.isfile(dst_basename+'.JP2'):
        print ("File exist")
    else:
        dst = dst_basefpath+'.cub'
        # print('Creating cube')
        lronac2isis(from_=src, to=dst)
        init = None
        while init == None:
            try:
                spiceinit(from_=dst, web='yes')
                init = 'Done'
            except:
                pass
        dst_cal = dst_basefpath+'_cal.cub'
        # print('Calibrating Cube')
        lronaccal(from_=dst,to=dst_cal)
        map_template = './maptemplate/map_template_moon_eqc.map'
        dst_map = dst_cal.split('.cub')[0]+'_map.cub'
        # print('Projectin cube to map')
        try:
            cam2map(from_=dst_cal, to=dst_map, map_=map_template)
            
            src_map = gdal.Open(dst_map)
            # format = 'GTiff'
            # driver = gdal.GetDriverByName(format)
            dst_jp2 = dst_basefpath+'.JP2'
            # isis2std(from_=dst_map, to=dst_gtiff,mode='grayscale',format='TIFF',bittype='8BIT',stretch='linear', minpercent=0.2, maxpercent=99.8)
            opts = f'-a_nodata none -mask none -scale -ot Byte'
            # print('Exporting map')
            gdal.Translate(dst_jp2,src_map,options=opts)
            try:
                os.remove(dst)
            except Exception as e:
                print(e)
            try:
                os.remove(dst_cal)
            except Exception as e:
                print(e)
            try:
                os.remove(dst_map)
            except Exception as e:
                print(e)
        except Exception as e:
            print(src_basename, e)
            pass
    
    
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
    
        
    # if ram_thread > 2:
    #     JOBS=avthreads
    
        
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
        # from time import time
        from datetime import datetime
        for i in range(len(chunks)):
            start = datetime.now()
            dt_string = start.strftime("%d/%m/%Y %H:%M:%S")
            print(f'Loop {i} started at: {dt_string}', chunks[i])
            files = chunks[i]
            parallel_cub2map(files, JOBS)
            pbar.update(JOBS)
            # print(time()-start)
            

     

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument('--PATH', help='Directory with the files to be processed')
    parser.add_argument('--DPATH', help='Destination directory')
    parser.add_argument('--ixt', help='output file format (IMG')

    args = parser.parse_args()  
    PATH = args.PATH
    DPATH = args.PATH
    ixt = args.ixt
     
    if PATH is None:
        root = Tk()
        root.withdraw()
        PATH = filedialog.askdirectory(parent=root,initialdir=os.getcwd(),title="Please select the folder with the files to be processed")
        print('Working folder:', PATH)
    if DPATH is None:
        root = Tk()
        root.withdraw()
        DPATH = filedialog.askdirectory(parent=root,initialdir=os.getcwd(),title="Please select the destination folder")
        print('Working folder:', DPATH)
    if ixt is None:
        while ixt not in ['IMG','img']:
         print('Please enter IMG or img')    
         ixt = input('Enter input image format: ')
  
    
    # dst_folder = make_folder(PATH,'processed')
    main()


