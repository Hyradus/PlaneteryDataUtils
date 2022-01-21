#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Title: 
@author: @author: Giacomo Nodjoumi g.nodjoumi@jacobs-unversity.de



Created on Mon Sep 28 18:45:02 2020
@author: @author: Giacomo Nodjoumi g.nodjoumi@jacobs-unversity.de
"""
import os
os.environ["ISISROOT"]="/opt/conda/envs/isis/"
os.environ["ISISDATA"]="/isis/data"
from kalasiris import lronac2isis, lrowac2isis, lronaccal, lrowaccal, chan1m32isis, cam2map, spiceinit
from osgeo import gdal

def lronac(src, dst_basename, maptemplate):
    dst_lev0 = dst_basename+'_lev0.cub'
    if os.path.isfile(dst_lev0):
        print('init cub exists')
        print(dst_lev0)
    else:
        print('Creating cube')
        print(src, '\n',dst_lev0)
        lronac2isis(src, to=dst_lev0)
    init = None
    while init == None:
        try:
            spiceinit(dst_lev0, web='yes')
            init = 'Done'
        except:
            pass
    dst_lev1 = dst_basename+'_lev1.cub'
    if os.path.isfile(dst_lev1):
        print('dst cal cub exists')
        
    else:
        try:
            print('Calibrating Cube')
            lronaccal(dst_lev0,to=dst_lev1)
        except Exception as e:
            print(e)
    os.remove(dst_lev0)
    try:
        print('Map projecting')
        cub2map(dst_lev1, maptemplate, dst_basename)    
    except Exception as e:
        print(e)
    

def lrowac(src, dst_basename,maptemplate):
    dst_lev0 = dst_basename+'_lev0.cub'
    if os.path.isfile(dst_lev0):
        print('init cub exists')
        print(dst_lev0)
    else:
        print('Creating cube')
        print(src, '\n',dst_lev0)
        lrowac2isis(src, to=dst_lev0)
    init = None
    while init == None:
        try:
            spiceinit(dst_lev0, web='yes')
            init = 'Done'
        except:
            pass
    dst_lev1 = dst_basename+'_lev1.cub'
    if os.path.isfile(dst_lev1):
        print('dst cal cub exists')
        
    else:
        try:
            print('Calibrating Cube')
            lrowaccal(dst_lev0,to=dst_lev1)
        except Exception as e:
            print(e)
    os.remove(dst_lev0)
    try:
        print('Map projecting')
        cub2map(dst_lev1, maptemplate, dst_basename)    
    except Exception as e:
        print(e)

def m3(src, dst_basename,maptemplate):
        src_basename=src.split('_L1B')[0]
        src_L1B=src_basename+'_L1B.LBL'
        src_LOC=src_basename+'_LOC.IMG'
        src_OBS=src_basename+'_OBS.IMG'
        dst_lev0 = dst_basename+'_lev0.cub'
        if os.path.isfile(dst_lev0):
            print('init cub exists')
        else:
            print('Creating cube')
            chan1m32isis(src_L1B, loc=src_LOC, obs=src_OBS, to=dst_lev0)
        init = None
        while init == None:
            try:
                spiceinit(dst_lev0, web='yes')
                init = 'Done'
            except:
                pass
            
        dst_lev2 = dst_lev0.split('.cub')[0]+'_lev2.cub'     
        if os.path.isfile(dst_lev2):
            print('dst lev2 exists')
        else:
            try:
                print('Map projecting')
                dst_lev2 = cub2map(dst_lev0, maptemplate,dst_basename)    
            except Exception as e:
                print(e)
        os.remove(dst_lev0)

def cub2map(dst_lev_x, maptemplate, dst_basename):
        dst_lev2 = dst_basename+'_lev2.cub'      
        if os.path.isfile(dst_lev2):
            print('lev2 cub exists')
            map2jp2(dst_lev2)
            os.remove(dst_lev_x)
            #return(dst_map)
        else:
            print('Projecting cube to map')
            try:
                print('Mapping')
                cam2map(dst_lev_x, to=dst_lev2, map=maptemplate)
                # return(dst_map)
                map2jp2(dst_lev2)
                os.remove(dst_lev_x)
                print('done')
            except Exception as e:
                print(e)
                pass
            

def map2jp2(dst_lev2):
    src_map = gdal.Open(dst_lev2)
    dst_jp2 = dst_lev2.split('.cub')[0]+'.JP2'
    opts = f'-a_nodata none -mask none -scale -ot Byte'
    gdal.Translate(dst_jp2,src_map,options=opts)
    try:
        os.remove(dst_lev2)
    except Exception as e:
        print(e)     

