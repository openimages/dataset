# python3
# coding=utf-8
# Copyright 2020 The Google Research Authors.
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
"""Open Images image downloader.

This script downloads a subset of Open Images images, given a list of image ids.
Typical uses of this tool might be downloading images:
- That contain a certain category.
- That have been annotated with certain types of annotations (e.g. Localized
Narratives, Exhaustively annotated people, etc.)

The input file IMAGE_LIST should be a text file containing one image per line
with the format <SPLIT>/<IMAGE_ID>, where <SPLIT> is either "train", "test",
"validation", or "challenge2018"; and <IMAGE_ID> is the image ID that uniquely
identifies the image in Open Images. A sample file could be:
  train/f9e0434389a1d4dd
  train/1a007563ebc18664
  test/ea8bfd4e765304db

"""

import argparse
from concurrent import futures
import os
import re
import sys

import boto3
import botocore
import tqdm

BUCKET_NAME = 'open-images-dataset'
REGEX = r'(test|train|validation|challenge2018)/([a-fA-F0-9]*)'


def check_and_homogenize_one_image(image):
  split, image_id = re.match(REGEX, image).groups()
  yield split, image_id


def check_and_homogenize_image_list(image_list):
  for line_number, image in enumerate(image_list):
    try:
      yield from check_and_homogenize_one_image(image)
    except (ValueError, AttributeError):
      raise ValueError(
          f'ERROR in line {line_number} of the image list. The following image '
          f'string is not recognized: "{image}".')


def read_image_list_file(image_list_file):
  with open(image_list_file, 'r') as f:
    for line in f:
      yield line.strip().replace('.jpg', '')


def download_one_image(bucket, split, image_id, download_folder):
  try:
    bucket.download_file(f'{split}/{image_id}.jpg',
                         os.path.join(download_folder, f'{image_id}.jpg'))
  except botocore.exceptions.ClientError as exception:
    sys.exit(
        f'ERROR when downloading image `{split}/{image_id}`: {str(exception)}')


def download_all_images(args):
  """Downloads all images specified in the input file."""
  bucket = boto3.resource(
      's3', config=botocore.config.Config(
          signature_version=botocore.UNSIGNED)).Bucket(BUCKET_NAME)

  download_folder = args['download_folder'] or os.getcwd()

  if not os.path.exists(download_folder):
    os.makedirs(download_folder)

  try:
    image_list = list(
        check_and_homogenize_image_list(
            read_image_list_file(args['image_list'])))
  except ValueError as exception:
    sys.exit(exception)

  progress_bar = tqdm.tqdm(
      total=len(image_list), desc='Downloading images', leave=True)
  with futures.ThreadPoolExecutor(
      max_workers=args['num_processes']) as executor:
    all_futures = [
        executor.submit(download_one_image, bucket, split, image_id,
                        download_folder) for (split, image_id) in image_list
    ]
    for future in futures.as_completed(all_futures):
      future.result()
      progress_bar.update(1)
  progress_bar.close()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument(
      'image_list',
      type=str,
      default=None,
      help=('Filename that contains the split + image IDs of the images to '
            'download. Check the document'))
  parser.add_argument(
      '--num_processes',
      type=int,
      default=5,
      help='Number of parallel processes to use (default is 5).')
  parser.add_argument(
      '--download_folder',
      type=str,
      default=None,
      help='Folder where to download the images.')
  download_all_images(vars(parser.parse_args()))
