import tf2onnx
import tensorflow as tf

model = tf.keras.models.load_model('path_to_your_model.h5')
onnx_model, _ = tf2onnx.convert.from_keras(model, output_path='model.onnx')
