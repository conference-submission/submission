from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import ast
import functools
import sys
import os
import hashlib
import scipy.misc

from datetime import datetime
import json
import numpy as np


import tensorflow as tf


def get_num_classes():
  classes = []
  with tf.gfile.GFile(FLAGS.classes_file, "r") as f:
    classes = [x for x in f]
  num_classes = len(classes)
  return num_classes


def get_input_fn(mode, tfrecord_pattern, batch_size):
  """Creates an input_fn that stores all the data in memory.

  Args:
   mode: one of tf.contrib.learn.ModeKeys.{TRAIN, INFER, EVAL}
   tfrecord_pattern: path to a TF record file created using create_dataset.py.
   batch_size: the batch size to output.

  Returns:
    A valid input_fn for the model estimator.
  """

  def _parse_tfexample_fn(example_proto, mode):
    """Parse a single record which is expected to be a tensorflow.Example."""
    feature_to_type = {
        "ink": tf.VarLenFeature(dtype=tf.float32),
        "shape": tf.FixedLenFeature([2], dtype=tf.int64)
    }
    if mode != tf.estimator.ModeKeys.PREDICT:
      # The labels won't be available at inference time, so don't add them
      # to the list of feature_columns to be read.
      feature_to_type["class_index"] = tf.FixedLenFeature([1], dtype=tf.int64)

    parsed_features = tf.parse_single_example(example_proto, feature_to_type)
    parsed_features["ink"] = tf.sparse_tensor_to_dense(parsed_features["ink"])

    if mode != tf.estimator.ModeKeys.PREDICT:
      labels = parsed_features["class_index"]
      return parsed_features, labels
    else:
      return parsed_features  # In prediction, we have no labels

  def _input_fn():
    """Estimator `input_fn`.

    Returns:
      A tuple of:
      - Dictionary of string feature name to `Tensor`.
      - `Tensor` of target labels.
    """
    dataset = tf.data.TFRecordDataset.list_files(tfrecord_pattern)
    if mode == tf.estimator.ModeKeys.TRAIN:
      dataset = dataset.shuffle(buffer_size=10)
    dataset = dataset.repeat()
    # Preprocesses 10 files concurrently and interleaves records from each file.
    dataset = dataset.interleave(
        tf.data.TFRecordDataset,
        cycle_length=10,
        block_length=1)
    dataset = dataset.map(
        functools.partial(_parse_tfexample_fn, mode=mode),
        num_parallel_calls=10)
    dataset = dataset.prefetch(10000)
    if mode == tf.estimator.ModeKeys.TRAIN:
      dataset = dataset.shuffle(buffer_size=1000000)
    # Our inputs are variable length, so pad them.
    dataset = dataset.padded_batch(
        batch_size, padded_shapes=dataset.output_shapes)

    iter = dataset.make_one_shot_iterator()
    if mode != tf.estimator.ModeKeys.PREDICT:
        features, labels = iter.get_next()
        return features, labels
    else:
        features = iter.get_next()
        return features, None  # In prediction, we have no labels

  return _input_fn


def model_fn(features, labels, mode, params):
  """Model function for RNN classifier.

  This function sets up a neural network which applies convolutional layers (as
  configured with params.num_conv and params.conv_len) to the input.
  The output of the convolutional layers is given to LSTM layers (as configured
  with params.num_layers and params.num_nodes).
  The final state of the all LSTM layers are concatenated and fed to a fully
  connected layer to obtain the final classification scores.

  Args:
    features: dictionary with keys: inks, lengths.
    labels: one hot encoded classes
    mode: one of tf.estimator.ModeKeys.{TRAIN, INFER, EVAL}
    params: a parameter dictionary with the following keys: num_layers,
      num_nodes, batch_size, num_conv, conv_len, num_classes, learning_rate.

  Returns:
    ModelFnOps for Estimator API.
  """

  def _get_input_tensors(features, labels):
    """Converts the input dict into inks, lengths, and labels tensors."""
    # features[ink] is a sparse tensor that is [8, batch_maxlen, 3]
    # inks will be a dense tensor of [8, maxlen, 3]
    # shapes is [batchsize, 2]
    shapes = features["shape"]
    # lengths will be [batch_size]
    lengths = tf.squeeze(
        tf.slice(shapes, begin=[0, 0], size=[params.batch_size, 1]))
    inks = tf.reshape(features["ink"], [params.batch_size, 30, 300, 1])
    if labels is not None:
      labels = tf.squeeze(labels)
    return inks, lengths, labels

  def _add_conv_layers(inks, lengths):
    """Adds convolution layers."""
    convolved = inks
    for i in range(len(params.num_conv)):
      convolved_input = convolved
      if params.batch_norm:
        convolved_input = tf.layers.batch_normalization(
            convolved_input,
            training=(mode == tf.estimator.ModeKeys.TRAIN))
      # Add dropout layer if enabled and not first convolution layer.
      if i > 0 and params.dropout:
        convolved_input = tf.layers.dropout(
            convolved_input,
            rate=params.dropout,
            training=(mode == tf.estimator.ModeKeys.TRAIN))
      convolved = tf.layers.conv2d(
          convolved_input,
          filters=params.num_conv[i],
          kernel_size=params.conv_len[i],
          activation=tf.nn.relu,
          strides=1,
          padding="same",
          name="conv2d_%d" % i)
    shape = convolved.get_shape().as_list()  # [batch, height, width, features] [8, 31, 150, 48]
    transposed = tf.transpose(convolved, perm=[0, 2, 1, 3], name='transposed')  # [batch, width, height, features]
    conv_reshaped = tf.reshape(transposed, [shape[0], -1, shape[1] * shape[3]], name='reshaped')  # [batch, width, height x features]
    return conv_reshaped, lengths

  def _add_regular_rnn_layers(convolved, lengths):
    """Adds RNN layers."""
    if params.cell_type == "lstm":
      cell = tf.nn.rnn_cell.BasicLSTMCell
    elif params.cell_type == "block_lstm":
      cell = tf.contrib.rnn.LSTMBlockCell
    cells_fw = [cell(params.num_nodes) for _ in range(params.num_layers)]
    cells_bw = [cell(params.num_nodes) for _ in range(params.num_layers)]
    if params.dropout > 0.0:
      cells_fw = [tf.contrib.rnn.DropoutWrapper(cell) for cell in cells_fw]
      cells_bw = [tf.contrib.rnn.DropoutWrapper(cell) for cell in cells_bw]
    outputs, _, _ = tf.contrib.rnn.stack_bidirectional_dynamic_rnn(
        cells_fw=cells_fw,
        cells_bw=cells_bw,
        inputs=convolved,
        sequence_length=lengths,
        dtype=tf.float32,
        scope="rnn_classification")
    return outputs


  def _add_rnn_layers(convolved, lengths):
    """Adds recurrent neural network layers depending on the cell type."""
    if params.cell_type != "cudnn_lstm":
      outputs = _add_regular_rnn_layers(convolved, lengths)
    else:
      outputs = _add_cudnn_rnn_layers(convolved)
    # outputs is [batch_size, L, N] where L is the maximal sequence length and N
    # the number of nodes in the last layer.
    mask = tf.tile(
        tf.expand_dims(tf.sequence_mask(lengths, tf.shape(outputs)[1]), 2),
        [1, 1, tf.shape(outputs)[2]])
    zero_outside = tf.where(mask, outputs, tf.zeros_like(outputs))
    outputs = tf.reduce_sum(zero_outside, axis=1)
    return outputs

  def _add_fc_layers(final_state):
    """Adds a fully connected layer."""
    return tf.layers.dense(final_state, params.num_classes)

  # Build the model.
  inks, lengths, labels = _get_input_tensors(features, labels)
  convolved, lengths = _add_conv_layers(inks, lengths)
  final_state = _add_rnn_layers(convolved, lengths)
  logits = _add_fc_layers(final_state)

  # Compute current predictions.
  predictions = tf.argmax(logits, axis=1)

  if mode == tf.estimator.ModeKeys.PREDICT:
      preds = {
          "class_index": predictions,
          "probabilities": tf.nn.softmax(logits),
          "logits": logits
      }

      return tf.estimator.EstimatorSpec(mode, predictions=preds)
      # Add the loss.
  cross_entropy = tf.reduce_mean(
      tf.nn.sparse_softmax_cross_entropy_with_logits(
          labels=labels, logits=logits))

  # Add the optimizer.
  train_op = tf.contrib.layers.optimize_loss(
      loss=cross_entropy,
      global_step=tf.train.get_global_step(),
      learning_rate=params.learning_rate,
      optimizer="Adam",
      # some gradient clipping stabilizes training in the beginning.
      clip_gradients=params.gradient_clipping_norm,
      summaries=["learning_rate", "loss", "gradients", "gradient_norm"])

  return tf.estimator.EstimatorSpec(
      mode=mode,
      predictions={"logits": logits, "predictions": predictions},
      loss=cross_entropy,
      train_op=train_op,
      eval_metric_ops={"accuracy": tf.metrics.accuracy(labels, predictions)})


def create_tfrecord_for_prediction(batch_size, stoke_data, tfrecord_file):
    def parse_line(stoke_data):
        """Parse provided stroke data and ink (as np array) and classname."""
        sample = json.loads(stoke_data)
        inkarray = sample["indicators"]
        np_ink = np.asarray(inkarray, dtype=np.float32)

        features = {}
        features["ink"] = tf.train.Feature(float_list=tf.train.FloatList(value=np_ink.flatten()))
        features["shape"] = tf.train.Feature(int64_list=tf.train.Int64List(value=np_ink.shape))
        f = tf.train.Features(feature=features)
        ex = tf.train.Example(features=f)
        return ex

    if stoke_data is None:
        print("Error: Stroke data cannot be none")
        return

    example = parse_line(stoke_data)

    #Remove the file if it already exists
    if tf.gfile.Exists(tfrecord_file):
        tf.gfile.Remove(tfrecord_file)

    writer = tf.python_io.TFRecordWriter(tfrecord_file)
    for i in range(batch_size):
        writer.write(example.SerializeToString())
    writer.flush()
    writer.close()
    print ('wrote',tfrecord_file)

def get_classes():
  classes = []
  with tf.gfile.GFile(FLAGS.classes_file, "r") as f:
    classes = [x.rstrip() for x in f]
  return classes

def main(unused_args):
  model_params = tf.contrib.training.HParams(
      num_layers=FLAGS.num_layers,
      num_nodes=FLAGS.num_nodes,
      batch_size=FLAGS.batch_size,
      num_conv=ast.literal_eval(FLAGS.num_conv),
      conv_len=ast.literal_eval(FLAGS.conv_len),
      num_classes=get_num_classes(),
      learning_rate=FLAGS.learning_rate,
      gradient_clipping_norm=FLAGS.gradient_clipping_norm,
      cell_type=FLAGS.cell_type,
      batch_norm=FLAGS.batch_norm,
      dropout=FLAGS.dropout)

  estimator = tf.estimator.Estimator(
      model_fn=model_fn,
      model_dir=FLAGS.model_dir,
      params=model_params)

  if FLAGS.predict_for_dir != None:
      res_list = []
      class_names = get_classes()
      file_handles = []
      # Open all input files.
      for filename in sorted(tf.gfile.ListDirectory(FLAGS.predict_for_dir)):
        if not filename.endswith(".ndjson"):
          print("Skipping", filename)
          continue
        file_handles.append(
            tf.gfile.GFile(os.path.join(FLAGS.predict_for_dir, filename), "r"))
        for i in range(len(file_handles)):
          line = file_handles[i].readline()
          while line!="":
            sample = json.loads(line)
            create_tfrecord_for_prediction(FLAGS.batch_size, line, FLAGS.predict_temp_file)
            predict_results = estimator.predict(input_fn=get_input_fn(
                mode=tf.estimator.ModeKeys.PREDICT,
                tfrecord_pattern=FLAGS.predict_temp_file,
                batch_size=FLAGS.batch_size))

            for idx, prediction in enumerate(predict_results):
                index = prediction["class_index"]  # Get the predicted class (index)
                probability = prediction["probabilities"][index]
                class_name = class_names[index]
                print("%s: Predicted Class is: %s with a probability of %f" % (datetime.now(), class_name, probability))
                res = {}
                res["Warning_ID"] = hashlib.md5('prediction-'+sample["date"]).hexdigest()
                res["Event_Type"] = "Civil Unrest"
                res["Event_Date"] = sample["date"]
                res['Case_Count'] = prediction["probabilities"].tolist()
                res_list.append(res)
                break #We care for only the first prediction, rest are all duplicates just to meet the batch size
            line = file_handles[i].readline()
        formated = {}
        formated["participant_id"] = ""
        formated["payload"] = res_list
        with open(FLAGS.output_dir, 'w') as outfile:
          json.dump(formated, outfile)

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.register("type", "bool", lambda v: v.lower() == "true")
  parser.add_argument(
      "--training_data",
      type=str,
      default="",
      help="Path to training data (tf.Example in TFRecord format)")
  parser.add_argument(
      "--eval_data",
      type=str,
      default="",
      help="Path to evaluation data (tf.Example in TFRecord format)")
  parser.add_argument(
      "--classes_file",
      type=str,
      default="",
      help="Path to a file with the classes - one class per line")
  parser.add_argument(
      "--num_layers",
      type=int,
      default=3,
      help="Number of recurrent neural network layers.")
  parser.add_argument(
      "--num_nodes",
      type=int,
      default=64,
      help="Number of node per recurrent network layer.")
  parser.add_argument(
      "--num_conv",
      type=str,
      default="[16, 32, 48]",
      help="Number of conv layers along with number of filters per layer.")
  parser.add_argument(
      "--conv_len",
      type=str,
      default="[5, 5, 3]",
      help="Length of the convolution filters.")
  parser.add_argument(
      "--cell_type",
      type=str,
      default="lstm",
      help="Cell type used for rnn layers: cudnn_lstm, lstm or block_lstm.")
  parser.add_argument(
      "--batch_norm",
      type="bool",
      default="False",
      help="Whether to enable batch normalization or not.")
  parser.add_argument(
      "--learning_rate",
      type=float,
      default=0.0001,
      help="Learning rate used for training.")
  parser.add_argument(
      "--gradient_clipping_norm",
      type=float,
      default=9.0,
      help="Gradient clipping norm used during training.")
  parser.add_argument(
      "--dropout",
      type=float,
      default=0.3,
      help="Dropout used for convolutions and bidi lstm layers.")
  parser.add_argument(
      "--steps",
      type=int,
      default=100000,
      help="Number of training steps.")
  parser.add_argument(
      "--batch_size",
      type=int,
      default=8,
      help="Batch size to use for training/evaluation.")
  parser.add_argument(
      "--model_dir",
      type=str,
      default="",
      help="Path for storing the model checkpoints.")
  parser.add_argument(
      "--output_dir",
      type=str,
      default="",
      help="Path for storing the predictions.")
  parser.add_argument(
      "--self_test",
      type=bool,
      default="False",
      help="Whether to enable batch normalization or not.")
  parser.add_argument(
      "--predict_for_data",
      type=str,
      default="[[[73,66,46,23,12,11,22,48,58,67,70,65],[11,6,2,10,23,33,48,56,54,41,22,10]],[[66,85,71],[9,3,26]],[[24,1,2,8],[6,1,10,19]],[[64,88,134,176,180,184,184,174,111,63,47],[34,29,28,35,39,58,91,94,86,71,62]],[[64,61,62],[74,83,102]],[[83,84,87],[78,102,107]],[[157,159,164],[96,108,116]],[[175,182],[91,115]],[[182,186,198,209,223,234,251,255],[51,36,29,30,38,39,20,8]],[[157,136,128,133,139],[35,47,57,35,29]],[[104,94,84,84,89],[40,52,70,30,26]],[[111,105,105,109,121],[30,59,68,72,34]],[[159,153,153],[41,54,65]]]",
      help=".ndjson single line .drawing (e.g. just the strokes, no labels)")
  parser.add_argument(
      "--predict_for_dir",
      type=str,
      default="",
      help="Path for prediction input data.")
  parser.add_argument(
      "--predict_temp_file",
      type=str,
      default="./predict_temp.tfrecord",
      help="path to a temporary tfrecord that will be created from the .ndjson drawing data")

  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)