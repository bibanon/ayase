#!/usr/bin/python3
# -*- coding: utf-8 -*-
 
#import fourchan
from model.asagi import *
from view.asagi import thread_html
 
html = thread_html('g', 50959866)
#html = thread_html('a', 132646961)
print(html)
