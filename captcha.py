import cv2
import os, re
import shutil
import numpy as np
from base64 import b64decode
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.preprocessing.image import img_to_array
import json
from settings import captcha_parameters


class CaptchaModelPredictionClass:
    def __init__(self, captcha_type):
        self.captcha_type = captcha_type
        self.prediction_model = captcha_parameters[captcha_type]['prediction_model']
        self.characters = captcha_parameters[captcha_type]['characters']
        self.max_length = captcha_parameters[captcha_type]['max_length']

        self.char_to_num = layers.StringLookup(vocabulary=list(self.characters), mask_token=None)
        self.num_to_char = layers.StringLookup(vocabulary=self.char_to_num.get_vocabulary(), mask_token=None, invert=True)

        self.img_width = 225
        self.img_height = 75

    def gst_image_processing(self, image_path):
        image = cv2.imread(image_path)
        image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_AREA)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 145, 0)
        kernel = np.ones((3, 3), np.uint8)
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        kernel = np.ones((1, 1), np.uint8)
        image = cv2.dilate(image, kernel, iterations=1)
        image = cv2.resize(image, (self.img_width, self.img_height))
        return image

    def tds_image_processing(self, image_path):
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_AREA)
        image = 255 - image[:, :, 3]
        image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 145, 0)
        kernel = np.ones((3, 3), np.uint8)
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        kernel = np.ones((1, 1), np.uint8)
        image = cv2.dilate(image, kernel, iterations=1)
        image = cv2.resize(image, (self.img_width, self.img_height))
        return image

    def general_image_processing(self, image_path):
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = cv2.resize(image, (self.img_width, self.img_height))
        return image


    def general_postprocessing(self, preds):
        preds = str(preds[0]).replace('[UNK]', '').strip()
        if len(preds) != self.max_length: preds = ''
        return preds

    def decode_predictions(self, prediction):
        input_len = np.ones(prediction.shape[0]) * prediction.shape[1]
        results = keras.backend.ctc_decode(prediction, input_length=input_len, greedy=True)[0][0][:, :self.max_length]
        # Iterate over the results and get back the text
        output_text = []
        for res in results:
            res = tf.strings.reduce_join(self.num_to_char(res)).numpy().decode("utf-8")
            output_text.append(res)
        return output_text

    def predictions(self, image):
        image = np.transpose(image, (1, 0))
        payload = np.expand_dims(img_to_array(image), axis=0) / 255.0
        preds = self.prediction_model.predict(payload, verbose=0)
        pred_texts = self.decode_predictions(preds)
        return pred_texts


class CaptchaCracking:
    def __init__(self, imfile, captcha_type):
        self.captcha_type = captcha_type
        self.file = imfile
        
    def captcha_cracking(self):
        if self.captcha_type not in captcha_parameters.keys():
            captcha_text = 'service under development !'
        else:
            predict_obj = CaptchaModelPredictionClass(self.captcha_type)
            if self.captcha_type == 'gst':
                img = predict_obj.gst_image_processing(self.file)
                captcha_text = predict_obj.predictions(img)[0]
            elif self.captcha_type == 'sbi':
                img = predict_obj.general_image_processing(self.file)
                captcha_text = predict_obj.predictions(img)
                captcha_text = predict_obj.general_postprocessing(captcha_text)
            elif self.captcha_type == 'tds':
                img = predict_obj.tds_image_processing(self.file)
                captcha_text = predict_obj.predictions(img)
                captcha_text = predict_obj.general_postprocessing(captcha_text)
            else:
                img = predict_obj.general_image_processing(self.file)
                captcha_text = predict_obj.predictions(img)
                captcha_text = predict_obj.uidai_postprocessing(captcha_text)

        return captcha_text if captcha_text else ''