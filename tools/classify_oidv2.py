#!/usr/bin/env python
#
# Copyright 2017 The Open Images Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""This script takes a resnet_v1_101 checkpoint, runs the classifier on the
image and prints top(n) predictions in human-readable form.

-------------------------------
Example command:
-------------------------------

# 0. Create directory for model/data
WORK_PATH="/tmp/oidv2"
mkdir -p "${WORK_PATH}"
cd "${WORK_PATH}"

# 1. Download the model and sample image
wget https://storage.googleapis.com/openimages/2017_07/classes-trainable.txt
wget https://storage.googleapis.com/openimages/2017_07/class-descriptions.csv
wget https://storage.googleapis.com/openimages/2017_07/oidv2-resnet_v1_101.ckpt.tar.gz
tar -xzf oidv2-resnet_v1_101.ckpt.tar.gz

wget -O cat.jpg https://farm6.staticflickr.com/5470/9372235876_d7d69f1790_b.jpg

# 2. Run inference
python classify_v2.py \
--checkpoint_path='oidv2-resnet_v1_101.ckpt' \
--labelmap='classes-trainable.txt' \
--dict='class-descriptions.csv' \
--image="cat.jpg" \
--top_k=10 \
--score_threshold=0.3

# Sample output:
Image: "cat.jpg"

3272: /m/068hy - Pet (score = 0.96)
1076: /m/01yrx - Cat (score = 0.95)
0708: /m/01l7qd - Whiskers (score = 0.90)
4755: /m/0jbk - Animal (score = 0.90)
2847: /m/04rky - Mammal (score = 0.89)
2036: /m/0307l - Felidae (score = 0.79)
3574: /m/07k6w8 - Small to medium-sized cats (score = 0.77)
4799: /m/0k0pj - Nose (score = 0.70)
1495: /m/02cqfm - Close-up (score = 0.55)
0036: /m/012c9l - Domestic short-haired cat (score = 0.40)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
from google.protobuf import text_format

import tensorflow as tf

flags = tf.app.flags
FLAGS = flags.FLAGS

flags.DEFINE_string('labelmap', '/cns/is-d/home/image-understanding/nalldrin/datasets/open-image-dataset/v2/2017_07/classes-trainable.txt', 'Labels, one per line.')

flags.DEFINE_string('dict', '/cns/is-d/home/image-understanding/nalldrin/datasets/open-image-dataset/v2/2017_07/class-descriptions.csv', 'Descriptive string for each label.')

flags.DEFINE_string('checkpoint_path', '/usr/local/google/home/nalldrin/temp/oid_graph/local/adapt-model.ckpt-61995903',
                    'Path to checkpoint file.')

flags.DEFINE_string('image', '',
                    'Comma separated paths to image files on which to perform '
                    'inference.')

flags.DEFINE_integer('top_k', 10, 'Maximum number of results to show.')

flags.DEFINE_float('score_threshold', None, 'Score threshold.')


def LoadLabelMap(labelmap_path, dict_path):
  """Load index->mid and mid->display name maps.
  Args:
    labelmap_path: path to the file with the list of mids, describing predictions.
    dict_path: path to the dict.csv that translates from mids to display names.
  Returns:
    labelmap: an index to mid list
    label_dict: mid to display name dictionary
  """
  labelmap = [line.rstrip()
              for line in tf.gfile.GFile(labelmap_path).readlines()]

  label_dict = {}
  for line in tf.gfile.GFile(dict_path).readlines():
    words = [word.strip(' "\n') for word in line.split(',', 1)]
    label_dict[words[0]] = words[1]

  return labelmap, label_dict


def main(_):
  # Load labelmap and dictionary from disk.
  labelmap, label_dict = LoadLabelMap(FLAGS.labelmap, FLAGS.dict)
  num_classes = len(labelmap)

  g = tf.Graph()
  with g.as_default():
    with tf.Session() as sess:
      saver = tf.train.import_meta_graph(FLAGS.checkpoint_path + '.meta')
      saver.restore(sess, FLAGS.checkpoint_path)

      input_values = g.get_tensor_by_name('input_values:0')
      predictions = g.get_tensor_by_name('multi_predictions:0')

      for image_filename in FLAGS.image.split(','):
        compressed_image = tf.gfile.FastGFile(image_filename, 'rb').read()
        predictions_eval = sess.run(predictions,
                           feed_dict={input_values: [compressed_image]})
        top_k = predictions_eval.argsort()[::-1]  # indices of predictions_eval sorted by score
        if FLAGS.top_k > 0:
          top_k = top_k[:FLAGS.top_k]
        if FLAGS.score_threshold is not None:
          top_k = [i for i in top_k if predictions_eval[i] >= FLAGS.score_threshold]
        print('Image: "%s"\n' % image_filename)
        for idx in top_k:
          mid = labelmap[idx]
          display_name = label_dict[mid]
          score = predictions_eval[idx]
          print('{:04d}: {} - {} (score = {:.2f})'.format(idx, mid, display_name,
                                                      score))


if __name__ == '__main__':
  tf.app.run()
