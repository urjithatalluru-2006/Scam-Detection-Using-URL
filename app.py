from pathlib import Path

import joblib
import pandas as pd
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_DIR / "scam_detection_model.pkl"

st.set_page_config(page_title="Phishing URL Detector", page_icon="Shield", layout="centered")
st.title("Scam Detection Using URL")
st.write("Detect potentially phishing URLs using machine learning.")

@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


try:
    saved_data = load_model()
    model = saved_data["model"]
    feature_names = saved_data["features"]
except FileNotFoundError:
    st.error(f"Model file not found at {MODEL_PATH}. Run `python run_pipeline.py` first.")
    st.stop()
except Exception as exc:
    st.error(f"Could not load the model at {MODEL_PATH}: {exc}")
    st.stop()

st.info("Upload a dataset with the model's feature columns. Live URL-only prediction requires matching feature extraction.")
st.subheader("Test a dataset record")
uploaded_file = st.file_uploader("Upload cleaned_dataset.csv", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as exc:
        st.error(f"Could not read the uploaded CSV: {exc}")
        st.stop()

    if df.empty:
        st.error("The uploaded CSV has no data rows.")
        st.stop()

    missing = [column for column in feature_names if column not in df.columns]
    if missing:
        st.error("Missing model features: " + ", ".join(missing))
    else:
        index = st.number_input(
            "Dataset row number (starting at 0)",
            min_value=0,
            max_value=len(df) - 1,
            value=0,
            step=1,
        )
        if st.button("Predict"):
            features = df.iloc[[int(index)]][feature_names].copy()
            for column in feature_names:
                features[column] = pd.to_numeric(features[column], errors="coerce")

            prediction = int(model.predict(features)[0])
            if prediction == 0:
                st.error("Prediction: PHISHING URL")
            else:
                st.success("Prediction: LEGITIMATE URL")

            if "URL" in df.columns:
                st.write("URL:", df.iloc[int(index)]["URL"])
            st.caption("Predictions indicate model output, not a guarantee of safety.")
