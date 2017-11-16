import os
import time
import random
import threading
import sys, time
from socket import *
import pickle
import numpy as np
import cv2
from primesense import openni2#, nite2
from primesense import _openni2 as c_api

ser_run = True
BUFSIZE = 10000
hostAddr = "192.168.137.250"
PORT = 5000


## Path of the OpenNI redistribution OpenNI2.so or OpenNI2.dll
# Windows
#dist = 'C:\Program Files\OpenNI-Windows-x86-2.3\Samples\Bin'
# OMAP
#dist = '/home/carlos/Install/kinect/OpenNI2-Linux-ARM-2.2/Redist/'
# Linux
dist ='/OpenNI-Linux-x86-2.3/Redist'

openni2.initialize(dist)
if (openni2.is_initialized()):
    print ("openNI2 initialized")
else:
    print ("openNI2 not initialized")

## Register the device
dev = openni2.Device.open_any()
## create the streams stream
rgb_stream = dev.create_color_stream()
depth_stream = dev.create_depth_stream()
##configure the depth_stream
#print 'Get b4 video mode', depth_stream.get_video_mode()
depth_stream.set_video_mode(c_api.OniVideoMode(pixelFormat=c_api.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM, resolutionX=640, resolutionY=480, fps=30))
## Check and configure the mirroring -- default is True
# print 'Mirroring info1', depth_stream.get_mirroring_enabled()
depth_stream.set_mirroring_enabled(False)
rgb_stream.set_mirroring_enabled(False)
## start the stream
rgb_stream.start()
depth_stream.start()
## synchronize the streams
dev.set_depth_color_sync_enabled(True) # synchronize the streams
## IMPORTANT: ALIGN DEPTH2RGB (depth wrapped to match rgb stream)
dev.set_image_registration_mode(openni2.IMAGE_REGISTRATION_DEPTH_TO_COLOR)

def get_rgb():
    """
    Returns numpy 3L ndarray to represent the rgb image.
    """
    bgr   = np.fromstring(rgb_stream.read_frame().get_buffer_as_uint8(),dtype=np.uint8).reshape(480,640,3)
    rgb   = cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
    return rgb

def get_depth():
    """
    Returns numpy ndarrays representing the raw and ranged depth images.
    Outputs:
        dmap:= distancemap in mm, 1L ndarray, dtype=uint16, min=0, max=2**12-1
        d4d := depth for dislay, 3L ndarray, dtype=uint8, min=0, max=255    
    Note1: 
        fromstring is faster than asarray or frombuffer
    Note2:     
        .reshape(120,160) #smaller image for faster response 
                OMAP/ARM default video configuration
        .reshape(240,320) # Used to MATCH RGB Image (OMAP/ARM)
                Requires .set_video_mode
    """
    dmap = np.fromstring(depth_stream.read_frame().get_buffer_as_uint16(),dtype=np.uint16).reshape(480,640)  # Works & It's FAST
    d4d = np.uint8(dmap.astype(float) *255/ 2**12-1) # Correct the range. Depth images are 12bits
    d4d = 255 - cv2.cvtColor(d4d,cv2.COLOR_GRAY2RGB)
    return dmap, d4d

def mask_rgbd(d4d,rgb, th=0):
    """
    Overlays images and uses some blur to slightly smooth the mask
    (3L ndarray, 3L ndarray) -> 3L ndarray
    th:= threshold
    """
    mask = d4d.copy()
    idx =(mask>th)
    mask[idx] = rgb[idx]
    return mask
#mask_rgbd

def cli_send(arr1):
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((hostAddr, PORT))
        #send the size of the array
        s.send()
        #send the combined version of the array (for rgbd)



        s.close()

def send(arr):
        thread = threading.Thread(target=cli_send,args=[arr])
        thread.start()


s = 0
done = False
while not done:
    key = cv2.waitKey(1) & 255
    ## Read keystrokes
    if key == 27:  # terminate
        print("\tESC key detected!")
        done = True
    elif chr(key) == 's':  # screen capture
        print("\ts key detected. Saving image and distance map {}".format(s))
        #cv2.imwrite("ex5_" + str(s) + '.png', canvas)
        np.savetxt("ex5dmap_" + str(s) + '.out', dmap)
        # s+=1 # uncomment for multiple captures
    # if

    ## Streams
    # RGB
    rgb = get_rgb()

    # DEPTH
    dmap, d4d = get_depth()
    # Overlay rgb over the depth stream
    rgbd = mask_rgbd(d4d, rgb)
    send(rgbd)
    # canvas
    #canvas = np.hstack((d4d, rgb, rgbd))

    ## Distance map
   # print('Center pixel is {} mm away'.format(dmap[119, 159]))

    ## Display the stream
    #cv2.imshow('depth || rgb || rgbd', canvas)
# end while

## Release resources
cv2.destroyAllWindows()
rgb_stream.stop()
depth_stream.stop()
openni2.unload()
print("Terminated")