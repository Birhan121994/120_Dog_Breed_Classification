import streamlit as st
import numpy as np
from keras.preprocessing.image import img_to_array, load_img
from tensorflow.keras.models import load_model
from keras.applications.inception_v3 import preprocess_input
import os
from sklearn.preprocessing import LabelEncoder
import wikipedia
import time
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
from io import BytesIO
from streamlit_option_menu import option_menu

# Load the trained model
model = load_model('dog_breed_classifier_model_via_inceptionv3.h5')

# Load breed labels
dog_classes = os.listdir('Images/')
breeds = [breed.split('-', 1)[1] for breed in dog_classes]  # Extract breed names from folder names

# Initialize LabelEncoder
le = LabelEncoder()
le.fit(breeds)

# Define function to preprocess and predict the image
def prepare_image(image):
    img = load_img(image, target_size=(299, 299))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
    img_array = preprocess_input(img_array)  # Preprocess the image for InceptionV3
    return img_array

def predict_breed(image):
    img_array = prepare_image(image)
    predictions = model.predict(img_array)
    top_5_preds = np.argsort(predictions[0])[::-1][:5]  # Indices of top 5 predictions
    top_5_probs = predictions[0][top_5_preds]  # Probabilities of top 5 predictions
    top_5_breeds = le.inverse_transform(top_5_preds)  # Convert indices to breed names using LabelEncoder
    return top_5_breeds, top_5_probs

# Fetch breed information from Wikipedia
def get_wikipedia_summary(breed_name):
    try:
        summary = wikipedia.summary(breed_name, sentences=3)  # Get summary of the breed
    except wikipedia.exceptions.DisambiguationError as e:
        summary = f"Sorry, there are multiple results for '{breed_name}'. Here's some information on {e.options[0]}."
    except wikipedia.exceptions.HTTPTimeoutError:
        summary = "Sorry, there was a network timeout while fetching information. Please try again later."
    except wikipedia.exceptions.RedirectError:
        summary = "Sorry, the breed name redirects to another page. Please check the spelling or try another breed."
    except wikipedia.exceptions.PageError:
        summary = "Sorry, no information found for this breed."
    except Exception as e:
        summary = f"An error occurred: {str(e)}"
    return summary

# Streamlit UI setup
st.set_page_config(page_title="Dog Breed Classifier", layout="wide")
st.title("🐶 Dog Breed Classifier 🐶")
st.markdown("""
Welcome to the Dog Breed Classifier! 
Upload an image or use your camera to classify a dog breed, and get a brief description about it.
""")
st.markdown("---")

# Sidebar with navigation using option_menu
selected = option_menu(
    menu_title="Main Menu",
    options=['Browse File', 'Take Camera', 'Quiz app', 'Demo', 'Doc'],
    icons=['house', 'yin-yang', 'file-bar-graph-fill', 'steam', 'book'],
    menu_icon='cast',
    default_index=0,
    orientation="vertical"
)

# Layout structure based on the selected option in the sidebar
if selected == "Browse File":
    st.subheader("Upload Picture to Classify Breed")
    
    # Allow users to upload an image
    image_file = st.file_uploader("Upload an Image", type=["jpg", "png", "jpeg"])

    if image_file:
        # Show the uploaded image
        st.image(image_file, caption="Uploaded Image", use_column_width=True)
        
        # Show a loading spinner while processing
        with st.spinner('Classifying breed...'):
            time.sleep(2)  # Simulating a delay
            
            # Get predictions
            top_5_breeds, top_5_probs = predict_breed(image_file)
        
        # Show predictions and confidence scores
        st.subheader("Top 5 Predicted Breeds:")
        for i in range(5):
            st.write(f"{i+1}. {top_5_breeds[i]} with {top_5_probs[i]*100:.2f}% confidence")
        
        # Plot a bar chart for breed confidence
        fig, ax = plt.subplots()
        sns.barplot(x=top_5_breeds, y=top_5_probs*100, ax=ax)
        ax.set_title("Top 5 Breed Confidence")
        ax.set_xlabel("Breed")
        ax.set_ylabel("Confidence (%)")
        st.pyplot(fig)

        # Fetch Wikipedia info for the top predicted breed
        breed_name = top_5_breeds[0]  # Most confident breed
        st.subheader(f"About {breed_name}:")
        wikipedia_summary = get_wikipedia_summary(breed_name)
        st.write(wikipedia_summary)

elif selected == "Take Camera":
    st.subheader("Use Camera to Classify Breed")

    # Capture image from the camera
    camera_image = st.camera_input("Take a picture")

    if camera_image:
        # Show the captured image
        st.image(camera_image, caption="Captured Image", use_column_width=True)
        
        # Show a loading spinner while processing
        with st.spinner('Classifying breed...'):
            time.sleep(2)  # Simulating a delay
            
            # Get predictions
            top_5_breeds, top_5_probs = predict_breed(camera_image)
        
        # Show predictions and confidence scores
        st.subheader("Top 5 Predicted Breeds:")
        for i in range(5):
            st.write(f"{i+1}. {top_5_breeds[i]} with {top_5_probs[i]*100:.2f}% confidence")
        
        # Plot a bar chart for breed confidence
        fig, ax = plt.subplots()
        sns.barplot(x=top_5_breeds, y=top_5_probs*100, ax=ax)
        ax.set_title("Top 5 Breed Confidence")
        ax.set_xlabel("Breed")
        ax.set_ylabel("Confidence (%)")
        st.pyplot(fig)

        # Fetch Wikipedia info for the top predicted breed
        breed_name = top_5_breeds[0]  # Most confident breed
        st.subheader(f"About {breed_name}:")
        wikipedia_summary = get_wikipedia_summary(breed_name)
        st.write(wikipedia_summary)

elif selected == "Quiz app":
    st.subheader("Quiz App (Coming Soon)")

elif selected == "Demo":
    st.subheader("Demo (Coming Soon)")

elif selected == "Doc":
    st.subheader("Documentation")
    st.write("""
        This app allows you to classify dog breeds by either uploading an image or using your camera.
        The model predicts the breed and provides a short description fetched from Wikipedia.
    """)

# Footer (Optional)
st.markdown("---")
st.markdown("Built with ❤️ by [Your Name]")
