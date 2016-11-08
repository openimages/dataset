#!/usr/bin/env python
#
# Copyright 2016 The Open Images Authors. All Rights Reserved.
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
#
# This script takes an Inception v3 checkpoint, runs the classifier
# on the image and prints the values from the bottleneck layer.
# Example:
#   $ wget -O /tmp/cat.jpg https://farm6.staticflickr.com/5470/9372235876_d7d69f1790_b.jpg
#   $ ./tools/compute_bottleneck.py /tmp/cat.jpg
#
# Make sure to download the ANN weights and support data with:
# $ ./tools/download_data.sh

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import math
import sys
import os.path

import numpy as np
import tensorflow as tf

from tensorflow.contrib.slim.python.slim.nets import inception
from tensorflow.python.framework import ops
from tensorflow.python.ops import control_flow_ops
from tensorflow.python.ops import data_flow_ops
from tensorflow.python.ops import variables
from tensorflow.python.training import saver as tf_saver
from tensorflow.python.training import supervisor

slim = tf.contrib.slim
FLAGS = None

def PreprocessImage(image_path, central_fraction=0.875):
  """Load and preprocess an image.

  Args:
    image_path: path to an image
    central_fraction: do a central crop with the specified
      fraction of image covered.
  Returns:
    An ops.Tensor that produces the preprocessed image.
  """
  if not os.path.exists(image_path):
    tf.logging.fatal('Input image does not exist %s', image_path)
  img_data = tf.gfile.FastGFile(image_path).read()

  # Decode Jpeg data and convert to float.
  img = tf.cast(tf.image.decode_jpeg(img_data, channels=3), tf.float32)

  img = tf.image.central_crop(img, central_fraction=central_fraction)
  # Make into a 4D tensor by setting a 'batch size' of 1.
  img = tf.expand_dims(img, [0])
  img = tf.image.resize_bilinear(img,
                                 [FLAGS.image_size, FLAGS.image_size],
                                 align_corners=False)

  # Center the image about 128.0 (which is done during training) and normalize.
  img = tf.mul(img, 1.0/127.5)
  return tf.sub(img, 1.0)


def main(args):
  if not os.path.exists(FLAGS.checkpoint):
    tf.logging.fatal(
        'Checkpoint %s does not exist. Have you download it? See tools/download_data.sh',
        FLAGS.checkpoint)
  g = tf.Graph()
  with g.as_default():
    input_image = PreprocessImage(FLAGS.image_path[0])

    with slim.arg_scope(inception.inception_v3_arg_scope()):
      logits, end_points = inception.inception_v3(
          input_image, num_classes=FLAGS.num_classes, is_training=False)

    bottleneck = end_points['PreLogits']
    init_op = control_flow_ops.group(variables.initialize_all_variables(),
                                     variables.initialize_local_variables(),
                                     data_flow_ops.initialize_all_tables())
    saver = tf_saver.Saver()
    sess = tf.Session()
    saver.restore(sess, FLAGS.checkpoint)

    # Run the evaluation on the image
    bottleneck_eval = np.squeeze(sess.run(bottleneck))

  first = True
  for val in bottleneck_eval:
    if not first:
      sys.stdout.write(",")
    first = False
    sys.stdout.write('{:.3f}'.format(val))
  sys.stdout.write('\n')


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--checkpoint', type=str, default='data/2016_08/model.ckpt',
                      help='Checkpoint to run inference on.')
  parser.add_argument('--image_size', type=int, default=299,
                      help='Image size to run inference on.')
  parser.add_argument('--num_classes', type=int, default=6012,
                      help='Number of output classes.')
  parser.add_argument('image_path', nargs=1, default='')
  FLAGS = parser.parse_args()
  tf.app.run()
