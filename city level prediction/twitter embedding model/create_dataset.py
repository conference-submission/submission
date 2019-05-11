# Copyright 2017 The TensorFlow Authors. All Rights Reserved.
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

r"""Creates training and eval data from Quickdraw NDJSON files.

This tool reads the NDJSON files from https://quickdraw.withgoogle.com/data
and converts them into tensorflow.Example stored in TFRecord files.

The tensorflow example will contain 3 features:
 shape - contains the shape of the sequence [length, dim] where dim=3.
 class_index - the class index of the class for the example.
 ink - a length * dim vector of the ink.

It creates disjoint training and evaluation sets.

python create_dataset.py \
  --ndjson_path ${HOME}/ndjson \
  --output_path ${HOME}/tfrecord
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import json
import os
import random
import sys
import numpy as np
import tensorflow as tf
import math
import operator
import scipy.misc


def parse_line(ndjson_line):
  """Parse an ndjson line and return ink (as np array) and classname."""
  sample = json.loads(ndjson_line)
  c = sample["counts"]
  if c<=0:
    class_name = "0"
  elif c<=1:
    class_name = "1"
  else:
    class_name = "2"
  if not class_name:
    print ("Empty classname")
    return None, None
  inkarray = sample["indicators"]
  np_ink = np.asarray(inkarray, dtype=np.float32)
  return np_ink, class_name


def convert_data(trainingdata_dir,
                 observations_per_class,
                 output_file,
                 classnames,
                 output_shards=10,
                 offset=0):
  """Convert training data from ndjson files into tf.Example in tf.Record.

  Args:
   trainingdata_dir: path to the directory containin the training data.
     The training data is stored in that directory as ndjson files.
   observations_per_class: the number of items to load per class.
   output_file: path where to write the output.
   classnames: array with classnames - is auto created if not passed in.
   output_shards: the number of shards to write the output in.
   offset: the number of items to skip at the beginning of each file.

  Returns:
    classnames: the class names as strings. classnames[classes[i]] is the
      textual representation of the class of the i-th data point.
  """

  def _pick_output_shard():
    return random.randint(0, output_shards - 1)

  samples_per_class = [1005, 84, 8]
  observations = [int(math.floor(spc * observations_per_class)) for spc in samples_per_class]
  print(observations)

  file_handles = []
  # Open all input files.
  for filename in sorted(tf.gfile.ListDirectory(trainingdata_dir)):
    if not filename.endswith(".ndjson"):
      print("Skipping", filename)
      continue
    file_handles.append(
        tf.gfile.GFile(os.path.join(trainingdata_dir, filename), "r"))

    if offset!=0:  # Fast forward all files to skip the offset.
      training_num = [703, 58, 5]
      if filename=="0.ndjson":
        offset = training_num[0]
      elif filename=="1.ndjson":
        offset = training_num[1]
      else:
        offset = training_num[2]

      count = 0
      for _ in file_handles[-1]:
        count += 1
        if count == offset:
          break

  writers = []
  for i in range(FLAGS.output_shards):
    writers.append(
        tf.python_io.TFRecordWriter("%s-%05i-of-%05i" % (output_file, i,
                                                         output_shards)))
  reading_order = []
  for i in range(len(file_handles)):
    reading_order.extend([i] * observations[i])
  random.shuffle(reading_order)

  for c in reading_order:
    line = file_handles[c].readline()
    ink = None
    while ink is None:
      ink, class_name = parse_line(line)
      if ink is None:
        print ("Couldn't parse ink from '" + line + "'.")
    if class_name not in classnames:
      classnames.append(class_name)
    features = {}
    features["class_index"] = tf.train.Feature(int64_list=tf.train.Int64List(
        value=[classnames.index(class_name)]))
    features["ink"] = tf.train.Feature(float_list=tf.train.FloatList(
        value=ink.flatten()))
    features["shape"] = tf.train.Feature(int64_list=tf.train.Int64List(
        value=ink.shape))
    f = tf.train.Features(feature=features)
    example = tf.train.Example(features=f)
    writers[_pick_output_shard()].write(example.SerializeToString())

  # Close all files
  for w in writers:
    w.close()
  for f in file_handles:
    f.close()
  # Write the class list.
  with tf.gfile.GFile(output_file + ".classes", "w") as f:
    for class_name in classnames:
      f.write(class_name + "\n")
  return classnames


def main(argv):
  del argv
  classnames = convert_data(
      FLAGS.ndjson_path,
      FLAGS.train_observations_per_class,
      os.path.join(FLAGS.output_path, "training.tfrecord"),
      classnames=[],
      output_shards=FLAGS.output_shards,
      offset=0)
  convert_data(
      FLAGS.ndjson_path,
      FLAGS.eval_observations_per_class,
      os.path.join(FLAGS.output_path, "eval.tfrecord"),
      classnames=classnames,
      output_shards=FLAGS.output_shards,
      offset=FLAGS.train_observations_per_class)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.register("type", "bool", lambda v: v.lower() == "true")
  parser.add_argument(
      "--ndjson_path",
      type=str,
      default="",
      help="Directory where the ndjson files are stored.")
  parser.add_argument(
      "--output_path",
      type=str,
      default="",
      help="Directory where to store the output TFRecord files.")
  parser.add_argument(
      "--train_observations_per_class",
      type=int,
      default=0.7,
      help="How many items per class to load for training.")
  parser.add_argument(
      "--eval_observations_per_class",
      type=int,
      default=0.3,
      help="How many items per class to load for evaluation.")
  parser.add_argument(
      "--output_shards",
      type=int,
      default=1,
      help="Number of shards for the output.")

  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
