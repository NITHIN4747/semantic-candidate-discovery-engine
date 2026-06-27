import streamlit as st
import requests
import pandas as pd
import time

# ------------------------------------------------------
# 1. Page Configuration & Branding
# ------------------------------------------------------
st.set_page_config(
    page_title="TrioLogic | Semantic Talent OS",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner, enterprise look
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 4px; font-weight: bold; }
    .stTextArea>div>textarea { border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 TrioLogic Semantic Candidate Discovery")
st.markdown("### Zero-Trust AI Recruiter & Vector Search Engine")
st.markdown("---")

# ------------------------------------------------------
# 2. UI Layout: Sidebar & Main Content
# ------------------------------------------------------
with st.sidebar:
    st.header("⚙️ System Telemetry")
    st.markdown("**Engine:** `sentence-transformers/all-MiniLM-L6-v2`")
    st.markdown("**Vector Dimensions:** `384`")
    st.markdown("**Distance Metric:** `Cosine Similarity`")
    st.markdown("**Infrastructure:** `AWS EC2 + NitroTPM`")
    st.markdown("**Database:** `Amazon RDS (pgvector)`")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. Ingestion Layer")
    job_desc = st.text_area(
        "Paste Job Description / Requirements:",
        height=350,
        placeholder="Enter nuanced job details here. The LLM will extract semantic meaning, implied skills, and required experience..."
    )
    
    analyze_btn = st.button("🚀 Run Semantic Analysis", type="primary")

# ------------------------------------------------------
# 3. API Integration & Execution
# ------------------------------------------------------
with col2:
    st.subheader("2. Proximity Scoring & Results")
    
    if analyze_btn:
        if not job_desc.strip():
            st.error("⚠️ Please enter a Job Description to begin.")
        else:
            # Display a highly technical progress state for the video demo
            with st.spinner("Translating JD to high-dimensional vectors & calculating Cosine Similarity..."):
                start_time = time.time()
                
                try:
                    # Trigger the FastAPI wrapper on Port 8443
                    payload = {"job_description": job_desc}
                    response = requests.post("http://localhost:8443/v1/rank", json=payload)
                    
                    if response.status_code == 200:
                        elapsed_time = round(time.time() - start_time, 2)
                        st.success(f"✅ Semantic Ranking Complete (Executed in {elapsed_time}s)")
                        
                        # Load the generated submission.csv output
                        try:
                            df = pd.read_csv("submission.csv")  # Defaulting to root since we start streamlit from root or ui
                            
                            # Reformat columns for cleaner UI presentation
                            df.columns = ["Candidate ID", "Rank", "Semantic Score", "Confidence", "Coherence", "Stability", "AI Reasoning"]
                            
                            def style_confidence(val):
                                color = ''
                                if val == 'HIGH': color = '#00FF00'
                                elif val == 'MEDIUM': color = '#FFA500'
                                elif val == 'LOW': color = '#FF4500'
                                return f'color: {color}; font-weight: bold'

                            # Display the interactive dataframe
                            st.dataframe(
                                df.style.map(style_confidence, subset=['Confidence']).background_gradient(subset=['Semantic Score', 'Coherence'], cmap='viridis'),
                                use_container_width=True,
                                height=400
                            )
                            
                        except FileNotFoundError:
                            # Try one level up if streamlit is started inside ui/
                            df = pd.read_csv("../submission.csv")
                            df.columns = ["Candidate ID", "Rank", "Semantic Score", "Confidence", "Coherence", "Stability", "AI Reasoning"]
                            
                            def style_confidence(val):
                                color = ''
                                if val == 'HIGH': color = '#00FF00'
                                elif val == 'MEDIUM': color = '#FFA500'
                                elif val == 'LOW': color = '#FF4500'
                                return f'color: {color}; font-weight: bold'

                            st.dataframe(
                                df.style.map(style_confidence, subset=['Confidence']).background_gradient(subset=['Semantic Score', 'Coherence'], cmap='viridis'),
                                use_container_width=True,
                                height=400
                            )
                    else:
                        st.error(f"Backend Engine Error: {response.text}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("🚨 Connection Failed: Ensure the FastAPI backend is running on http://localhost:8443")
    else:
        st.info("Awaiting execution trigger. The semantic engine is standing by.")
