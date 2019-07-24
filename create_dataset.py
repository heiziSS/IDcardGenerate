# -*- coding: utf-8 -*-
"""
参考：https://blog.csdn.net/dcrmg/article/details/79155276
"""
import os
import lmdb  # install lmdb by "pip install lmdb"
import cv2
import numpy as np
# from keys import alphabet


# 检查图片是否有效
def checkImageIsValid(imageBin):
    if imageBin is None:
        return False
    imageBuf = np.fromstring(imageBin, dtype=np.uint8)
    img = cv2.imdecode(imageBuf, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False
    imgH, imgW = img.shape[0], img.shape[1]
    if imgH * imgW == 0:
        return False
    return True


def writeCache(env, cache):
    with env.begin(write=True) as txn:
        for k, v in cache.items():
            txn.put(k.encode(), v)

def createDataset(outputPath, dataList, checkValid=True):
    """
    Create LMDB dataset for CRNN training.

    ARGS:
        outputPath    : LMDB output path
        imagePathList : list of image path
        labelList     : list of corresponding groundtruth texts
        lexiconList   : (optional) list of lexicon lists
        checkValid    : if true, check the validity of every image
    """
    nSamples = len(dataList)
    # 1 M = 1048576 bytes
    # 1 G = 1073741824 bytes
    # 1 T = 1099511627776 bytes
    env = lmdb.open(outputPath, map_size=1073741824)

    cache = {}
    cnt = 1
    for data in dataList:
        imagePath = data[0]
        label = data[1]
        if not os.path.exists(imagePath):
            print('%s does not exist' % imagePath)
            continue
        with open(imagePath, 'rb') as f:
            imageBin = f.read()
        if checkValid:
            if not checkImageIsValid(imageBin):
                print('%s is not a valid image' % imagePath)
                continue

        imageKey = 'image-%09d' % cnt
        labelKey = 'label-%09d' % cnt
        cache[imageKey] = imageBin
        cache[labelKey] = label.encode()
        if cnt % 1000 == 0:
            writeCache(env, cache)
            cache = {}
            print('Written %d / %d' % (cnt, nSamples))
        cnt += 1
    nSamples = cnt - 1
    cache['num-samples'] = str(nSamples).encode()
    writeCache(env, cache)
    print('Created dataset with %d samples' % nSamples)


def readDataset(datasetPath):
    with lmdb.open(datasetPath) as env:
        txn = env.begin()
        for key, value in txn.cursor():
            print(key, value)
            # imageBuf = np.fromstring(value, dtype=np.uint8)
            # print(imageBuf)
            # img = cv2.imdecode(imageBuf, cv2.IMREAD_GRAYSCALE)
            # print(img)
            # break
            # if img is not None:
            #     cv2.imshow('image', img)
            #     cv2.waitKey()
            # else:
            #     print('This is a label: {}'.format(value))


def outputLmdb(inputPath, outputPath, dataPath):
    imgLabelList = []
    with open(inputPath, 'r') as f:
        for line in f:
            imgLabel = line.split(" ")
            imagePath = dataPath + imgLabel[0]
            label = imgLabel[1]
            imgLabelList.append((imagePath, label))

    ##sort by labelList
    imgLabelListSort = sorted(imgLabelList, key=lambda x: len(x[1]))
    #pathList = [p[0] for p in imgLabelListSort]
    #labelList = [p[1] for p in imgLabelListSort]

    createDataset(outputPath, imgLabelListSort, checkValid=True)


# import glob
if __name__ == '__main__':

    # lmdb 输出目录
    train_outputPath = './lmdb/mini_train'
    val_outputPath = './lmdb/mini_val'
    train_inputPath = './data/annotations/mini_train.txt'
    val_inputPath = './data/annotations/mini_val.txt'
    dataPath = './data/images/'

    # f = open('./char_std_5990.txt', 'r')
    # characters = f.readlines()
    # f.close()
    # characters_list = [character.strip() for character in characters]

    outputLmdb(train_inputPath, train_outputPath, dataPath)
    outputLmdb(val_inputPath, val_outputPath, dataPath)
    # readDataset(train_outputPath)


