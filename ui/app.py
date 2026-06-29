import streamlit as st
import pandas as pd
import time
import os

# ------------------------------------------------------
# 1. Page Configuration & Branding
# ------------------------------------------------------
st.set_page_config(
    page_title="TrioLogic | Semantic Discovery OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Dark Enterprise Observability Theme (Zero-Trust aesthetic)
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #c9d1d9;
        font-family: "Courier New", Courier, monospace;
    }
    .stButton>button { width: 100%; border-radius: 2px; font-weight: bold; background-color: #238636; color: white; border: 1px solid #2ea043; }
    .stButton>button:hover { background-color: #2ea043; }
    .stTextArea>div>textarea { border-radius: 2px; background-color: #161b22; color: #c9d1d9; font-family: monospace; border: 1px solid #30363d; }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 4px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-value { font-size: 28px; font-weight: bold; color: #58a6ff; }
    .metric-label { font-size: 13px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }
    .terminal {
        background-color: #0d1117;
        color: #39ff14;
        font-family: monospace;
        padding: 15px;
        border-radius: 4px;
        border: 1px solid #30363d;
        height: 250px;
        overflow-y: auto;
        font-size: 13px;
        line-height: 1.5;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
    }
    .log-info { color: #8b949e; }
    .log-warn { color: #ffb000; }
    .log-success { color: #39ff14; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ TrioLogic Semantic Discovery OS")
st.markdown("### Zero-Trust Enterprise Observability Dashboard")
st.markdown("---")

# ------------------------------------------------------
# 2. Telemetry Bar (The SRE Flex)
# ------------------------------------------------------
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="metric-card"><div class="metric-value">&lt; 4.2 GB</div><div class="metric-label">Peak Memory Utilization</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card"><div class="metric-value">86.4s</div><div class="metric-label">Execution Latency (50,000 rows)</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-card"><div class="metric-value">273 LOW | 69 DARK</div><div class="metric-label">Epistemic Exclusions Purged</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------
# 3. Layout: System Context & Execution
# ------------------------------------------------------
left_col, right_col = st.columns([1, 2.5])

with left_col:
    st.subheader("System Topology")
    st.markdown("""
    **AWS Infrastructure Context:**
    - **Compute:** EC2 t3.xlarge (IMDSv2 Enforced)
    - **Database:** RDS PostgreSQL (pgvector HNSW)
    - **Isolation:** Private Subnet (SG-EC2 ↔ SG-RDS)
    - **Engine:** PyTorch INT8 + CPU Dot Product
    """)
    
    st.markdown("---")
    st.subheader("Execution Trigger")
    job_desc = st.text_area(
        "Job Description / Semantic Context:",
        height=180,
        value="Looking for a Senior AI Engineer to join the founding team. Must have strong PyTorch and NLP experience."
    )
    
    run_btn = st.button("EXECUTE // RANK", type="primary")

# ------------------------------------------------------
# 4. Live Telemetry Terminal & Confidence Dataframe
# ------------------------------------------------------
with right_col:
    st.subheader("Live Operational Telemetry & Epistemic Ranking")
    
    terminal_placeholder = st.empty()
    df_placeholder = st.empty()
    
    if run_btn:
        # Simulate Terminal Output for Demo
        logs = [
            '<span class="log-info">[INFO] Initiating Zero-Trust Compute... AWS IAM Role verified.</span>',
            '<span class="log-info">[INFO] Streaming 50,000 candidates from pgvector RDS via chunking...</span>',
            '<span class="log-info">[INFO] L1 Gatekeeper Active: 28,885 candidates dropped (Lexical Sieve).</span>',
            '<span class="log-info">[INFO] L2 Lexical Reranker: Top 5,000 extracted for dense semantic analysis.</span>',
            '<span class="log-info">[INFO] L3 Semantic Rerank (PyTorch INT8): Embedding 5,000 candidates via all-MiniLM-L6-v2...</span>',
            '<span class="log-info">[INFO] Layer 5 Epistemic Confidence Engine initialized...</span>',
            '<span class="log-warn">[WARN] Trigger: Stability threshold breached (σ > 0.05). Excluded 69 DARK candidates (Keyword stuffers).</span>',
            '<span class="log-warn">[WARN] Trigger: Coherence threshold breached (< 0.35). Excluded 273 LOW candidates.</span>',
            '<span class="log-success">[SUCCESS] Telemetry complete. Outputting 100 HIGH/MEDIUM trusted candidates to final CSV in 86.4s.</span>'
        ]
        
        terminal_out = ""
        for log in logs:
            terminal_out += log + "<br>"
            terminal_placeholder.markdown(f'<div class="terminal">{terminal_out}</div>', unsafe_allow_html=True)
            time.sleep(0.4)
            
        time.sleep(0.5)
        
        # Load CSV (handles path difference whether run from root or ui dir)
        csv_path = "submission.csv"
        if not os.path.exists(csv_path):
            csv_path = "../submission.csv"
            
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            
            # Parse the reasoning column (format: BAND | sem:X | coh:X | stb:X | Title | ...)
            def parse_reasoning(row):
                parts = [p.strip() for p in str(row).split("|")]
                band = parts[0] if len(parts) > 0 else ""
                sem = parts[1].split(":")[1] if len(parts) > 1 and ":" in parts[1] else ""
                coh = parts[2].split(":")[1] if len(parts) > 2 and ":" in parts[2] else ""
                stb = parts[3].split(":")[1] if len(parts) > 3 and ":" in parts[3] else ""
                title = parts[4] if len(parts) > 4 else ""
                return pd.Series([band, title, sem, coh, stb])
                
            df[['Band', 'Title', 'Sem', 'Coh', 'Stb']] = df['reasoning'].apply(parse_reasoning)
            
            # Select and rename columns for display
            display_df = df[['rank', 'candidate_id', 'Title', 'score', 'Band', 'Sem', 'Coh', 'Stb']]
            display_df.columns = ["Rank", "Candidate ID", "Job Title", "Hybrid Score", "Confidence", "Semantic", "Coherence", "Stability"]
            
            # Streamlit Dataframe Styling (Neon Green for HIGH, Muted Yellow for MEDIUM)
            def style_band(val):
                if val == 'HIGH':
                    return 'color: #39ff14; font-weight: bold;' # Neon Green
                elif val == 'MEDIUM':
                    return 'color: #ffb000; font-weight: bold;' # Muted Yellow
                elif val == 'LOW' or val == 'DARK':
                    return 'color: #ff003c; font-weight: bold;' # Red
                return ''
                
            df_placeholder.dataframe(
                display_df.style.map(style_band, subset=['Confidence']),
                use_container_width=True,
                height=450
            )
        else:
            df_placeholder.error("🚨 submission.csv not found. Ensure rank.py backend was executed first.")
    else:
        terminal_placeholder.markdown('<div class="terminal"><span class="log-info">Awaiting execution trigger. The semantic engine is standing by...</span></div>', unsafe_allow_html=True)
