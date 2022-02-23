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
from kalasiris import lronac2isis, lrowac2isis, lronaccal, lrowaccal, chan1m32isis, cam2map, spiceinit, lronacecho
from osgeo import gdal
from osgeo.gdal import gdalconst
import rasterio as rio
import time

def RAWtoL0(inst, src, L0):
    inst(src, to=L0)
    

def L0toL1(dst_basename, L0, L1):
    lronaccal(L0,to=L1)
    os.remove(L0)

def L1toL1echo(L1,L1echo):
    lronacecho(L1, to=L1echo)
    os.remove(L1)
    
def L1toL2(maptemplate, L1, L2):
    #res=GetRes(maptemplate)
    cam2map(L1, to=L2, PIXRES='MAP', map=maptemplate)
    os.remove(L1)

    
def L2toStd(L2cub, L2std):
    try:
        src_map = gdal.Open(L2cub)
        nodata=rio.open(L2cub).nodata #using rio since src_map.GetMetadata() return empty
        nodata=0
        opts = f'-a_nodata {nodata} -mask none -scale -ot Byte'
#        gdal.Translate(L2std, src_map,options=opts)
        otype=gdalconst.GDT_Byte
        gdal.Translate(L2std, src_map, options=opts)#,scaleParams=[])
        return 'Done'
        #os.remove(dst_lev2)
    except Exception as e:
        return(e)     




def lro(src, dst_basename, maptemplate, oxt, cam):
    L2std = dst_basename+'_lev2.'+oxt
    L2 = dst_basename+'_lev2.cub'
    L1echo = dst_basename+'_lev1echo.cub'
    L1 = dst_basename+'_lev1.cub'                
    L0 = dst_basename+'_lev0.cub'    
    if os.path.isfile(L2std):
        print('File exists')
    else:
        L2 = L2std.split(oxt)[0]+'cub'
        if os.path.isfile(L2):
            L2toStd(L2, L2std)
        else:
            
            if os.path.isfile(L1echo):
                
                L1toL2(maptemplate, L1echo, L2)
                e=L2toStd(L2, L2std)
            else:
                
                if os.path.isfile(L1):
                    if cam in ['nac']:
                        L1toL1echo(L1, L1echo)
                        L1toL2(maptemplate, L1echo, L2)
                    else:
                        L1toL2(maptemplate, L1, L2)
                    e=L2toStd(L2, L2std)
                else:                        
                    
                    if os.path.isfile(L0):
                        L0toL1(dst_basename, L0, L1)
                        if cam in ['nac']:
                            L1toL1echo(L1, L1echo)
                            L1toL2(maptemplate, L1echo, L2)
                        else:
                            L1toL2(maptemplate, L1, L2)                                                
                        e=L2toStd(L2, L2std)
                    else:
                        RAWtoL0(lronac2isis, src, L0)
                        init = None
                        while init == None:
                            try:
                                print('Spiceinit')
                                spiceinit(L0)#, web='yes')
                                init = 'Done'
                                print(init)
                            except subprocess.CalledProcessError as err:
                                print('Had an ISIS error:')
                                print(' '.join(err.cmd))
                                print(err.stdout)
                                print(err.stderr)
                                raise err
                                
                        L0toL1(dst_basename, L0, L1)
                        if cam in ['nac']:
                            L1toL1echo(L1, L1echo)
                            L1toL2(maptemplate, L1echo, L2)
                        else:
                            L1toL2(maptemplate, L1, L2)                                                
                        L2toStd(L2, L2std)
                        e=L2toStd(L2, L2std)
        return e
                        



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
        if os.path.isfile(dst_lev2.split('.cub')[0]+'.JP2'):
            print('JP2 exists')
        else:
            map2jp2(dst_lev2)
            #os.remove(dst_lev_x)
        #os.remove(dst_lev0)

        
        
def equalizer(L2list):
    L2equ = [cub.split('.cub')[0]+'_equ.cub' for cub in L2list]
    isis.equalizer(L2list, to=L2equ)
    return(L2equ)


def GetRes(maptemplate):
    line=check_if_string_in_file(maptemplate,'PixelResolution')
    for val in line.split(' '):
        try:
            float(val)
            return(float(val))
            break
        except:        
            continue
            
            
def check_if_string_in_file(file_name, string_to_search):
    ### source https://thispointer.com/python-search-strings-in-a-file-and-get-line-numbers-of-lines-containing-the-string/
    """ Check if any line in the file contains given string """
    # Open the file in read only mode
    with open(file_name, 'r') as read_obj:
        # Read all lines in the file one by one
        for line in read_obj:
            # For each line, check if line contains the string
            if string_to_search in line:
                return line
    return False            