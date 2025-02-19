#!/usr/bin/env python
# coding: utf-8

import logging
import types

import os, fnmatch
import matplotlib.pyplot as plt 
import pandas as pd

import glob
import numpy as np

from random import seed
from random import randint

from tqdm import tqdm_notebook, tnrange
from itertools import chain
from skimage.io import imread, imshow, concatenate_images
from skimage.morphology import label
from sklearn.model_selection import train_test_split
from scipy.stats import poisson

from silence_tensorflow import silence_tensorflow
silence_tensorflow()

import tensorflow as tf

from keras.models import Model, load_model
from keras.layers import Input, BatchNormalization, Activation, Dense, Dropout
from keras.layers.core import Lambda, RepeatVector, Reshape
from keras.layers.convolutional import Conv2D, Conv2DTranspose
from keras.layers.pooling import MaxPooling2D, GlobalMaxPool2D
from keras.layers.merge import concatenate, add
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from keras.optimizers import Adam
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img

import healpy as hp

#####################
#unet model
#####################

def conv2d_block(input_tensor, n_filters, kernel_size = 3, batchnorm = True):
    """Function to add 2 convolutional layers with the parameters passed to it"""
    
    # first layer
    x = Conv2D(filters = n_filters, kernel_size = (kernel_size, kernel_size), \
               kernel_initializer = 'he_normal', padding = 'same')(input_tensor)
    if batchnorm:
        x = BatchNormalization()(x)
    x = Activation('relu')(x)
      
    return x

def get_unet(n_filters = 16, batchnorm = True, im_row=128, im_col=128, im_depth=17, im_output=5):
    """Function to define the UNET Model"""
    # Input
    input_img = Input((im_row, im_col, im_depth))
    
    # Contracting Path
    c1 = conv2d_block(input_img, n_filters * 1, kernel_size = 3, batchnorm = batchnorm)
    c1 = conv2d_block(c1, n_filters * 1, kernel_size = 3, batchnorm = batchnorm)
    
    p1 = MaxPooling2D((2, 2))(c1)
      
    c2 = conv2d_block(p1, n_filters * 2, kernel_size = 3, batchnorm = batchnorm)
    c2 = conv2d_block(c2, n_filters * 2, kernel_size = 3, batchnorm = batchnorm)
    
    p2 = MaxPooling2D((2, 2))(c2)
      
    c3 = conv2d_block(p2, n_filters * 4, kernel_size = 3, batchnorm = batchnorm)
    c3 = conv2d_block(c3, n_filters * 4, kernel_size = 3, batchnorm = batchnorm)
    
    p3 = MaxPooling2D((2, 2))(c3)
      
    c4 = conv2d_block(p3, n_filters * 8, kernel_size = 3, batchnorm = batchnorm)
    c4 = conv2d_block(c4, n_filters * 8, kernel_size = 3, batchnorm = batchnorm)
    
    p4 = MaxPooling2D((2, 2))(c4)
      
    c5 = conv2d_block(p4, n_filters = n_filters * 16, kernel_size = 3, batchnorm = batchnorm)
    c5 = conv2d_block(c5, n_filters = n_filters * 16, kernel_size = 3, batchnorm = batchnorm)
    
    # Expansive Path
    u6 = Conv2DTranspose(n_filters * 8, (3, 3), strides = (2, 2), padding = 'same')(c5)
    u6 = concatenate([u6, c4])
      
    c6 = conv2d_block(u6, n_filters * 8, kernel_size = 3, batchnorm = batchnorm)
    c6 = conv2d_block(c6, n_filters * 8, kernel_size = 3, batchnorm = batchnorm)
    
    u7 = Conv2DTranspose(n_filters * 4, (3, 3), strides = (2, 2), padding = 'same')(c6)
    u7 = concatenate([u7, c3])
      
    c7 = conv2d_block(u7, n_filters * 4, kernel_size = 3, batchnorm = batchnorm)
    c7 = conv2d_block(c7, n_filters * 4, kernel_size = 3, batchnorm = batchnorm)
    
    u8 = Conv2DTranspose(n_filters * 2, (3, 3), strides = (2, 2), padding = 'same')(c7)
    u8 = concatenate([u8, c2])
      
    c8 = conv2d_block(u8, n_filters * 2, kernel_size = 3, batchnorm = batchnorm)
    c8 = conv2d_block(c8, n_filters * 2, kernel_size = 3, batchnorm = batchnorm)
    
    u9 = Conv2DTranspose(n_filters * 1, (3, 3), strides = (2, 2), padding = 'same')(c8)
    u9 = concatenate([u9, c1])
      
    c9 = conv2d_block(u9, n_filters * 1, kernel_size = 3, batchnorm = batchnorm)
    c9 = conv2d_block(c9, n_filters * 1, kernel_size = 3, batchnorm = batchnorm)
    
    outputs = Conv2D(im_output, (1, 1), activation='softmax')(c9)
    model = Model(inputs=[input_img], outputs=[outputs])
    
    return model

def generator_train(patches_list, batch_size):

    number_of_batches = len(patches_list)//batch_size
    np.random.shuffle(patches_list)
    counter=0
    
    while 1:
        
        if counter >= number_of_batches:
            np.random.shuffle(patches_list)
            counter = 0
        
        ini_for = min(batch_size*counter, len(patches_list))
        end_for = min(batch_size*(counter+1), len(patches_list))

        batch_size_local = end_for-ini_for

        if (batch_size_local > 0):
            x_batch = np.zeros((batch_size_local, xsize, xsize, 5), dtype=float)
            y_batch = np.zeros((batch_size_local, xsize, xsize, 2), dtype=float)
        
            for con in range(batch_size_local):

                #image counter starts with ini_for
                index_image = ini_for + con
                image_file = patches_list[index_image]
                masks_file = image_file.replace("image", "masks")

                #read the asimov data image
                x_a = np.load(f'{path_to_data}/{image_file}')  
                y_a = np.load(f'{path_to_data}/{masks_file}')

                #we compute the total patch and then we apply the global factor
                x_a_t = x_a[0,:,:,:] + x_a[1,:,:,:] + x_a[2,:,:,:] 
                             
                #generate the batch elements
                x_batch[con,:,:,:] = x_a_t[:,:,:] 
                y_batch[con,:,:,:] = y_a

            #don't forget to from scipy.stats import poisson
            yield poisson.rvs(x_batch), y_batch

        counter += 1

def generator_valid(patches_list, batch_size):

    number_of_batches = len(patches_list)//batch_size
    np.random.shuffle(patches_list)
    counter=0
    
    while 1:
        
        if counter >= number_of_batches:
            np.random.shuffle(patches_list)
            counter = 0
        
        ini_for = min(batch_size*counter, len(patches_list))
        end_for = min(batch_size*(counter+1), len(patches_list))

        batch_size_local = end_for-ini_for

        if (batch_size_local > 0):
            x_batch = np.zeros((batch_size_local, xsize, xsize, 5), dtype=float)
            y_batch = np.zeros((batch_size_local, xsize, xsize, 2), dtype=float)
        
            for con in range(batch_size_local):

                #image counter starts with ini_for
                index_image = ini_for + con
                image_file = patches_list[index_image]
                masks_file = image_file.replace("image", "masks")

                #read the asimov data image
                x_a = np.load(f'{path_to_data}/{image_file}')  
                y_a = np.load(f'{path_to_data}/{masks_file}')

                #we compute the total patch and then we apply the global factor
                x_a_t = x_a[0,:,:,:] + x_a[1,:,:,:] + x_a[2,:,:,:] 
                            
                #generate the batch elements
                x_batch[con,:,:,:] = x_a_t[:,:,:] 
                y_batch[con,:,:,:] = y_a

            #don't forget to from scipy.stats import poisson
            yield poisson.rvs(x_batch), y_batch

        counter += 1

#####################################################
#main program
#####################################################

epochs=50

xsize = 64
ysize = 64

xdepth = 5
ydepth = 2

batch_size = 128

#let us fix the np random seed
np.random.seed(23)

#patches_localization_training and csv_files folders can be downloaded from zenodo repo
#https://zenodo.org/record/4587205#.YFOjKv7Q9uR

path_to_data = "../patches_localization_training"
path_to_csv = "../csv_files"

#local path to model folder
path_to_model = "../models" 

##########################
#data load, csv lists
##########################
data_train = pd.read_csv(f'{csv_files}/training_localization.csv')
data_valid = pd.read_csv(f'{csv_files}/validation_localization.csv') 

#list of train and valid patches
train_patches_list = data_train["filename"].unique()
valid_patches_list = data_valid["filename"].unique()

#length of patches list
len_train_patches_list = len(train_patches_list)
len_valid_patches_list = len(valid_patches_list)

print("train and valid lengths: ",len_train_patches_list,len_valid_patches_list)

#############################
##### train and validation
#############################

model = get_unet(n_filters=16, batchnorm=True, im_row=ysize, im_col=xsize, im_depth=xdepth, im_output=ydepth)
model.compile(optimizer=Adam(), loss="binary_crossentropy", metrics=["binary_accuracy"])

earlystopper = EarlyStopping(monitor='val_loss', patience=50, verbose=1, min_delta=1e-7)

checkpointer = ModelCheckpoint(f"{path_to_model}/unet_model.h5", \
                               monitor='val_loss', verbose=1, save_best_only=True)

reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, verbose=1, patience=5, min_lr=0.000000001)

model.fit_generator(
    generator_train(train_patches_list, batch_size),
    epochs=epochs,
    steps_per_epoch = len_train_patches_list//batch_size,
    validation_data = generator_valid(valid_patches_list, batch_size*2),
    validation_steps = len_valid_patches_list//batch_size*2,
    verbose=1,
    callbacks=[checkpointer, earlystopper, reduce_lr]
)






