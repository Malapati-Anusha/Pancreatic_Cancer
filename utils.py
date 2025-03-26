import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model, Model
import os
import uuid

IMG_SIZE = 224

model = load_model("model/pancreas_cnn_model.h5")
HEATMAP_FOLDER = 'static/heatmaps'

def get_gradcam_heatmap(img_array, model, last_conv_layer_name='block5_conv3'):
    grad_model = Model([model.inputs], [model.get_layer(last_conv_layer_name).output, model.output])
    with tf.GradientTape() as tape:
        conv_output, predictions = grad_model(img_array)
        loss = predictions[:, 0]

    grads = tape.gradient(loss, conv_output)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_output = conv_output[0]
    conv_output = conv_output * pooled_grads[tf.newaxis, tf.newaxis, :]
    heatmap = tf.reduce_sum(conv_output, axis=-1)
    heatmap = tf.maximum(heatmap, 0)
    heatmap /= tf.reduce_max(heatmap) + 1e-8
    return heatmap.numpy()

def predict_with_heatmap(image_path):
    img = cv2.imread(image_path)
    img_resized = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img_array = np.expand_dims(img_resized / 255.0, axis=0)

    prediction = model.predict(img_array)[0][0]
    result = "Cancer Detected" if prediction > 0.5 else "No Cancer Detected"
    percentage = float(prediction * 100) if prediction > 0.5 else float((1 - prediction) * 100)

    heatmap = get_gradcam_heatmap(img_array, model)
    heatmap = cv2.resize(heatmap, (IMG_SIZE, IMG_SIZE))

    threshold = 0.4
    mask = np.uint8(255 * (heatmap > threshold))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxed_img = img_resized.copy()
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(boxed_img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    heatmap_colored = cv2.applyColorMap(np.uint8(255 * heatmap), cv2.COLORMAP_JET)
    superimposed_img = heatmap_colored * 0.4 + img_resized

    combined = np.hstack((superimposed_img.astype('uint8'), boxed_img))

    if not os.path.exists(HEATMAP_FOLDER):
        os.makedirs(HEATMAP_FOLDER)

    heatmap_filename = f"{uuid.uuid4().hex}.jpg"
    heatmap_path = os.path.join(HEATMAP_FOLDER, heatmap_filename)
    cv2.imwrite(heatmap_path, combined)

    # Enhanced precautions
    if prediction > 0.5:
        precautions = (
            "Consult an oncologist immediately.\n"
            "Schedule a detailed diagnostic test like MRI/CT.\n"
            "Avoid self-medication.\n"
            "Maintain a healthy, low-fat diet.\n"
            "Stay hydrated and rest well.\n"
            "Seek emotional support from family or counseling."
        )
    else:
        precautions = (
            "No immediate action required.\n"
            "Maintain regular checkups and a healthy lifestyle.\n"
            "Avoid smoking and alcohol.\n"
            "Eat a fiber-rich diet and exercise regularly."
        )

    return result, round(percentage, 2), f"heatmaps/{heatmap_filename}", precautions, f"uploads/{os.path.basename(image_path)}"
