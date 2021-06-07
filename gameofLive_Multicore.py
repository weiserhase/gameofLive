import random as r 
from PIL import Image
import numpy as np
import time
import cv2
import os
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from scipy.spatial import Delaunay
from functools import partial
import multiprocessing

def selectOptions(options): #'''selectOptions''' 
    maxlen = 0
    col = len(options) //10

    for option in options:
        if(maxlen < len(option)):
            maxlen = len(option)
    prettyPrefix = ''
    
    for i in range(maxlen+8):
        prettyPrefix +='#'
    print(prettyPrefix)
    for i in range(len(options)):
        text = str(options[i])
        if(i<9):
            pad = ' '
            tmp = maxlen+1
        else:
            pad = ''
            tmp = maxlen
        print('# '+str(pad)+str(i+1)+': '+text.ljust(tmp)+'#')
    print(prettyPrefix)
    print('type the number to select; press c to cancel')
    inp = input('select: ')
    if(inp != 'c'):
        try:
            return str(int(inp)-1)
        except Exception as e:
            print(e)
            return False
    else:
        return False

def loadImage():
    path = str(os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"))
    for root, dirs,files in os.walk(path+'/images/'):
        option = selectOptions(files)
    # filename = input('filename:')
    #filename = 'expanding1'
    filename = files[int(option)]
    return np.array(Image.open(path + '/images/{}'.format(filename)))

def mapMatrix(arr, executor, depth = 0):
    if(depth): 
        newArr = np.zeros((arr.shape[0], arr.shape[0], depth), dtype=np.uint8)
    else:
        newArr = np.zeros((arr.shape[0], arr.shape[0]), dtype=np.uint8)

    for x in range(arr.shape[0]):
        for y in range(arr.shape[1]):
            newArr[x, y] = executor(arr[x, y], x, y)

    return newArr

def iterateMatrix(arr, executor):
    for x in range(arr.shape[0]):
        for y in range(arr.shape[1]):
            executor(arr[x, y], x, y)

def mergeMatricies(largeMatrix, smallMatrix):
    offsetX = (largeMatrix.shape[0] - smallMatrix.shape[0]) // 2
    offsetY = (largeMatrix.shape[1] - smallMatrix.shape[1]) // 2

    for x in range(smallMatrix.shape[0]):
        for y in range(smallMatrix.shape[1]):
            largeMatrix[x + offsetX, y + offsetY] = smallMatrix[x, y]

def binaryToPixel(binary, _, __):
    if(binary): return [255, 255, 255]

    return [0, 0, 0]

def pixelToBinary(color, _, __):
    if(color[0] == 255): return 1

    return 0

def render():
    pixelMap = mapMatrix(aliveMap, binaryToPixel, 3)
    cv2.imshow('output', pixelMap)
    cv2.waitKey(1)

def updateSurroundingPixels(writeMatrix, x, y, executor):
    offsets = [-1, 0, 1]
    for dx in range(3):
        for dy in range(3):
            if dx == 1 and dy == 1: continue

            try:
                newX = x+offsets[dx]
                newY = y+offsets[dy]

                writeMatrix[newX, newY] = executor(writeMatrix[newX, newY])

            except:
                pass
            
def countSurroundingAlive(aliveMap, _, x, y):
    counter = 0

    offsets = [-1, 0, 1]
    for dx in range(3):
        for dy in range(3):
            if dx == 1 and dy == 1: continue

            try:
                newX = x+offsets[dx]
                newY = y+offsets[dy]

                if(aliveMap[newX, newY]): counter+=1

            except:
                pass

    return counter

def evolvePixel(newAliveMap, newAliveCounterMap, isAlive, x, y):
    aliveCounter = aliveCounterMap[x, y]

    if(isAlive):
        if(aliveCounter < 2 or aliveCounter > 3):
            # cell dies
            updateSurroundingPixels(newAliveCounterMap, x, y, lambda oldCounter: oldCounter-1)
            newAliveMap[x, y] = 0

    elif aliveCounter == 3:
        # cell becomes alive
        updateSurroundingPixels(newAliveCounterMap, x, y, lambda oldCounter: oldCounter+1)
        newAliveMap[x, y] = 1

def nextGeneration():
    newAliveMap = np.copy(aliveMap)
    newAliveCounterMap = np.copy(aliveCounterMap)
    

    iterateMatrix(aliveMap, partial(evolvePixel, newAliveMap, newAliveCounterMap))

    return newAliveMap, newAliveCounterMap

if __name__ == "__main__":
    cv2.namedWindow("output", cv2.WINDOW_NORMAL) 
    cv2.resizeWindow('output', (1024,1024))


    dimensions = [64]*2

    aliveMap = np.zeros(dimensions, dtype=np.uint8)
    aliveCounterMap = np.zeros(dimensions, dtype=np.uint8)

    # merge image with zeroed matrix
    imageMap = mapMatrix(loadImage(), pixelToBinary)
    mergeMatricies(aliveMap, imageMap)

    aliveCounterMap = mapMatrix(aliveMap, partial(countSurroundingAlive, aliveMap))

    #init render
    render()
    generation = 0
    start = time.time()
    while generation <= 1000:

        aliveMap, aliveCounterMap = nextGeneration()
        render()
        generation +=1

    end = time.time()
    print((end-start)/generation)
        #input()