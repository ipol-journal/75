#!/usr/bin/env python3

import argparse
import os
import shutil
from PIL import Image
import sys
import subprocess

# parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("--thresholdtype", type=int)
ap.add_argument("--tmax", type=int)
ap.add_argument("--m", type=int)
args = ap.parse_args()

#string to bool
list_commands = ""

def runCommand(command, stdOut=None, stdErr=None, comp=None):
    """
    Run command and update the attribute list_commands
    """
    global list_commands
    p = subprocess.run(command, stderr=stdErr, stdout=stdOut)
    index = 0
    # transform convert.sh in it classic prog command (equivalent)
    for arg in command:
        if arg == "convert.sh" :
            command[index] = "convert"
        index = index + 1
    command_to_save = ' '.join(['"' + arg + '"' if ' ' in arg else arg
                for arg in command ])
    if comp is not None:
        command_to_save += comp
    list_commands +=  command_to_save + '\n'
    return command_to_save

def commentsResultContourFile(command, fileStrContours):
    """
    Add comments in the resulting contours (command line producing the file,
    or file format info)
    """

    with open("tmp.dat", "w") as contoursList:
        contoursList.write("# Set of resulting contours obtained from the " +\
                        "pgm2freeman algorithm. \n")
        contoursList.write( "# Each line corresponds to a digital "  + \
                            "contour " +  \
                            " given with the first point of the digital "+ \
                            "contour followed  by its freeman code "+ \
                            "associated to each move from a point to "+ \
                            "another (4 connected: code 0, 1, 2, and 3).\n")
        contoursList.write( "# Command to reproduce the result of the "+\
                        "algorithm:\n")
        contoursList.write("# "+ command+'\n \n')
    
    with open("inputContour.txt", "r") as f:
        index = 0
        for line in f:
            contoursList.write("# contour number: "+ str(index) + "\n")
            contoursList.write(line+"\n")
            index = index +1
    
    shutil.copy('tmp.dat', fileStrContours)
    os.remove('tmp.dat')

##  -------
## process 2: extract contour files
## ---------
with open("inputPolygon.txt", "w") as f, open("algoLog.txt", "w") as fInfo:
        command_args = ['pgm2freeman']+ ['-min_size', str(args.m), '-image', 'inputNG.pgm']+ ['-outputSDPAll' ]

        if not args.thresholdtype:  #autothreshold means thresholdtype=1
            command_args += ['-maxThreshold', str(args.tmax)]+ \
                            ['-minThreshold', str(args.tmin)]

        cmd = runCommand(command_args, f, fInfo, comp = ' > inputPolygon.txt')

        if os.path.getsize("inputPolygon.txt") == 0:
            raise ValueError



# t, m, autothreshold

##  -------
## process 1: transform input file
## ---------
command_args = ['convert.sh', 'input_0.png', 'input_0.pgm' ]
runCommand(command_args)


##  -------
## process 2: Extract 2D contours
## ---------
with open("input_0.pgm", "r") as fInput, open("inputContour.txt", "w") as f, open("info.txt", "w") as fInfo:        
        command_args = ['pgm2freeman']
        if not args.thresholdtype:  #autothreshold means thresholdtype=1
            command_args += ['-threshold', str(args.tmax) ]
            command_args += ['-min_size', str(args.m) ]
                        
        cntExtractionCmd = runCommand(command_args, stdIn=fInput, stdOut=f, stdErr=fInfo, comp = ' < input_0.pgm > inputContour.txt')

        sizeContour = os.path.getsize("inputContour.txt")
        if sizeContour == 0:
            with open('demo_failure.txt', 'w') as file:
                file.write("The parameters given produce no contours, please change them.")
                sys.exit(0)


#Recover otsu max value from log
with open("info.txt", "r") as fInfo:
    if args.thresholdtype:
        lines = fInfo.readlines()
        line_cases = lines[0].split('=')
        args.tmax = float(line_cases[1])

commentsResultContourFile(cntExtractionCmd, 'inputContourFC.txt')


##  -------
## process 3: Convert background image
## ---------
command_args = ['convert.sh', '-brightness-contrast', '40x-40' ]
command_args += ['input_0.png', 'input_0BG.png']
runCommand(command_args)

command_args = ['convert.sh', '-white-threshold', '-1' ]
command_args += ['input_0.png', 'input_0BGW.png']
runCommand(command_args)


##  -------
## process 4:
## ---------
with open("noiseLevels.txt", "w") as foutput, open("logMS.txt", "w") as fLog, open("inputContour.txt", "r") as fInput:

    command_args = ['meaningfulScaleEstim', '-enteteXFIG']+\
                    ['-drawXFIGNoiseLevel', '-setFileNameFigure']+\
                    ['noiseLevel.fig', '-drawContourSRC', '4', '1']+\
                    ['-afficheImage', 'input_0BG.png']+\
                    [str(Image('input_0BG.png').size[0])] +\
                    [str(Image('input_0BG.png').size[1])] +\
                    ['-setPosImage', '1', '1', '-printNoiseLevel'] + \
                    ['-processAllContours']
    try:
        num_lines = sum(1 for line in fInput)
        num_contours = num_lines
        runCommand(command_args, stdIn=fInput, stdOut=foutput, stdErr=fLog, comp="< inputContour.txt > noiseLevels.txt")
    except (OSError, RuntimeError):
        fLog.write("Some contours were not processed.")

p = subprocess.run(['convertFig.sh','noiseLevel.fig'])


## -----
## process 5:
## -----
# Edit fig to obtain display without background image
with open('noiseLevelWhiteBG.fig', "w") as foutput, open('logTransform.txt', "w") as fLog:
    command_args = ['sed.sh', '-e', 's/input_0BG.png/input_0BGW.png/', 'noiseLevel.fig']
    
    runCommand(command_args,  stdOut=foutput, \
                    stdErr=fLog, comp=" > noiseLevelWhiteBG.fig")


shutil.copy('resu.png', 'resuBG.png')
shutil.copy('resu.eps', 'resuBG.eps')

p = subprocess.run(['convertFig.sh','noiseLevelWhiteBG.fig'])

shutil.copy('resu.png', 'resuWhiteBG.png')
shutil.copy('resu.eps', 'resuWhiteBG.eps')


## ----
## Final step: save command line
## ----
with open("commands.txt", "w") as f:
    f.write(list_commands)