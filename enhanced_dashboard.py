# enhanced_dashboard.py
"""
Enhanced Spotify Dashboard with new analytical features.
This version extends the original dashboard with genre, audio features, session, and context analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import numpy as np
from datetime import datetime
import json

# Import the enhanced SpotifyAnalyzer
from spotify_analyzer import SpotifyAnalyzer
from spotify_features import enhance_spotify_analyzer

# Enhance the SpotifyAnalyzer class with new features
enhance_spotify_analyzer()

def main():
    st.set_page_config(
        page_title="Enhanced Spotify Listening Dashboard",
        page_icon="🎵",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🎵 Enhanced Spotify Listening Dashboard")
    st.write("Analyze your Spotify listening habits with advanced insights")
    
    # Sidebar for file selection and API connection
    st.sidebar.header("Data Selection")
    
    # File uploader for JSON files
    uploaded_files = st.sidebar.file_uploader(
        "Upload your Spotify JSON files", 
        type=["json"], 
        accept_multiple_files=True
    )
    
    # Spotify API connection (optional)
    st.sidebar.header("Spotify API Connection (Optional)")
    st.sidebar.markdown("""
    Some advanced features require Spotify API access.  
    You can get free API credentials at the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
    """)
    
    client_id = st.sidebar.text_input("Spotify Client ID", type="password")
    client_secret = st.sidebar.text_input("Spotify Client Secret", type="password")
    
    if not uploaded_files:
        st.info("Please upload your Spotify data files to begin analysis.")
        st.markdown("""
        ### How to get your Spotify data:
        1. Go to your Spotify account page: [Privacy Settings](https://www.spotify.com/account/privacy/)
        2. Click on "Request your data"
        3. You'll receive an email with a download link within a few days
        4. Extract the ZIP file and look for files named like "StreamingHistory0.json"
        5. Upload those files here!
        
        ### New Enhanced Features:
        - 🎸 **Genre Analysis**: Discover your most listened genres and genre diversity
        - 🎛️ **Audio Features Analysis**: Explore the acoustic characteristics of your music
        - ⏱️ **Listening Session Analysis**: Understand your listening behavior patterns
        - 🔮 **Context Prediction**: Identify when and why you listen to music
        
        Note: Genre and audio feature analysis require Spotify API credentials
        """)
        return
    
    # Save uploaded files temporarily
    temp_dir = "temp_spotify_data"
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_paths = []
    for uploaded_file in uploaded_files:
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        temp_paths.append(file_path)
    
    # Initialize analyzer with uploaded files
    try:
        analyzer = SpotifyAnalyzer(temp_paths)
        
        # Connect to Spotify API if credentials are provided
        api_connected = False
        if client_id and client_secret:
            with st.spinner("Connecting to Spotify API..."):
                try:
                    analyzer.connect_to_spotify_api(client_id, client_secret)
                    api_connected = True
                    st.sidebar.success("✅ Connected to Spotify API")
                except Exception as e:
                    st.sidebar.error(f"Error connecting to Spotify API: {str(e)}")
        
        # Create tabs for different analysis sections
        tab_basic, tab_genres, tab_audio, tab_sessions, tab_context = st.tabs([
            "Basic Stats", 
            "Genre Analysis", 
            "Audio Features", 
            "Listening Sessions", 
            "Listening Context"
        ])
        
        # =====================
        # BASIC STATS TAB
        # =====================
        with tab_basic:
            st.header("📊 Listening Overview")
            stats = analyzer.basic_stats()
            
            # Create three columns for stats
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Listening Time", f"{stats['total_listening_hours']:.1f} hours")
                st.metric("Total Tracks Played", f"{stats['total_songs_played']:,}")
            
            with col2:
                st.metric("Unique Artists", f"{stats['unique_artists']:,}")
                st.metric("Unique Tracks", f"{stats['unique_tracks']:,}")
            
            with col3:
                st.metric("Daily Average", f"{stats['avg_daily_hours'] * 60:.1f} minutes")
                st.metric("Data Period", f"{stats['date_range_days']} days")
            
            # Show data date range
            st.info(f"Data from {stats['start_date']} to {stats['end_date']}")
            
            # Top Artists and Tracks
            st.header("🎤 Top Artists & Tracks")
            
            tab1, tab2 = st.tabs(["Top Artists", "Top Tracks"])
            
            with tab1:
                top_n = st.slider("Number of top artists to display", 5, 20, 10, key="artist_slider")
                top_artists = analyzer.top_artists(top_n)
                
                # Convert to dataframes for Plotly
                artists_by_count = pd.DataFrame(top_artists["by_count"]).reset_index()
                artists_by_count.columns = ["Artist", "Play Count"]
                
                artists_by_time = pd.DataFrame(top_artists["by_time"]).reset_index()
                artists_by_time.columns = ["Artist", "Hours"]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(
                        artists_by_count, 
                        x="Play Count", 
                        y="Artist", 
                        orientation='h',
                        title="By Play Count"
                    )
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.bar(
                        artists_by_time, 
                        x="Hours", 
                        y="Artist", 
                        orientation='h',
                        title="By Hours Listened"
                    )
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                top_n = st.slider("Number of top tracks to display", 5, 20, 10, key="track_slider")
                top_tracks = analyzer.top_tracks(top_n)
                
                # Convert to dataframes for Plotly
                tracks_by_count = pd.DataFrame(top_tracks["by_count"]).reset_index()
                tracks_by_count.columns = ["Track", "Artist", "Play Count"]
                tracks_by_count["Label"] = tracks_by_count["Track"] + " - " + tracks_by_count["Artist"]
                
                tracks_by_time = pd.DataFrame(top_tracks["by_time"]).reset_index()
                tracks_by_time.columns = ["Track", "Artist", "Hours"]
                tracks_by_time["Label"] = tracks_by_time["Track"] + " - " + tracks_by_time["Artist"]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(
                        tracks_by_count, 
                        x="Play Count", 
                        y="Label", 
                        orientation='h',
                        title="By Play Count"
                    )
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.bar(
                        tracks_by_time, 
                        x="Hours", 
                        y="Label", 
                        orientation='h',
                        title="By Hours Listened"
                    )
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
            
            # Show original dashboard sections (patterns, streaks, diversity)
            # (Code from original dashboard_main function...)
        
        # =====================
        # GENRE ANALYSIS TAB
        # =====================
        with tab_genres:
            st.header("🎸 Genre Analysis")
            
            if not api_connected:
                st.warning("Genre analysis requires Spotify API connection. Please provide your API credentials in the sidebar.")
            else:
                # Check if genre data already exists, if not, fetch it
                if 'genres' not in analyzer.df.columns:
                    with st.spinner("Fetching genre data from Spotify API..."):
                        try:
                            analyzer.enrich_with_genres()
                            st.success("Successfully retrieved genre data!")
                        except Exception as e:
                            st.error(f"Error fetching genre data: {str(e)}")
                            st.info("This usually happens if your data export doesn't include track IDs. Try requesting a newer data export from Spotify.")
                
                # If we have genre data, show analysis
                if 'genres' in analyzer.df.columns:
                    # Top Genres
                    st.subheader("Top Genres")
                    top_n = st.slider("Number of top genres to display", 5, 20, 10, key="genre_slider")
                    
                    with st.spinner("Analyzing genre data..."):
                        top_genres = analyzer.top_genres(limit=top_n)
                        
                        # Convert to dataframes for Plotly
                        genres_by_count = pd.DataFrame(top_genres["by_count"]).reset_index()
                        genres_by_count.columns = ["Genre", "Play Count"]
                        
                        genres_by_time = pd.DataFrame(top_genres["by_time"]).reset_index()
                        genres_by_time.columns = ["Genre", "Hours"]
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig = px.bar(
                                genres_by_count, 
                                x="Play Count", 
                                y="Genre", 
                                orientation='h',
                                title="Top Genres by Play Count"
                            )
                            fig.update_layout(yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            fig = px.bar(
                                genres_by_time, 
                                x="Hours", 
                                y="Genre", 
                                orientation='h',
                                title="Top Genres by Hours Listened"
                            )
                            fig.update_layout(yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Genre Diversity
                    st.subheader("Genre Diversity")
                    
                    with st.spinner("Calculating genre diversity..."):
                        diversity = analyzer.genre_diversity()
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Total Unique Genres", diversity["unique_genres_count"])
                            
                            # Show all genres as tags
                            st.markdown("### All Genres")
                            genre_html = ""
                            for genre in sorted(diversity["all_genres"]):
                                genre_html += f'<span style="background-color: #9c89ff; margin: 2px; padding: 2px 8px; border-radius: 10px; color: white; display: inline-block;">{genre}</span>'
                            st.markdown(f'<div style="max-height: 200px; overflow-y: auto;">{genre_html}</div>', unsafe_allow_html=True)
                        
                        # Monthly unique genres chart
                        with col2:
                            if not diversity["monthly_unique"].empty:
                                monthly_unique_df = pd.DataFrame(diversity["monthly_unique"]).reset_index()
                                monthly_unique_df.columns = ["Year", "Month", "Unique Genres"]
                                monthly_unique_df["YearMonth"] = monthly_unique_df["Year"].astype(str) + "-" + monthly_unique_df["Month"].astype(str).str.zfill(2)
                                
                                fig = px.bar(
                                    monthly_unique_df, 
                                    x="YearMonth", 
                                    y="Unique Genres",
                                    title="Unique Genres per Month"
                                )
                                fig.update_layout(xaxis_tickangle=-45)
                                st.plotly_chart(fig, use_container_width=True)
                    
                    # Genre Discovery
                    st.subheader("Genre Discovery")
                    
                    if not diversity["monthly_discovery_ratio"].empty:
                        discovery_df = pd.DataFrame(diversity["monthly_discovery_ratio"]).reset_index()
                        discovery_df.columns = ["Year", "Month", "Discovery Ratio"]
                        discovery_df["YearMonth"] = discovery_df["Year"].astype(str) + "-" + discovery_df["Month"].astype(str).str.zfill(2)
                        
                        fig = px.bar(
                            discovery_df, 
                            x="YearMonth", 
                            y="Discovery Ratio",
                            title="New Genre Discovery Ratio by Month",
                            range_y=[0, 1]
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.info("The discovery ratio shows the proportion of new genres you listened to each month. A higher value means you explored more new genres.")
        
        # =====================
        # AUDIO FEATURES TAB
        # =====================
        with tab_audio:
            st.header("🎛️ Audio Features Analysis")
            
            if not api_connected:
                st.warning("Audio features analysis requires Spotify API connection. Please provide your API credentials in the sidebar.")
            else:
                # Check if audio features already exist, if not, fetch them
                required_features = ['energy', 'danceability', 'valence', 'tempo']
                if not any(feature in analyzer.df.columns for feature in required_features):
                    with st.spinner("Fetching audio features from Spotify API..."):
                        try:
                            analyzer.enrich_with_audio_features()
                            st.success("Successfully retrieved audio features!")
                        except Exception as e:
                            st.error(f"Error fetching audio features: {str(e)}")
                            st.info("This usually happens if your data export doesn't include track IDs. Try requesting a newer data export from Spotify.")
                
                # If we have audio features, show analysis
                if any(feature in analyzer.df.columns for feature in required_features):
                    # Average Audio Features
                    st.subheader("Average Audio Features")
                    
                    with st.spinner("Calculating average audio features..."):
                        avg_features = analyzer.average_audio_features()
                        
                        # Select features to display
                        display_features = ['danceability', 'energy', 'valence', 'acousticness', 
                                          'instrumentalness', 'liveness', 'speechiness']
                        available_display = [f for f in display_features if f in avg_features and avg_features[f] is not None]
                        
                        # Create radar chart data
                        if available_display:
                            radar_data = {
                                'Feature': available_display,
                                'Value': [avg_features[f] for f in available_display]
                            }
                            radar_df = pd.DataFrame(radar_data)
                            
                            # Create radar chart using plotly
                            fig = px.line_polar(
                                radar_df, 
                                r='Value', 
                                theta='Feature', 
                                line_close=True,
                                range_r=[0, 1]
                            )
                            fig.update_traces(fill='toself')
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Display feature explanations
                            st.markdown("### Audio Feature Explanations")
                            feature_explanations = {
                                'danceability': 'How suitable the track is for dancing (0.0 = least danceable, 1.0 = most danceable)',
                                'energy': 'Intensity and activity (0.0 = calm, 1.0 = energetic)',
                                'valence': 'Musical positiveness (0.0 = sad/negative, 1.0 = happy/positive)',
                                'acousticness': 'Confidence that the track is acoustic (0.0 = electric, 1.0 = acoustic)',
                                'instrumentalness': 'Predicts if a track has no vocals (0.0 = vocal, 1.0 = instrumental)',
                                'liveness': 'Presence of audience (0.0 = studio recording, 1.0 = live performance)',
                                'speechiness': 'Presence of spoken words (0.0 = music, 1.0 = speech)'
                            }
                            
                            for feature in available_display:
                                st.markdown(f"**{feature.capitalize()}**: {feature_explanations.get(feature, '')}")
                    
                    # Mood Analysis
                    st.subheader("Mood Analysis")
                    
                    with st.spinner("Analyzing mood patterns..."):
                        # Classify moods if not already done
                        if 'mood' not in analyzer.df.columns:
                            analyzer.classify_moods()
                        
                        mood_data = analyzer.mood_analysis()
                        
                        if not mood_data["by_count"].empty:
                            # Mood distribution
                            mood_counts = pd.DataFrame(mood_data["by_count"]).reset_index()
                            mood_counts.columns = ["Mood", "Count"]
                            
                            # Mood by time
                            mood_time = pd.DataFrame(mood_data["by_time"]).reset_index()
                            mood_time.columns = ["Mood", "Minutes"]
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                fig = px.pie(
                                    mood_counts, 
                                    values='Count', 
                                    names='Mood',
                                    title="Mood Distribution by Track Count",
                                    color_discrete_map={
                                        'Happy': '#4CAF50',
                                        'Sad': '#2196F3',
                                        'Angry': '#FF5722',
                                        'Relaxed': '#8BC34A'
                                    }
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            
                            with col2:
                                fig = px.pie(
                                    mood_time, 
                                    values='Minutes', 
                                    names='Mood',
                                    title="Mood Distribution by Listening Time",
                                    color_discrete_map={
                                        'Happy': '#4CAF50',
                                        'Sad': '#2196F3',
                                        'Angry': '#FF5722',
                                        'Relaxed': '#8BC34A'
                                    }
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Mood explanation
                            st.markdown("""
                            ### Mood Classification
                            Tracks are classified into moods based on their energy and valence (musical positiveness):
                            - **Happy**: High energy + high valence (energetic and positive)
                            - **Angry**: High energy + low valence (energetic but negative)
                            - **Relaxed**: Low energy + high valence (calm and positive)
                            - **Sad**: Low energy + low valence (calm and negative)
                            """)
                        
                        # Mood by hour heatmap
                        if "by_hour" in mood_data and not mood_data["by_hour"].empty:
                            st.subheader("Mood by Hour of Day")
                            
                            # Convert to format needed for Plotly
                            hour_mood_df = mood_data["by_hour"].reset_index()
                            hour_mood_melted = pd.melt(hour_mood_df, id_vars='hour', var_name='Mood', value_name='Count')
                            
                            fig = px.density_heatmap(
                                hour_mood_melted,
                                x='hour',
                                y='Mood',
                                z='Count',
                                title="When You Listen to Different Moods",
                                labels={"hour": "Hour of Day", "Count": "Number of Tracks"}
                            )
                            fig.update_layout(yaxis_categoryorder='category descending')
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Audio Features Over Time
                    st.subheader("Audio Features Over Time")
                    
                    # Feature selector
                    feature_options = [f for f in ['energy', 'danceability', 'valence', 'acousticness'] 
                                      if f in analyzer.df.columns]
                    if feature_options:
                        selected_feature = st.selectbox(
                            "Select audio feature to track", 
                            options=feature_options,
                            format_func=lambda x: x.capitalize()
                        )
                        
                        with st.spinner(f"Tracking {selected_feature} over time..."):
                            feature_over_time = analyzer.audio_features_over_time(selected_feature)
                            
                            if not feature_over_time.empty:
                                # Convert to dataframe for plotting
                                feature_df = pd.DataFrame(feature_over_time).reset_index()
                                feature_df.columns = ["Year", "Month", "Value"]
                                feature_df["YearMonth"] = feature_df["Year"].astype(str) + "-" + feature_df["Month"].astype(str).str.zfill(2)
                                
                                fig = px.line(
                                    feature_df,
                                    x="YearMonth",
                                    y="Value",
                                    title=f"{selected_feature.capitalize()} Over Time",
                                    labels={"Value": selected_feature.capitalize()},
                                    markers=True
                                )
                                fig.update_layout(xaxis_tickangle=-45)
                                st.plotly_chart(fig, use_container_width=True)
                                
                                st.info(f"This chart shows how your preference for {selected_feature} has changed over time.")
        
        # =====================
        # LISTENING SESSIONS TAB
        # =====================
        with tab_sessions:
            st.header("⏱️ Listening Session Analysis")
            
            # Session detection settings
            st.subheader("Session Detection")
            
            gap_threshold = st.slider(
                "Gap threshold (minutes between tracks to consider a new session)",
                min_value=5,
                max_value=60,
                value=30,
                step=5
            )
            
            with st.spinner("Detecting listening sessions..."):
                sessions = analyzer.detect_sessions(gap_threshold=gap_threshold)
                
                # Session count and stats
                if sessions:
                    st.success(f"Detected {len(sessions)} listening sessions with a {gap_threshold}-minute gap threshold")
                    
                    stats = analyzer.session_statistics()
                    
                    # Display session statistics in columns
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Sessions", stats['total_sessions'])
                    
                    with col2:
                        st.metric("Avg. Session Length", f"{stats['avg_session_length']:.1f} min")
                    
                    with col3:
                        st.metric("Avg. Tracks per Session", f"{stats['avg_tracks_per_session']:.1f}")
                    
                    # Session length distribution
                    st.subheader("Session Length Distribution")
                    
                    if stats['session_length_distribution']:
                        # Convert to DataFrame for plotting
                        length_dist = pd.DataFrame({
                            'Duration': list(stats['session_length_distribution'].keys()),
                            'Sessions': list(stats['session_length_distribution'].values())
                        })
                        
                        # Sort by duration categories
                        duration_order = ['0-15min', '15-30min', '30-60min', '60-120min', '120-240min', '240min+']
                        length_dist['Duration'] = pd.Categorical(
                            length_dist['Duration'], 
                            categories=duration_order, 
                            ordered=True
                        )
                        length_dist = length_dist.sort_values('Duration')
                        
                        fig = px.bar(
                            length_dist,
                            x='Duration',
                            y='Sessions',
                            title='Distribution of Session Lengths',
                            color_discrete_sequence=['#7c83fd']
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Session start times
                    st.subheader("When Do Your Sessions Start?")
                    
                    patterns = analyzer.session_patterns()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Hour distribution
                        hour_data = pd.DataFrame({
                            'Hour': list(patterns['by_hour'].keys()),
                            'Sessions': list(patterns['by_hour'].values())
                        })
                        
                        fig = px.bar(
                            hour_data,
                            x='Hour',
                            y='Sessions',
                            title='Sessions by Hour of Day',
                            color_discrete_sequence=['#7c83fd']
                        )
                        fig.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=2))
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Weekday distribution
                        weekday_data = pd.DataFrame({
                            'Weekday': list(patterns['by_weekday'].keys()),
                            'Sessions': list(patterns['by_weekday'].values())
                        })
                        
                        # Ensure correct weekday order
                        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        weekday_data['Weekday'] = pd.Categorical(
                            weekday_data['Weekday'], 
                            categories=day_order, 
                            ordered=True
                        )
                        weekday_data = weekday_data.sort_values('Weekday')
                        
                        fig = px.bar(
                            weekday_data,
                            x='Weekday',
                            y='Sessions',
                            title='Sessions by Day of Week',
                            color_discrete_sequence=['#7c83fd']
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Session content analysis
                    st.subheader("Session Content Analysis")
                    
                    content = analyzer.session_content_analysis()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Session types pie chart
                        if content["session_types"]:
                            type_data = pd.DataFrame({
                                'Type': list(content['session_types'].keys()),
                                'Count': list(content['session_types'].values())
                            })
                            
                            fig = px.pie(
                                type_data,
                                values='Count',
                                names='Type',
                                title='Session Types',
                                color_discrete_map={
                                    'single_artist': '#6200ea',
                                    'album_listening': '#3f51b5',
                                    'variety': '#00897b',
                                    'mixed': '#8d6e63'
                                }
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Artist continuity and diversity metrics
                        st.markdown("### Session Metrics")
                        
                        st.metric(
                            "Artist Continuity", 
                            f"{content['avg_artist_continuity']:.2f}",
                            help="Average proportion of consecutive tracks by the same artist"
                        )
                        
                        st.metric(
                            "Artist Diversity", 
                            f"{content['avg_unique_artists_ratio']:.2f}",
                            help="Average ratio of unique artists to total tracks in a session"
                        )
                        
                        st.markdown("""
                        #### Session Type Definitions
                        - **Single Artist**: All tracks by the same artist
                        - **Album Listening**: Consecutive tracks mostly by 1-2 artists
                        - **Variety**: Many different artists with few repeats
                        - **Mixed**: Other listening patterns
                        """)
        
        # =====================
        # LISTENING CONTEXT TAB
        # =====================
        with tab_context:
            st.header("🔮 Listening Context Prediction")
            
            # Add context categories
            st.markdown("""
            This feature predicts the likely context of your listening sessions based on time patterns and audio features.
            Contexts include:
            - **Workout**: High-energy music during typical exercise hours
            - **Commute**: Music during weekday commuting hours
            - **Work**: Moderate-energy music during working hours
            - **Party**: High-energy music on weekend evenings
            - **Relaxation**: Low-energy music in the evenings
            """)
            
            with st.spinner("Categorizing listening contexts..."):
                # Categorize contexts
                analyzer.categorize_listening_contexts()
                context_stats = analyzer.context_statistics()
                
                # Context distribution
                st.subheader("Listening Context Distribution")
                
                if not context_stats["distribution"].empty:
                    # Convert to DataFrame for plotting
                    context_dist = pd.DataFrame(context_stats["distribution"]).reset_index()
                    context_dist.columns = ["Context", "Proportion"]
                    
                    # Convert proportion to percentage
                    context_dist["Percentage"] = context_dist["Proportion"] * 100
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = px.pie(
                            context_dist,
                            values='Proportion',
                            names='Context',
                            title='Distribution of Listening Contexts',
                            color_discrete_map={
                                'workout': '#f44336',
                                'commute': '#ff9800',
                                'work': '#2196f3',
                                'party': '#e91e63',
                                'relaxation': '#4caf50',
                                'other': '#9e9e9e'
                            }
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        fig = px.bar(
                            context_dist,
                            x='Context',
                            y='Percentage',
                            title='Percentage of Listening by Context',
                            color='Context',
                            color_discrete_map={
                                'workout': '#f44336',
                                'commute': '#ff9800',
                                'work': '#2196f3',
                                'party': '#e91e63',
                                'relaxation': '#4caf50',
                                'other': '#9e9e9e'
                            }
                        )
                        fig.update_layout(yaxis_title="Percentage (%)")
                        st.plotly_chart(fig, use_container_width=True)
                
                # Context by time of day heatmap
                st.subheader("Context by Time of Day")
                
                if "by_hour" in context_stats and not context_stats["by_hour"].empty:
                    # Convert to format needed for Plotly
                    hour_context_df = context_stats["by_hour"].reset_index()
                    hour_context_melted = pd.melt(
                        hour_context_df, 
                        id_vars='hour', 
                        var_name='Context', 
                        value_name='Count'
                    )
                    
                    fig = px.density_heatmap(
                        hour_context_melted,
                        x='hour',
                        y='Context',
                        z='Count',
                        title="When Different Contexts Occur",
                        labels={"hour": "Hour of Day", "Count": "Number of Tracks"}
                    )
                    fig.update_layout(yaxis_categoryorder='category descending')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Context recommendations
                st.subheader("Music Suggestions by Context")
                
                # Context selector
                context_options = [c for c in ['workout', 'commute', 'work', 'party', 'relaxation'] 
                                  if c in context_stats["distribution"].index]
                
                if context_options:
                    selected_context = st.selectbox(
                        "Select a context to get track suggestions", 
                        options=context_options,
                        format_func=lambda x: x.capitalize()
                    )
                    
                    with st.spinner(f"Finding recommendations for {selected_context}..."):
                        suggestions = analyzer.suggest_for_context(selected_context, limit=10)
                        
                        if suggestions:
                            st.markdown(f"### Top tracks for {selected_context.capitalize()}")
                            
                            # Display suggestions as a table
                            suggestion_df = pd.DataFrame(suggestions)
                            suggestion_df.columns = ["Track", "Artist", "Times Played"]
                            
                            st.dataframe(suggestion_df, use_container_width=True)
                            
                            st.info("These suggestions are based on your most frequently played tracks in this context.")
                        else:
                            st.info(f"No specific suggestions available for {selected_context}. Try a different context.")
                
                # Context prediction demo
                st.subheader("Context Prediction Demo")
                st.markdown("Try predicting the context for a specific time and music style:")
                
                try:
                    # Train the predictor model
                    analyzer.train_context_predictor()
                    
                    # Create input form
                    with st.form("context_predictor"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            hour = st.number_input("Hour of day (0-23)", min_value=0, max_value=23, value=12)
                            weekday = st.selectbox(
                                "Day of week", 
                                options=range(7), 
                                format_func=lambda x: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][x]
                            )
                        
                        with col2:
                            if 'energy' in analyzer.df.columns:
                                energy = st.slider("Energy level", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
                            else:
                                energy = 0.5
                                
                            if 'tempo' in analyzer.df.columns:
                                tempo = st.slider("Tempo (BPM)", min_value=60, max_value=180, value=120, step=10)
                            else:
                                tempo = 120
                        
                        submit = st.form_submit_button("Predict Context")
                    
                    if submit:
                        # Create prediction kwargs based on available features
                        predict_kwargs = {'hour': hour, 'weekday': weekday}
                        if 'energy' in analyzer.df.columns:
                            predict_kwargs['energy'] = energy
                        if 'tempo' in analyzer.df.columns:
                            predict_kwargs['tempo'] = tempo
                        
                        # Make prediction
                        predicted = analyzer.predict_context(**predict_kwargs)
                        
                        # Display result
                        st.success(f"Predicted context: **{predicted.upper()}**")
                        
                        # Context explanation
                        context_explanations = {
                            'workout': "This is typical workout music - high energy at common exercise times.",
                            'commute': "This matches typical commute patterns during weekday rush hours.",
                            'work': "This is the kind of music people often listen to during work hours.",
                            'party': "This music and timing matches weekend party patterns.",
                            'relaxation': "This is typical evening relaxation music.",
                            'other': "This doesn't fit cleanly into a specific context pattern."
                        }
                        
                        st.info(context_explanations.get(predicted, ""))
                
                except Exception as e:
                    if "scikit-learn is required" in str(e):
                        st.warning("Context prediction requires scikit-learn. Install with: pip install scikit-learn")
                    else:
                        st.error(f"Error in context prediction: {str(e)}")
        
        # Clean up temporary files
        for file_path in temp_paths:
            try:
                os.remove(file_path)
            except:
                pass
            
    except Exception as e:
        st.error(f"Error analyzing data: {str(e)}")
        st.exception(e)
        
if __name__ == "__main__":
    main()