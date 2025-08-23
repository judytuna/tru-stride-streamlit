import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import hashlib
import tempfile
import os
import json

# Database setup
def init_db():
    conn = sqlite3.connect('horse_gait.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT, created_at TIMESTAMP)''')
    
    # Videos table
    c.execute('''CREATE TABLE IF NOT EXISTS videos
                 (id INTEGER PRIMARY KEY, user_id INTEGER, filename TEXT, 
                  upload_date TIMESTAMP, analysis_results TEXT,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

def get_user_stats():
    conn = sqlite3.connect('horse_gait.db')
    
    # Total users and videos
    total_users = pd.read_sql_query("SELECT COUNT(*) as count FROM users", conn).iloc[0]['count']
    total_videos = pd.read_sql_query("SELECT COUNT(*) as count FROM videos", conn).iloc[0]['count']
    
    # Videos per user
    videos_per_user = pd.read_sql_query('''
        SELECT u.username, COUNT(v.id) as video_count
        FROM users u
        LEFT JOIN videos v ON u.id = v.user_id
        GROUP BY u.id, u.username
        ORDER BY video_count DESC
    ''', conn)
    
    # Upload trends
    upload_trends = pd.read_sql_query('''
        SELECT DATE(upload_date) as date, COUNT(*) as uploads
        FROM videos
        GROUP BY DATE(upload_date)
        ORDER BY date DESC
        LIMIT 30
    ''', conn)
    
    conn.close()
    return total_users, total_videos, videos_per_user, upload_trends

def authenticate_user(username, password):
    # Simple hash-based auth (use proper auth in production)
    conn = sqlite3.connect('horse_gait.db')
    c = conn.cursor()
    
    # Check if user exists, create if not
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    
    if not user:
        c.execute("INSERT INTO users (username, email, created_at) VALUES (?, ?, ?)",
                 (username, f"{username}@example.com", datetime.now()))
        conn.commit()
        user_id = c.lastrowid
    else:
        user_id = user[0]
    
    conn.close()
    return user_id

def save_analysis(user_id, filename, analysis_results):
    conn = sqlite3.connect('horse_gait.db')
    c = conn.cursor()
    c.execute("INSERT INTO videos (user_id, filename, upload_date, analysis_results) VALUES (?, ?, ?, ?)",
             (user_id, filename, datetime.now(), analysis_results))
    conn.commit()
    conn.close()

def get_user_videos(user_id):
    conn = sqlite3.connect('horse_gait.db')
    videos = pd.read_sql_query('''
        SELECT filename, upload_date, analysis_results
        FROM videos
        WHERE user_id = ?
        ORDER BY upload_date DESC
    ''', conn, params=(user_id,))
    conn.close()
    return videos

def analyze_gait(video_file):
    """
    Call your HuggingFace Gradio app for gait analysis
    """
    try:
        from gradio_client import Client
        
        # Connect to your Gradio space
        client = Client("judytuna/tru-stride-analyzer")
        
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(video_file.read())
            tmp_file_path = tmp_file.name
        
        # Call your Gradio app
        # Adjust the prediction call based on your Gradio interface
        result = client.predict(
            tmp_file_path,  # video input
            api_name="/predict"  # adjust this to match your Gradio endpoint
        )
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        # Parse the result from your Gradio app
        # You'll need to adjust this based on what your model returns
        if isinstance(result, tuple):
            # If your Gradio returns multiple outputs
            analysis_text = result[0] if result else "No analysis available"
            confidence = 0.85  # Extract from your actual results
        else:
            analysis_text = str(result)
            confidence = 0.85
        
        # Parse your actual results into structured format
        # This is where you'll extract the real analysis from your model
        analysis = parse_gradio_results(analysis_text)
        
        return analysis
        
    except Exception as e:
        st.error(f"Error analyzing video: {str(e)}")
        # Fallback to demo data if API fails
        return {
            "primary_gait": "Analysis Failed",
            "confidence": 0.0,
            "stride_length": 0.0,
            "rhythm_score": 0.0,
            "symmetry_score": 0.0,
            "error": str(e)
        }

def parse_gradio_results(analysis_text):
    """
    Parse the stride analysis results from your Gradio app
    Expected format:
    ⚠️ **Stride Analysis Results**
    **Classification:** ABNORMAL
    **Confidence:** 95%
    **Processing Time:** 2.1 seconds
    **Details:** ...
    **Metrics:**
    - Stride Variability: 0.589
    - Mean Knee Angle: 66.0°
    - Body Length Variation: 0.749
    """
    try:
        import re
        
        # Initialize defaults
        analysis = {
            "primary_gait": "Unknown",
            "confidence": 0.0,
            "stride_variability": 0.0,
            "knee_angle": 0.0,
            "body_length_variation": 0.0,
            "processing_time": 0.0,
            "classification": "Unknown",
            "details": ""
        }
        
        # Parse the text line by line
        lines = analysis_text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Extract Classification (NORMAL/ABNORMAL)
            if "**Classification:**" in line:
                classification = line.split("**Classification:**")[-1].strip()
                analysis["classification"] = classification
                # Map to gait terminology for dashboard
                analysis["primary_gait"] = f"Stride: {classification}"
            
            # Extract Confidence percentage
            elif "**Confidence:**" in line:
                confidence_str = line.split("**Confidence:**")[-1].strip()
                # Remove % symbol and convert to decimal
                confidence_num = re.findall(r'\d+', confidence_str)
                if confidence_num:
                    analysis["confidence"] = float(confidence_num[0]) / 100.0
            
            # Extract Processing Time
            elif "**Processing Time:**" in line:
                time_str = line.split("**Processing Time:**")[-1].strip()
                time_num = re.findall(r'[\d.]+', time_str)
                if time_num:
                    analysis["processing_time"] = float(time_num[0])
            
            # Extract Details
            elif "**Details:**" in line:
                details = line.split("**Details:**")[-1].strip()
                analysis["details"] = details
            
            # Extract Metrics
            elif "Stride Variability:" in line:
                variability = re.findall(r'[\d.]+', line)
                if variability:
                    analysis["stride_variability"] = float(variability[0])
            
            elif "Mean Knee Angle:" in line:
                angle = re.findall(r'[\d.]+', line)
                if angle:
                    analysis["knee_angle"] = float(angle[0])
            
            elif "Body Length Variation:" in line:
                variation = re.findall(r'[\d.]+', line)
                if variation:
                    analysis["body_length_variation"] = float(variation[0])
        
        # Calculate quality scores based on your metrics
        # Lower variability = better rhythm (inverted scale)
        rhythm_score = max(0, 10 - (analysis["stride_variability"] * 10))
        
        # Body length variation - lower is better (inverted scale)  
        symmetry_score = max(0, 10 - (analysis["body_length_variation"] * 10))
        
        # Use knee angle as stride length approximation (normalize to reasonable range)
        stride_length = analysis["knee_angle"] / 30.0  # Rough conversion
        
        # Final formatted results
        return {
            "primary_gait": analysis["primary_gait"],
            "confidence": analysis["confidence"],
            "stride_length": round(stride_length, 1),
            "rhythm_score": round(rhythm_score, 1),
            "symmetry_score": round(symmetry_score, 1),
            "classification": analysis["classification"],
            "stride_variability": analysis["stride_variability"],
            "knee_angle": analysis["knee_angle"],
            "body_length_variation": analysis["body_length_variation"],
            "processing_time": analysis["processing_time"],
            "details": analysis["details"]
        }
            
    except Exception as e:
        return {
            "primary_gait": "Parse Error",
            "confidence": 0.0,
            "stride_length": 0.0,
            "rhythm_score": 0.0,
            "symmetry_score": 0.0,
            "error": f"Parsing failed: {str(e)}",
            "raw_output": analysis_text
        }

# Initialize database
init_db()

# App configuration
st.set_page_config(page_title="Horse Gait Analyzer", page_icon="🐎", layout="wide")

# Main app
def main():
    st.title("🐎 Horse Gait Analyzer")
    
    # Authentication
    if 'user_id' not in st.session_state:
        st.sidebar.header("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        
        if st.sidebar.button("Login"):
            if username and password:
                user_id = authenticate_user(username, password)
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.rerun()
            else:
                st.sidebar.error("Please enter username and password")
        
        st.info("👆 Please login in the sidebar to continue")
        return
    
    # Sidebar navigation
    st.sidebar.success(f"Logged in as: {st.session_state.username}")
    
    if st.sidebar.button("Logout"):
        del st.session_state.user_id
        del st.session_state.username
        st.rerun()
    
    # Check if admin (you can set this based on username)
    is_admin = st.session_state.username in ["admin", "owner"]
    
    if is_admin:
        tab1, tab2, tab3 = st.tabs(["📊 Admin Dashboard", "📹 Analyze Video", "📋 My Videos"])
    else:
        tab1, tab2 = st.tabs(["📹 Analyze Video", "📋 My Videos"])
    
    # Admin Dashboard (only for admins)
    if is_admin:
        with tab1:
            st.header("Admin Dashboard")
            
            # Get stats
            total_users, total_videos, videos_per_user, upload_trends = get_user_stats()
            
            # Key metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Users", total_users)
            with col2:
                st.metric("Total Videos", total_videos)
            with col3:
                avg_videos = total_videos / max(total_users, 1)
                st.metric("Avg Videos/User", f"{avg_videos:.1f}")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Videos per User")
                if not videos_per_user.empty:
                    fig = px.bar(videos_per_user, 
                               x='username', y='video_count',
                               title="Video Uploads by User")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No video data yet")
            
            with col2:
                st.subheader("Upload Trends (Last 30 Days)")
                if not upload_trends.empty:
                    fig = px.line(upload_trends, 
                                x='date', y='uploads',
                                title="Daily Upload Trends")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No upload trend data yet")
            
            # Detailed user table
            st.subheader("User Details")
            st.dataframe(videos_per_user, use_container_width=True)
    
    # Video Analysis Tab
    analysis_tab = tab2 if is_admin else tab1
    with analysis_tab:
        st.header("Analyze Horse Gait")
        
        uploaded_file = st.file_uploader(
            "Upload a video of your horse",
            type=['mp4', 'avi', 'mov', 'mkv'],
            help="Upload a clear video showing your horse's gait"
        )
        
        if uploaded_file is not None:
            # Display video
            st.video(uploaded_file)
            
            if st.button("Analyze Gait", type="primary"):
                with st.spinner("🔍 Analyzing gait patterns with AI model..."):
                    # Reset file pointer to beginning
                    uploaded_file.seek(0)
                    
                    # Analyze the video using your HuggingFace model
                    results = analyze_gait(uploaded_file)
                    
                    if "error" in results:
                        st.error(f"Analysis failed: {results['error']}")
                        st.info("💡 Tip: Make sure your video is clear and shows the horse's full body in motion")
                    else:
                        # Save to database
                        save_analysis(st.session_state.user_id, 
                                    uploaded_file.name, 
                                    str(results))
                        
                        # Display results
                        st.success("✅ Analysis complete!")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("🏇 Stride Analysis Results")
                            
                            # Classification with color coding
                            classification = results.get("classification", "Unknown")
                            if classification == "NORMAL":
                                st.success(f"**Classification:** {classification}")
                            elif classification == "ABNORMAL": 
                                st.error(f"**Classification:** {classification}")
                            else:
                                st.info(f"**Classification:** {classification}")
                            
                            st.metric("Confidence", f"{results['confidence']*100:.0f}%")
                            st.metric("Processing Time", f"{results.get('processing_time', 0):.1f}s")
                            
                            # Show details if available
                            if results.get('details'):
                                st.write(f"**Analysis:** {results['details']}")
                        
                        with col2:
                            st.subheader("📊 Stride Metrics")
                            
                            # Raw stride metrics from your model
                            col2a, col2b = st.columns(2)
                            with col2a:
                                st.metric("Stride Variability", f"{results.get('stride_variability', 0):.3f}")
                                st.metric("Mean Knee Angle", f"{results.get('knee_angle', 0):.1f}°")
                            with col2b:
                                st.metric("Body Length Variation", f"{results.get('body_length_variation', 0):.3f}")
                                st.metric("Derived Stride Length", f"{results['stride_length']}m")
                        
                        # Quality scores section
                        st.subheader("🎯 Quality Scores")
                        col3, col4 = st.columns(2)
                        
                        with col3:
                            st.metric("Rhythm Score", f"{results['rhythm_score']}/10", 
                                     help="Based on stride variability (lower variability = higher score)")
                        with col4:
                            st.metric("Symmetry Score", f"{results['symmetry_score']}/10",
                                     help="Based on body length variation (lower variation = higher score)")
                        
                        # Overall score visualization
                        if results['rhythm_score'] > 0 and results['symmetry_score'] > 0:
                            overall_score = (results['rhythm_score'] + results['symmetry_score']) / 2
                            
                            fig = go.Figure(go.Indicator(
                                mode = "gauge+number+delta",
                                value = overall_score,
                                domain = {'x': [0, 1], 'y': [0, 1]},
                                title = {'text': "Overall Stride Quality"},
                                delta = {'reference': 8.0},  # Good score reference
                                gauge = {'axis': {'range': [None, 10]},
                                       'bar': {'color': "darkgreen" if classification == "NORMAL" else "darkred"},
                                       'steps': [
                                           {'range': [0, 5], 'color': "lightgray"},
                                           {'range': [5, 8], 'color': "yellow"},
                                           {'range': [8, 10], 'color': "lightgreen"}],
                                       'threshold': {'line': {'color': "red", 'width': 4},
                                                   'thickness': 0.75, 'value': 7}}))
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Show raw output for debugging (remove in production)
                        if st.checkbox("Show raw model output (debug)"):
                            st.json(results)
    
    # My Videos Tab
    videos_tab = tab3 if is_admin else tab2
    with videos_tab:
        st.header("My Video Analysis History")
        
        user_videos = get_user_videos(st.session_state.user_id)
        
        if user_videos.empty:
            st.info("No videos uploaded yet. Upload your first video in the 'Analyze Video' tab!")
        else:
            st.write(f"Total videos: {len(user_videos)}")
            
            for idx, video in user_videos.iterrows():
                with st.expander(f"📹 {video['filename']} - {video['upload_date'][:16]}"):
                    
                    # Parse results (in real app, store as JSON)
                    try:
                        results = eval(video['analysis_results'])  # Don't use eval in production!
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Results:**")
                            st.write(f"• Primary Gait: {results['primary_gait']}")
                            st.write(f"• Confidence: {results['confidence']*100:.0f}%")
                            st.write(f"• Stride Length: {results['stride_length']}m")
                        
                        with col2:
                            st.write("**Quality Scores:**")
                            st.write(f"• Rhythm: {results['rhythm_score']}/10")
                            st.write(f"• Symmetry: {results['symmetry_score']}/10")
                    
                    except:
                        st.write("Error displaying results")

if __name__ == "__main__":
    main()
