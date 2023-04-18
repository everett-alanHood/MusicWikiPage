import tensorflow as tf
from tensorflow.keras.metrics import Metric
from rouge_score import rouge_scorer as rs


class RougeMetric(Metric):

  def __init__(self, method='min', **kwargs):
    super().__init__(**kwargs)

    if method not in {'avg', 'min', 'max'}:
      raise ValueError("Invalid score method, expected 'min', 'avg' or 'max' (str)")
    self.method = method
    self.rouge_scoring = rs.RougeScorer(['rougeL'])

    if self.method == 'min':
      self.f1_score = tf.Variable(1.0, dtype=tf.float32, trainable=False)
    else:
      self.f1_score = tf.Variable(0.0, dtype=tf.float32, trainable=False)
    self.co = tf.Variable(0.0, dtype=tf.float32, trainable=False)

  def sequences_to_texts(self, sequence): # (47, ) -> (1, )
      return tokenizer.sequences_to_texts(sequence.numpy().reshape(1, -1))

  def tf_sequences_to_texts(self, sequence): # (47, ) -> (1, )
      return tf.py_function(self.sequences_to_texts, [sequence], tf.string)

  def get_f1(self, ref, hyp): # (2, ) -> int
      score = self.rouge_scoring.score(ref.numpy(), hyp.numpy())
      return score['rougeL'].fmeasure

  def get_rouge(self, vals): # (2, ) -> int
      return tf.py_function(self.get_f1, [vals[0], vals[1]], tf.float32)

  def update_state(self, y_true, y_preds, sample_weight=None):
    max_preds = tf.convert_to_tensor(tf.argmax(y_preds, axis=-1)) # (50, 47)

    text_preds = tf.map_fn(self.tf_sequences_to_texts, max_preds, dtype=tf.string) # (50, 47) -> (50, )
    text_true = tf.map_fn(self.tf_sequences_to_texts, y_true, dtype=tf.string) # (50, 47) -> (50, )

    scores_f1 = tf.map_fn(self.get_rouge, (text_true, text_preds), dtype=tf.float32) # (50, 50) -> (50, )

    if self.method == 'min':
      self.f1_score.assign(tf.minimum(self.f1_score, tf.reduce_min(scores_f1)))
    elif self.method == 'avg':
      self.f1_score.assign_add(tf.reduce_sum(scores_f1))
      self.co.assign_add(tf.cast(tf.shape(y_true)[0], dtype=tf.float32))
    elif self.method == 'max':
      self.f1_score.assign(tf.maximum(self.f1_score, tf.reduce_max(scores_f1)))
    else:
      raise ValueError("Invalid score method when updating f1_score, expected 'min', 'avg' or 'max' (str)")

  def result(self):
    if self.method == 'avg':
      avg = self.f1_score / self.co
      return tf.round(avg * 10_000) / 10_000
    else:
      return tf.round(self.f1_score * 10_000) / 10_000

  def reset_state(self):
    print('\n reset')
    if self.method == 'min':
        self.f1_score.assign(1.0)
    else:
        self.f1_score.assign(0.0)
    self.co.assign(0.0)
