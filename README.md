# Dog Breeds Classification Using Transfer Learning

This repository contains a Jupyter Notebook that demonstrates how to classify dog breeds using transfer learning with the InceptionV3 model in Keras.

## Description

This project leverages the power of transfer learning to build a convolutional neural network for classifying 120 different dog breeds from the Stanford Dogs dataset. Transfer learning allows us to utilize a pre-trained model (InceptionV3) and adapt it for our specific task, saving time and resources compared to training a model from scratch.

The notebook covers the following steps:

1. Data Loading and Structure: Exploring the dataset and understanding its structure.
2. Shuffle and Plot Images: Randomly shuffling the images and visualizing a sample.
3. Subset Data: Optionally subsetting the data for memory management.
4. Encoding Data: Encoding the dog breed labels using one-hot encoding.
5. Preparing Train, Validation & Test Data: Splitting the data into training, validation, and testing sets.
6. Data Augmentation: Applying data augmentation to increase the diversity of the training data.
7. Model Building: Constructing the CNN model using InceptionV3 as a base and adding custom layers.
8. Train Model: Training the model on the training data and validating it on the validation set.
9. Accuracy and Loss Plots: Visualizing the training and validation accuracy and loss over epochs.
10. Predicting on Test Set: Evaluating the model's performance on the unseen test data.
11. Model Evaluation Metrics: Calculating accuracy, precision, recall, and F1 score to assess the model's performance.
12. Plot Predictions against Actual Labels: Visualizing predictions and confidence levels for a sample of test images.
13. Conclusions: Summarizing the results and potential improvements.

## Dataset

The Stanford Dogs dataset is used in this project, which contains around 20,000 images of 120 dog breeds. The dataset can be downloaded from: http://vision.stanford.edu/aditya86/ImageNetDogs/

## Requirements

- Python 3.x
- TensorFlow 2.x
- Keras
- scikit-learn
- matplotlib
- numpy
- pandas
- Pillow

## Usage

1. Clone the repository
2. Install the required libraries: `pip install -r requirements.txt`
3. Download the Stanford Dogs dataset and extract it to the desired location.
4. Open the Jupyter Notebook `Stanford_Dog_Breeds_Classification.ipynb` and update the dataset path accordingly.
5. Run the notebook cells sequentially to load the data, build the model, train it, and evaluate its performance.

## Results

The model achieved an accuracy of approximately 90% on the testing dataset.
