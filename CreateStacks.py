# -*- coding: utf-8 -*-
"""
Created on Thu Jun 10 17:47:03 2021

@author: Jean
"""

#pip install glob tifffile streamlit tkinter PIL exifread os

import glob
import tifffile
import streamlit as st
import tkinter as tk
from tkinter import filedialog
from PIL import Image
import exifread
import os
from PIL import Image
import shutil


class WL:
    def __init__(self,name,step=1):
        self.name=name
        self.step=step

class Exp:
    def __init__(self,expname,wl=[],nbpos=1,nbtime=1):
        self.name=expname
        self.nbpos=nbpos
        self.nbtime=nbtime
        self.wl=wl
        self.nbwl=len(wl)
        self.timestep=0
    
    def get_image_name(self,wl_ind,pos=1,timepoint=1):
        if self.nbtime==1 or timepoint==-1:
            tpstring=''
        else:
            tpstring='_t'+str(timepoint)
        if self.nbpos==1:
            posstring=''
        else:
            posstring='_s'+str(pos)
        return self.name+'_w'+str(wl_ind+1)+self.wl[wl_ind].name+posstring+tpstring+'.tif'
    
    def get_first_image(self,wl_ind,pos=1,timepoint=''):
        timepoint=1
        return Image.open(self.get_image_name(wl_ind,pos,timepoint))
    
    def get_last_image(self,wl_ind,pos=1,timepoint=1):
        last_ind=int(self.nbtime/self.wl[wl_ind].step-1)*self.wl[wl_ind].step+1
        return Image.open(self.get_image_name(wl_ind,pos,last_ind))
    
    def get_sizeimg(self):
        return self.get_first_image(0).size

def get_exp(filename):
    nb_pos=1
    nb_wl=1
    with open(filename,'r') as file:
        i=0
        line=file.readline()
        comments=[]
        iscomments=False
        while not line.rstrip().split(', ')[0]=='"NTimePoints"' and i<50:
            if line.rstrip().split(', ')[0]=='"StartTime1"':
                iscomments=False
            if iscomments:
                comments.append(line.rstrip())
            if line.rstrip().split(', ')[0]=='"Description"':
                iscomments=True
                comments.append(str(line.rstrip().split(', ')[1]))
            line=file.readline()
            i+=1
        #get number of timepoints
        nb_tp=int(line.rstrip().split(', ')[1])
        line=file.readline()
        
        #get positions if exist
        if line.split(', ')[1].rstrip('\n')=='TRUE':
            line=file.readline()
            nb_pos=int(line.split(', ')[1].rstrip('\n'))
            for i in range(nb_pos):
                file.readline()            
        file.readline()
        
        #get number of wavelengths
        line=file.readline()
        nb_wl=int(line.rstrip().split(', ')[1])
    
        #create all new wavelengths
        wl=[]
        for i in range (nb_wl):
            line=file.readline()
            wl.append(WL(line.rstrip().split(', ')[1].strip('\"')))
            file.readline()
    
        #change the time steps
        line=file.readline()
        while line.split(', ')[0].strip('\"')=='WavePointsCollected':
            sep=line.rstrip().split(', ')
            if len(sep)>3:
                wl[int(sep[1])-1].step=int(sep[3])-int(sep[2])
            line=file.readline()
        
        expname=filename.rstrip('d').rstrip('n').rstrip('.')
        
        return Exp(expname,wl,nb_pos,nb_tp)

def file_selector(folder_path='.',extension='.nd'):
    filenames = [f for f in os.listdir(folder_path) if f.endswith(extension)]
    return filenames   

# Folder picker button
root = tk.Tk()
root.withdraw()
root.wm_attributes('-topmost', 1)
clicked = st.button('Please select a folder:')

if clicked:
    file_dir = st.text_input('Selected folder:', filedialog.askdirectory(master=root))
    filenames=file_selector(file_dir)
    os.mkdir(file_dir+'/Stacks')
    for filename in filenames:
        st.write(file_dir+'/'+filename)
        try:
            exp=get_exp(file_dir+'/'+filename)
            doit=True
        except:
            doit=0
            st.write("Error in this experiment")
        if doit:
            st.write('Number of time points: '+str(exp.nbtime))
            st.write('Number of wavelengths: '+str(exp.wl))
            if len(exp.wl)>0 and exp.nbtime>1:
                for i,wl in enumerate(exp.wl):
                    for pos in range(1,exp.nbpos+1):
                        try:
                            with tifffile.TiffWriter(exp.get_image_name(i,pos=pos,timepoint=-1)) as stack:
                                #st.write(exp.get_image_name(i,pos=pos,timepoint='*').replace('\\','/').replace(exp.get_image_name(i,pos=pos,timepoint=-1).split('.')[0],'').replace("_t","").replace('.tif',''))
                                list_file=glob.glob(exp.get_image_name(i,pos=pos,timepoint='*'))
                                #st.write(list_file)
                                #st.write(sorted(list_file,key=lambda x:int(x.replace('\\','/').replace(exp.get_image_name(i,pos=pos,timepoint=-1).split('.')[0],'').replace("_t","").replace('.TIF',''))))
                                for file in sorted(list_file,key=lambda x:int(x.replace('\\','/').replace(exp.get_image_name(i,pos=pos,timepoint=-1).split('.')[0],'').replace("_t","").replace('.TIF',''))):
                                    #save and keep metamorph metadata in each iamge of the stack
                                    #st.write(file)
                                    with Image.open(file) as opened:
                                        metamorph_metadata=[key for key in opened.tag_v2]
                                        #st.write(metamorph_metadata)
                                        stack.save(
                                            tifffile.imread(file), 
                                            photometric='minisblack', 
                                            contiguous=True,
                                            description=str(metamorph_metadata)
                                        )

                        except:
                            st.write('error doing stack')
                        try:
                            shutil.move(exp.get_image_name(i,pos=pos,timepoint=-1),file_dir+'/Stacks')
                        except:
                            'problem moving files'
            st.write('Done')
            

