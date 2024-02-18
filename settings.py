import configparser
import tensorflow as tf
from pytz import timezone
from keras.models import load_model
from tensorflow import keras
from tensorflow.keras import layers
import json


class CTCLayer(layers.Layer):
    def __init__(self, name=None, **kwargs):
        super(CTCLayer, self).__init__(name=name)
        self.loss_fn = keras.backend.ctc_batch_cost

    def get_config(self):
        config = super(CTCLayer, self).get_config()
        return config

    def call(self, y_true, y_pred):
        # Compute the training-time loss value and add it
        # to the layer using `self.add_loss()`.
        batch_len = tf.cast(tf.shape(y_true)[0], dtype="int64")
        input_length = tf.cast(tf.shape(y_pred)[1], dtype="int64")
        label_length = tf.cast(tf.shape(y_true)[1], dtype="int64")

        input_length = input_length * tf.ones(shape=(batch_len, 1), dtype="int64")
        label_length = label_length * tf.ones(shape=(batch_len, 1), dtype="int64")

        loss = self.loss_fn(y_true, y_pred, input_length, label_length)
        self.add_loss(loss)

        # At test time, just return the computed predictions
        return y_pred


def load_captcha_model(model_path):
    captcha_model = tf.keras.models.load_model(model_path, custom_objects={'CTCLayer': CTCLayer})
    prediction_model = keras.models.Model(captcha_model.get_layer(name="image").input, captcha_model.get_layer(name="dense2").output)
    return prediction_model


PATH_TO_GST_CAPTCHA_MODEL = 'gst_ctc_v2.h5'
PATH_TO_SBI_CAPTCHA_MODEL = 'sbi_ctc_v1.h5'
PATH_TO_TDS_CAPTCHA_MODEL = 'tds_ctc_v1.h5'

with open("captcha_parameters.json",'r') as json_obj: 
    captcha_parameters = json.load(json_obj)

captcha_parameters['sbi']['prediction_model'] = load_captcha_model("sbi_ctc_v1.h5")
captcha_parameters['gst']['prediction_model'] = load_captcha_model("gst_ctc_v2.h5")
captcha_parameters['tds']['prediction_model'] = load_captcha_model("tds_ctc_v1.h5")
