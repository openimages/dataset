''' 
  Download all the images from the images.csv file
'''

import csv
import sys
import urllib

i = 0
r_file = open('images.csv', 'rt')
w_file = open('images_id.csv', 'wt')
writer = csv.writer(w_file)

images = csv.reader(r_file)
images_id = csv.writer(w_file)
images_id.writerow(["Image ID", "File Name"])

try:    
    imgs = iter(images)
    next(imgs)
    for img in imgs:
        i += 1
        urllib.urlretrieve (img[1], 'image_%d.jpg' % i)
        print ('image_%d.jpg .... Saved' % i)
        images_id.writerow([img[0], 'image_%d.jpg' % i])
finally:
    r_file.close()
    w_file.close()
