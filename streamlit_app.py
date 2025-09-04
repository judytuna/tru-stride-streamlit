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
import re

def reset_user_password_from_env(username):
    """
    Reset a user's password using environment variables
    Expected env vars: ADMIN_PASSWORD, EPONA01_PASSWORD
    """
    env_var_name = f"{username.upper()}_PASSWORD"
    new_password = os.getenv(env_var_name)

    if not new_password:
        return False, f"Environment variable {env_var_name} not found"

    conn = sqlite3.connect('horse_gait.db')
    c = conn.cursor()

    # Check if user exists
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = c.fetchone()

    if not user:
        conn.close()
        return False, f"User {username} not found"

    # Hash the new password
    password_hash = hashlib.sha256(new_password.encode()).hexdigest()

    # Update password
    c.execute("UPDATE users SET password_hash = ? WHERE username = ?", (password_hash, username))
    conn.commit()
    conn.close()

    return True, f"Password updated successfully for {username}"

# Database setup
def init_db():
    conn = sqlite3.connect('horse_gait.db')
    c = conn.cursor()

    # Create user table with full schema
    c.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT,
                    created_at TIMESTAMP, is_admin BOOLEAN DEFAULT 0,
                    password_hash TEXT)''')

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
        SELECT u.username, COUNT(v.id) as video_count, u.is_admin
        FROM users u
        LEFT JOIN videos v ON u.id = v.user_id
        GROUP BY u.id, u.username, u.is_admin
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
    """
    Enhanced authentication with password hashing and admin roles
    """
    conn = sqlite3.connect('horse_gait.db')
    c = conn.cursor()

    # Hash the provided password
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    # Check if user exists with correct password
    c.execute("SELECT id, is_admin FROM users WHERE username = ? AND password_hash = ?",
              (username, password_hash))
    user_data = c.fetchone()

    if user_data:
        user_id, is_admin = user_data
        conn.close()
        return user_id, bool(is_admin)

    conn.close()
    return None, False

def create_user(username, email, password):
    """
    Create a new user account
    """
    conn = sqlite3.connect('horse_gait.db')
    c = conn.cursor()

    # Check if username already exists
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return None, "Username already exists"

    # Hash the password
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    try:
        # Create new user
        c.execute("INSERT INTO users (username, email, created_at, is_admin, password_hash) VALUES (?, ?, ?, ?, ?)",
                 (username, email, datetime.now(), 0, password_hash))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return user_id, None
    except sqlite3.IntegrityError:
        conn.close()
        return None, "Username already exists"

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

def get_all_users():
    conn = sqlite3.connect('horse_gait.db')
    users = pd.read_sql_query('''
        SELECT u.id, u.username, u.email, u.created_at, u.is_admin,
               COUNT(v.id) as video_count
        FROM users u
        LEFT JOIN videos v ON u.id = v.user_id
        GROUP BY u.id, u.username, u.email, u.created_at, u.is_admin
        ORDER BY u.created_at DESC
    ''', conn)
    conn.close()
    return users

def toggle_admin_status(user_id, make_admin):
    conn = sqlite3.connect('horse_gait.db')
    c = conn.cursor()
    c.execute("UPDATE users SET is_admin = ? WHERE id = ?", (1 if make_admin else 0, user_id))
    conn.commit()
    conn.close()

def analyze_gait(video_file):
    """
    Call your HuggingFace Gradio app for gait analysis
    """
    try:
        from gradio_client import Client

        # Connect to your Gradio space
        client = Client("judytuna/tru-stride-analyzer")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(video_file.read())
            tmp_file_path = tmp_file.name

        # Call your Gradio app using the correct endpoint
        # Use gradio_client.handle_file() to properly format the file
        from gradio_client import handle_file

        result = client.predict(
            handle_file(tmp_file_path),
            api_name="/process_video_upload"
        )

        # Clean up temp file
        os.unlink(tmp_file_path)

        # Parse the result from your Gradio app
        # You'll need to adjust this based on what your model returns
        if isinstance(result, tuple):
            # If your Gradio returns multiple outputs
            analysis_text = result[0] if result else "No analysis available"
        else:
            analysis_text = str(result)

        # Parse your actual results into structured format
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
st.set_page_config(page_title="Tru-Stride", page_icon="🐎", layout="wide")

# Main app
def main():
    st.title("🐎 Tru-Stride")

    # Authentication
    if 'user_id' not in st.session_state:
        st.sidebar.header("🔐 Authentication")

        # Toggle between login and signup
        auth_mode = st.sidebar.radio("Choose action:", ["Login", "Sign Up Here"])

        if auth_mode == "Login":
            st.sidebar.subheader("Login")
            username = st.sidebar.text_input("Username", key="login_username")
            password = st.sidebar.text_input("Password", type="password", key="login_password")

            if st.sidebar.button("Login"):
                if username and password:
                    user_id, is_admin = authenticate_user(username, password)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.session_state.is_admin = is_admin
                        st.rerun()
                    else:
                        st.sidebar.error("Invalid username or password")
                else:
                    st.sidebar.error("Please enter username and password")

        else:  # Sign Up
            st.sidebar.subheader("Sign Up Here")
            new_username = st.sidebar.text_input("Choose Username", key="signup_username")
            new_email = st.sidebar.text_input("Email Address", key="signup_email")
            new_password = st.sidebar.text_input("Choose Password", type="password", key="signup_password")
            confirm_password = st.sidebar.text_input("Confirm Password", type="password", key="confirm_password")

            if st.sidebar.button("Sign Up"):
                if new_username and new_email and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.sidebar.error("Passwords do not match")
                    elif "@" not in new_email or "." not in new_email:
                        st.sidebar.error("Please enter a valid email address")
                    else:
                        user_id, error = create_user(new_username, new_email, new_password)
                        if user_id:
                            # Auto-login the new user
                            st.session_state.user_id = user_id
                            st.session_state.username = new_username
                            st.session_state.is_admin = False
                            st.sidebar.success("Account created successfully! Welcome!")
                            st.rerun()
                        else:
                            st.sidebar.error(error)
                else:
                    st.sidebar.error("Please fill in all fields")

        # Show login/signup prompt
        st.info("👆 Please login or sign up in the sidebar to continue")
        return

    # Sidebar navigation
    st.sidebar.success(f"Logged in as: {st.session_state.username}")
    if st.session_state.get('is_admin', False):
        st.sidebar.info("👑 Admin Access")

    if st.sidebar.button("Logout"):
        for key in ['user_id', 'username', 'is_admin']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # Check admin status from database
    is_admin = st.session_state.get('is_admin', False)

    if is_admin:
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Admin Dashboard", "👥 User Management", "📹 Analyze Video", "📋 My Videos"])
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
            st.subheader("User Activity Overview")
            # Add admin indicator to the table
            display_df = videos_per_user.copy()
            display_df['Role'] = display_df['is_admin'].apply(lambda x: '👑 Admin' if x else '👤 User')
            st.dataframe(display_df[['username', 'Role', 'video_count']], use_container_width=True)

        # User Management Tab (Admin only)
        with tab2:
            if is_admin:
                st.header("👥 User Management")

                # Get all users
                all_users = get_all_users()

                if not all_users.empty:
                    st.subheader("All Users")

                    for idx, user in all_users.iterrows():
                        with st.expander(f"{'👑' if user['is_admin'] else '👤'} {user['username']} ({user['video_count']} videos)"):

                            col1, col2 = st.columns([3, 1])

                            with col1:
                                st.write(f"**Email:** {user['email']}")
                                st.write(f"**Joined:** {user['created_at'][:10]}")
                                st.write(f"**Videos:** {user['video_count']}")
                                st.write(f"**Status:** {'👑 Admin' if user['is_admin'] else '👤 Regular User'}")

                            with col2:
                                # Don't allow demoting yourself
                                if user['username'] != st.session_state.username:
                                    if user['is_admin']:
                                        if st.button(f"Remove Admin", key=f"demote_{user['id']}"):
                                            toggle_admin_status(user['id'], False)
                                            st.success(f"Removed admin access from {user['username']}")
                                            st.rerun()
                                    else:
                                        if st.button(f"Make Admin", key=f"promote_{user['id']}"):
                                            toggle_admin_status(user['id'], True)
                                            st.success(f"Granted admin access to {user['username']}")
                                            st.rerun()
                                else:
                                    st.info("(You)")

                    # Summary stats
                    admin_count = all_users['is_admin'].sum()
                    regular_count = len(all_users) - admin_count

                    st.subheader("User Summary")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("👑 Admins", admin_count)
                    with col2:
                        st.metric("👤 Regular Users", regular_count)
                    with col3:
                        st.metric("📊 Total Users", len(all_users))

                else:
                    st.info("No users found")

    # Video Analysis Tab
    analysis_tab = tab3 if is_admin else tab1
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
    videos_tab = tab4 if is_admin else tab2
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