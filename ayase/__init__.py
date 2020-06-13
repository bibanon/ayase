#!/usr/bin/python3
# -*- coding: utf-8 -*-
 
#import fourchan
#from model.asagi import *
import json
from view.asagi import thread_html, index_html
from model.asagi import generate_gallery
 
#html = thread_html('g', 50959866)
#html = thread_html('a', 132646961)
#html = index_html('a', 1)
#print(html)

print(json.dumps(generate_gallery('a',1)))
