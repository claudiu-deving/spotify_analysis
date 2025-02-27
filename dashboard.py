# spotify_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import glob
import sys
from datetime import datetime

# Import the SpotifyAnalyzer class
from spotify_analyzer import SpotifyAnalyzer

def main():
    st.set_page_config(
        page_title="Spotify Listening Dashboard",
        page_icon="🎵",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🎵 Spotify Listening Dashboard")
    st.write("Analyze your Spotify listening habits with this interactive dashboard")
    
    # Sidebar for file selection
    st.sidebar.header("Data Selection")
    
    # File uploader for JSON files
    uploaded_files = st.sidebar.file_uploader(
        "Upload your Spotify JSON files", 
        type=["json"], 
        accept_multiple_files=True
    )
    
    if not uploaded_files:
        st.info("Please upload your Spotify data files to begin analysis.")
        st.markdown("""
        ### How to get your Spotify data:
        1. Go to your Spotify account page: [Privacy Settings](https://www.spotify.com/account/privacy/)
        2. Click on "Request your data"
        3. You'll receive an email with a download link within a few days
        4. Extract the ZIP file and look for files named like "StreamingHistory0.json"
        5. Upload those files here!
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
        
        # Basic stats section
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
        
        # Listening Patterns
        st.header("📅 Listening Patterns")
        
        tab1, tab2, tab3, tab4 = st.tabs(["By Hour", "By Day", "By Month", "Heatmap"])
        
        time_data = analyzer.listening_by_time()
        
        with tab1:
            # Hourly pattern
            hourly_df = pd.DataFrame(time_data["hourly"]).reset_index()
            hourly_df.columns = ["Hour", "Minutes"]
            
            fig = px.bar(
                hourly_df, 
                x="Hour", 
                y="Minutes",
                title="Listening by Hour of Day"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("This shows when during the day you listen to music the most.")
        
        with tab2:
            # Daily pattern
            daily_df = pd.DataFrame(time_data["daily"]).reset_index()
            daily_df.columns = ["Day", "Minutes"]
            
            fig = px.bar(
                daily_df, 
                x="Day", 
                y="Minutes",
                title="Listening by Day of Week"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("This shows which days of the week you listen to music the most.")
        
        with tab3:
            # Monthly pattern
            monthly_df = time_data["monthly"]
            
            # Create a figure
            fig = go.Figure()
            
            # Plot each year as a separate line
            for year in sorted(monthly_df["year"].unique()):
                year_data = monthly_df[monthly_df["year"] == year]
                
                # Sort by month
                year_data = year_data.sort_values("month")
                
                fig.add_trace(go.Scatter(
                    x=year_data["month_name"], 
                    y=year_data["hours_played"],
                    mode="lines+markers",
                    name=str(year)
                ))
            
            fig.update_layout(
                title="Listening by Month",
                xaxis_title="Month",
                yaxis_title="Hours",
                legend_title="Year",
                xaxis={
                    'categoryorder': 'array',
                    'categoryarray': [
                        'January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December'
                    ]
                }
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("This shows your listening patterns throughout the year(s).")
        
        with tab4:
            # Heatmap
            heatmap_data = analyzer.listening_heatmap_data()
            
            # Convert to format needed for Plotly
            heatmap_df = heatmap_data.reset_index()
            heatmap_df = pd.melt(heatmap_df, id_vars="index", var_name="hour", value_name="minutes")
            heatmap_df.columns = ["day", "hour", "minutes"]
            
            fig = px.density_heatmap(
                heatmap_df,
                x="hour",
                y="day",
                z="minutes",
                title="Listening Activity Heatmap (Hour × Day)",
                labels={"minutes": "Minutes", "hour": "Hour of Day", "day": "Day of Week"},
                category_orders={
                    "day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                }
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("This heatmap shows your listening patterns throughout the week.")
        
        # Listening Streaks
        st.header("🔄 Listening Streaks")
        
        streaks = analyzer.listening_streaks()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Days with Activity", f"{streaks['days_with_activity']} days")
        
        with col2:
            st.metric("Activity Ratio", f"{streaks['activity_ratio']:.1%}")
        
        with col3:
            st.metric("Longest Streak", f"{streaks['longest_streak']} days")
        
        if streaks['longest_streak_start'] and streaks['longest_streak'] > 1:
            st.success(
                f"Your longest listening streak was {streaks['longest_streak']} days "
                f"from {streaks['longest_streak_start']} to {streaks['longest_streak_end']}"
            )
        
        # Artist diversity
        st.header("🌈 Artist Diversity")
        
        diversity = analyzer.artist_diversity()
        
        # Monthly unique artists
        monthly_unique_df = pd.DataFrame(diversity["monthly_unique"]).reset_index()
        monthly_unique_df.columns = ["Year", "Month", "Unique Artists"]
        monthly_unique_df["YearMonth"] = monthly_unique_df["Year"].astype(str) + "-" + monthly_unique_df["Month"].astype(str).str.zfill(2)
        
        # Monthly discovery ratio
        discovery_df = pd.DataFrame(diversity["monthly_discovery_ratio"]).reset_index()
        discovery_df.columns = ["Year", "Month", "Discovery Ratio"]
        discovery_df["YearMonth"] = discovery_df["Year"].astype(str) + "-" + discovery_df["Month"].astype(str).str.zfill(2)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                monthly_unique_df, 
                x="YearMonth", 
                y="Unique Artists",
                title="Unique Artists per Month"
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                discovery_df, 
                x="YearMonth", 
                y="Discovery Ratio",
                title="New Artist Discovery Ratio",
                range_y=[0, 1]
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        st.write("The discovery ratio shows the proportion of new artists you listened to each month.")
        
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