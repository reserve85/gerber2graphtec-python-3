#!/usr/bin/env python

#
# gerber2graphtec
#
# Cut fine-pitch SMT stencils from a gerber file using a Graphtec craft/vinyl cutter (e.g. Silhouette Cameo or Portrait)
#
# Copyright (c) 2012 Peter Monta <pmonta@gmail.com>
#

import sys
import os
import string

#
# parse arguments
#

offset = (4,0.5)
border = (1,1)
matrix = (1,0,0,1)
speed = [2,2]
force = [8,30]
cut_mode = 0
input_filename = ''
media_size = (12,11)
theta = 0

def floats(s):
  return map(float,string.split(s,','))

argc = 1
while argc<len(sys.argv):
  x = sys.argv[argc]
  if x=='--offset':
    offset = floats(sys.argv[argc+1])
    argc = argc + 2
  elif x=='--border':
    border = floats(sys.argv[argc+1])
    argc = argc + 2
  elif x=='--matrix':
    matrix = floats(sys.argv[argc+1])
    argc = argc + 2
  elif x=='--speed':
    speed = floats(sys.argv[argc+1])
    argc = argc + 2
  elif x=='--force':
    force = floats(sys.argv[argc+1])
    argc = argc + 2
  elif x=='--cut_mode':
    cut_mode = int(sys.argv[argc+1])
    argc = argc + 2
  elif x=='--media_size':
    media_size = floats(sys.argv[argc+1])
    argc = argc + 2
  elif x=='--rotate':
    theta = float(sys.argv[argc+1])
    argc = argc + 1
  else:
    input_filename = sys.argv[argc]
    argc = argc + 1

if not input_filename:
  print('usage: gerber2graphtec [options] paste.gbr >/dev/usb/lp0')
  print("")
  print('options:')
  print('  --offset x,y        translate to device coordinates x,y (inches)')
  print('  --border bx,by      cut a border around the bounding box of the gerber file; 0,0 to disable')
  print('  --matrix a,b,c,d    transform coordinates by [a b;c d]')
  print('  --speed s[,s2[,s3]] use speed s in device units; s2,s3 for multiple passes')
  print('  --force f[,f2[,f3]] use force f in device units; f2,f3 for multiple passes')
  print('  --cut_mode [0|1]    0 for highest accuracy (fine pitch), 1 for highest speed')
  print('  --media_size x,y    size of media')
  print('  --rotate theta      rotate counterclockwise by theta degrees')
  print('')
  print('defaults:')
  print('  --offset 4.0,0.5    suitable for letter size (portrait) on the Cameo, fed as "media" not "mat"')
  print('  --border 1,1        1-inch border in x and y around gerber bounding box')
  print('  --matrix 1,0,0,1    identity linear transform for scale and skew calibration')
  print('  --speed 2,2         use two passes, speed 2 in each pass')
  print('  --force 8,30        use force 8 for first pass, force 30 for second pass')
  print('  --cut_mode 0        highest accuracy')
  print('  --media_size 12,11  use a media size of 12 inches in x, 11 inches in y')
  print('  --rotate 0          no rotation')
  print('')
  sys.exit(1)

#
# convert file to pic format
#

temp_pdf = "_tmp_gerber.pdf"
temp_pic = "_tmp_gerber.pic"

if string.lower(input_filename[-3:])=='pdf':
  os.system("pstoedit -f pic %s %s 2>/dev/null" % (input_filename,temp_pic))
else:
  os.system("gerbv --export=pdf --output=%s --border=20 %s" % (temp_pdf,input_filename))
  os.system("pstoedit -f pic %s %s 2>/dev/null" % (temp_pdf,temp_pic))

#
# main program
#

import graphtec
import pic
import optimize

g = graphtec.graphtec()

g.set(media_size=media_size)
g.set(offset=(offset[0]+border[0]+0.5,offset[1]+border[1]+0.5))
g.set(matrix=matrix)

g.start()

strokes = pic.read_pic(temp_pic)
strokes = optimize.rotate(strokes, theta)
strokes = optimize.justify(strokes)
max_x,max_y = optimize.max_extent(strokes)

border_path = [
  (-border[0], -border[1]),
  (max_x+border[0], -border[1]),
  (max_x+border[0], max_y+border[1]),
  (-border[0], max_y+border[1])
]

if cut_mode==0:
  lines = optimize.optimize(strokes, border)
  for (s,f) in zip(speed,force):
    g.set(speed=s, force=f)
    for x in lines:
      g.line(*x)
    if border[0]!=0 or border[1]!=0:
      g.closed_path(border_path)
else:
  for (s,f) in zip(speed,force):
    g.set(speed=s, force=f)
    for s in strokes:
      g.closed_path(s)
    if border[0]!=0 or border[1]!=0:
      g.closed_path(border_path)

g.end()
