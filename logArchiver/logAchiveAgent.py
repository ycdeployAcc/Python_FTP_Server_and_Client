#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        logAchiveAgent.py
#
# Purpose:     This module will provide a FTP server which can run in parallel 
#              thread for file transfer.
# 
# Author:      Yuancheng Liu
#
# Created:     2024/07/25
# Version:     v_0.0.1
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import os
import json
import platform

import ConfigLoader
import ftpComm


TEST_MD = False

dirpath = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE_NAME = 'ConfigAgent.txt'
gGonfigPath = os.path.join(dirpath, CONFIG_FILE_NAME)
iConfigLoader = ConfigLoader.ConfigLoader(gGonfigPath, mode='r')
if iConfigLoader is None:
    print("Error: The config file %s is not exist.Program exit!" %str(gGonfigPath))
    exit()
CONFIG_DICT = iConfigLoader.getJson()

slashCar = '\\' if platform.system() == "Windows" else '/'

#-----------------------------------------------------------------------------
def count_slashes(s):
    return str(s).count(slashCar)

#-----------------------------------------------------------------------------
class recordMgr(ConfigLoader.JsonLoader):

    def __init__(self):
        super().__init__()

    def addOneFile(self, filePath):
        if self._haveData():
            self.jsonData.append(filePath)
        else:
            self.jsonData = [filePath]

    def sortFileList(self):
        self.jsonData = sorted(self.jsonData, key=count_slashes)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class LogAchiveAgent():
    def __init__(self):
        
        self.targetDir = os.path.join(dirpath, CONFIG_DICT['LOG_DIR'])
        # 
        self.serverIP = CONFIG_DICT['FTP_SER_IP']
        self.serverPort = int(CONFIG_DICT['FTP_SER_PORT'])
        self.user= CONFIG_DICT['USER_NAME']
        self.password = CONFIG_DICT['USER_PWD']
        # Init the logfile list uploaded to the FTP server.
        self.logFileList = []
        self.recordLoader = recordMgr()
        rcdFIle = os.path.join(dirpath, CONFIG_DICT['RCD_JSON'])
        self.loadRcdFile(rcdFIle)
        self.logFileList = self.recordLoader.getJsonData()
        if not TEST_MD:
            self.client = ftpComm.ftpClient(self.serverIP, self.serverPort, self.user, self.password)
            print("LogAchiveAgent: Start to login to the log server...")
            if self.client.connectToServer():
                print("LogAchiveAgent: Login to the log server successfully!")
            else:
                print("LogAchiveAgent: Login to the log server failed!")
                exit()

    #-----------------------------------------------------------------------------
    def loadRcdFile(self, rcdFile):
        rcdFilePath = os.path.join(dirpath, rcdFile)
        if not os.path.exists(rcdFilePath):
            print("Can not find upload record file %s , create a new record" %str(rcdFilePath))
            with open(rcdFilePath, "w") as fh:
                json.dump([], fh)
        self.recordLoader.loadFile(rcdFilePath)
        
    #-----------------------------------------------------------------------------
    def findAlllogfiles(self, logDir):
        filePathList = []
        postFix = str(CONFIG_DICT['LOG_PF']) if 'LOG_PF' in CONFIG_DICT.keys() else None
        for root, dirs, files in os.walk(self.targetDir):
            for file in files:
                filePath = os.path.join(root, file)
                if filePath.lower().endswith(postFix):
                    filePathList.append(filePath)
        return filePathList

    #-----------------------------------------------------------------------------
    def getNewUploadFiles(self):
        newUpload = []
        allLogfiles = self.findAlllogfiles(None)
        uploadedFiles = self.recordLoader.getJsonData()
        for fileName in allLogfiles:
            if fileName not in uploadedFiles:
                print("LogAchiveAgent: Found a new log file %s" %fileName)
                newUpload.append(fileName)
        # sort the 
        newUpload = sorted(newUpload, key=count_slashes)
        return newUpload
    
    #-----------------------------------------------------------------------------
    def swithHome(self):
        self.client.swithToDir('/')
        homeDir = CONFIG_DICT['AGENT_ID']
        try:
            rst = self.client.swithToDir(homeDir)
        except Exception as erro:
            self.client.createDir(homeDir)
            self.client.swithToDir(homeDir)

    #-----------------------------------------------------------------------------
    def startUpload(self, localFilePath):
        self.swithHome()
        serPath = str(localFilePath).replace(self.targetDir, '')
        dirList = serPath.split(slashCar)
        if len(dirList) > 1:
            for dir in dirList[0:-1]:
                if dir != '':
                    try:
                        self.client.swithToDir(dir)
                    except Exception as erro:
                        self.client.createDir(dir)
                        self.client.swithToDir(dir)
        # upload file
        fileName = dirList[-1]
        try:
            self.client.uploadFile(localFilePath, fileName)
            print("LogAchiveAgent: successfully uploaded file %s" %fileName)
        except Exception as erro:
            print("LogAchiveAgent: Failed to upload file %s" %fileName)

#-----------------------------------------------------------------------------
def main():
    logAchiveAgent = LogAchiveAgent()
    data = logAchiveAgent.getNewUploadFiles()
    tsetFile = data[0]
    logAchiveAgent.startUpload(tsetFile)
    tsetFile = data[-1]
    logAchiveAgent.startUpload(tsetFile)

if __name__ == "__main__":
    main()