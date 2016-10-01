''' 
  Download all the images from the images.csv file
'''

import csv
import sys
import urllib

i = 0
r_file = open('images.csv', 'rt')
w_file = open('img_label.csv', 'wt')
writer = csv.writer(w_file)

images = csv.reader(r_file)
img_label = csv.writer(w_file)

try:    
    imgs = iter(images)
    next(imgs)
    for img in imgs:
        i += 1
        urllib.urlretrieve (img[1], 'image_%d.jpg' % i)
        img_id = ('image_%d.jpg .... Saved' % i)
        print (img_id)
        img_label.writerow(['image_%d.jpg' % i , img[6]])
finally:
    r_file.close()
    w_file.close()
