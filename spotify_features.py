# spotify_features.py
"""
Enhanced features for Spotify Analyzer.
This module extends the SpotifyAnalyzer class with new analytical capabilities.
"""

import pandas as pd
import numpy as np
from collections import Counter
from datetime import datetime, timedelta

class SpotifyFeaturesMixin:
    """
    Mixin class containing enhanced features for SpotifyAnalyzer.
    These methods can be incorporated into the SpotifyAnalyzer class.
    """
    
    def connect_to_spotify_api(self, client_id, client_secret):
        """
        Connect to Spotify API using client credentials flow.
        
        Parameters:
        - client_id: Spotify API client ID
        - client_secret: Spotify API client secret
        
        Returns:
        - Spotify client object
        """
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        return self.sp
    
    # ========================
    # Genre Analysis Features
    # ========================
    
    def enrich_with_genres(self):
        """
        Fetch genre information for tracks in the dataset.
        
        Returns:
        - DataFrame with added genres column
        """
        if not hasattr(self, 'sp'):
            raise ValueError("Must connect to Spotify API first using connect_to_spotify_api()")
        
        # Get unique track IDs (requires data export with track IDs)
        if 'trackId' not in self.df.columns:
            print("Warning: Track IDs not available in data, cannot fetch genres")
            return
        
        print("Fetching genre information for tracks...")
        unique_tracks = self.df['trackId'].unique()
        
        # Process in batches of 50 (API limit)
        genres_map = {}
        for i in range(0, len(unique_tracks), 50):
            batch = unique_tracks[i:i+50]
            results = self.sp.tracks(batch)
            
            for track in results['tracks']:
                if track and track['artists']:
                    artist_id = track['artists'][0]['id']
                    artist = self.sp.artist(artist_id)
                    genres_map[track['id']] = artist['genres']
        
        # Add genres to dataframe
        self.df['genres'] = self.df['trackId'].map(genres_map)
        self.df['genres'] = self.df['genres'].apply(lambda x: x if isinstance(x, list) else [])
        
        print(f"Added genre information for {len(genres_map)} unique tracks")
        return self.df
    
    def top_genres(self, limit=10):
        """
        Get top genres by play count and time.
        
        Parameters:
        - limit: Maximum number of genres to return
        
        Returns:
        - Dictionary with top genres by count and time
        """
        if 'genres' not in self.df.columns:
            raise ValueError("Genre data not available. Run enrich_with_genres() first")
        
        # Explode the genres list to count each genre separately
        genres_df = self.df.explode('genres')
        
        # Filter out None/empty values
        genres_df = genres_df[genres_df['genres'].notna() & (genres_df['genres'] != '')]
        
        # By count
        top_by_count = genres_df['genres'].value_counts().nlargest(limit)
        
        # By time
        genre_time = genres_df.groupby('genres')['hours_played'].sum().nlargest(limit)
        
        return {
            "by_count": top_by_count,
            "by_time": genre_time
        }
    
    def genre_diversity(self):
        """
        Analyze genre diversity over time.
        
        Returns:
        - Dictionary with genre diversity metrics
        """
        if 'genres' not in self.df.columns:
            raise ValueError("Genre data not available. Run enrich_with_genres() first")
        
        # Explode genres for proper counting
        genres_df = self.df.explode('genres')
        
        # Filter out None/empty values
        genres_df = genres_df[genres_df['genres'].notna() & (genres_df['genres'] != '')]
        
        # Monthly unique genres
        monthly_unique = genres_df.groupby(['year', 'month'])['genres'].nunique()
        
        # Genre discovery tracking
        genre_first_listen = genres_df.groupby('genres')['endTime'].min()
        genres_df['is_first_listen'] = genres_df.apply(
            lambda row: genre_first_listen[row['genres']] == row['endTime'], 
            axis=1
        )
        
        # Monthly ratio of new genres
        monthly_listens = genres_df.groupby(['year', 'month']).size()
        monthly_new = genres_df[genres_df['is_first_listen']].groupby(['year', 'month']).size()
        monthly_ratio = (monthly_new / monthly_listens).fillna(0)
        
        # Flatten all genres into a set for total count
        all_genres = set()
        for genres_list in self.df['genres'].dropna():
            if isinstance(genres_list, list):
                all_genres.update(genres_list)
        
        return {
            "monthly_unique": monthly_unique,
            "monthly_discovery_ratio": monthly_ratio,
            "unique_genres_count": len(all_genres),
            "all_genres": list(all_genres)
        }
    
    def plot_genre_analysis(self):
        """
        Create visualizations for genre analysis.
        
        Returns:
        - Dictionary of matplotlib figures
        """
        if 'genres' not in self.df.columns:
            raise ValueError("Genre data not available. Run enrich_with_genres() first")
        
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        top_genres = self.top_genres(limit=10)
        diversity = self.genre_diversity()
        
        # Top genres by count
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        top_genres["by_count"].plot(kind='barh', ax=ax1)
        ax1.set_title("Top Genres by Play Count")
        ax1.set_xlabel("Number of Plays")
        ax1.invert_yaxis()
        
        # Top genres by time
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        top_genres["by_time"].plot(kind='barh', ax=ax2)
        ax2.set_title("Top Genres by Time Listened")
        ax2.set_xlabel("Hours")
        ax2.invert_yaxis()
        
        # Monthly genre diversity
        fig3, ax3 = plt.subplots(figsize=(12, 6))
        diversity["monthly_unique"].plot(kind='bar', ax=ax3)
        ax3.set_title("Unique Genres per Month")
        ax3.set_xlabel("Year-Month")
        ax3.set_ylabel("Number of Unique Genres")
        
        # Format x-axis labels
        if not diversity["monthly_unique"].empty:
            labels = [f"{year}-{month:02d}" for year, month in diversity["monthly_unique"].index]
            ax3.set_xticklabels(labels, rotation=90)
        
        return {
            "top_by_count": fig1,
            "top_by_time": fig2,
            "monthly_diversity": fig3
        }
    
    # ==============================
    # Audio Features Analysis
    # ==============================
    
    def enrich_with_audio_features(self):
        """
        Fetch audio features for tracks in the dataset.
        
        Returns:
        - DataFrame with added audio feature columns
        """
        if not hasattr(self, 'sp'):
            raise ValueError("Must connect to Spotify API first using connect_to_spotify_api()")
        
        # Get unique track IDs (requires data export with track IDs)
        if 'trackId' not in self.df.columns:
            print("Warning: Track IDs not available in data, cannot fetch audio features")
            return
        
        print("Fetching audio features for tracks...")
        unique_tracks = self.df['trackId'].unique()
        
        # Process in batches of 100 (API limit)
        features_map = {}
        for i in range(0, len(unique_tracks), 100):
            batch = unique_tracks[i:i+100]
            results = self.sp.audio_features(batch)
            
            for track_features in results:
                if track_features:
                    features_map[track_features['id']] = track_features
        
        # Extract relevant features to separate columns
        for feature in ['danceability', 'energy', 'key', 'loudness', 'mode', 
                        'speechiness', 'acousticness', 'instrumentalness', 
                        'liveness', 'valence', 'tempo']:
            self.df[feature] = self.df['trackId'].apply(
                lambda x: features_map.get(x, {}).get(feature, None)
            )
        
        print(f"Added audio features for {len(features_map)} unique tracks")
        return self.df
    
    def average_audio_features(self):
        """
        Calculate average audio features across all tracks.
        
        Returns:
        - Dictionary of average feature values
        """
        audio_features = ['danceability', 'energy', 'loudness', 'speechiness', 
                          'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']
        
        # Check which features are available
        available_features = [f for f in audio_features if f in self.df.columns]
        
        if not available_features:
            raise ValueError("No audio features available. Run enrich_with_audio_features() first")
        
        # Calculate weighted averages based on listening time
        weighted_avgs = {}
        total_time = self.df['hours_played'].sum()
        
        for feature in available_features:
            # Filter out None/NaN values
            valid_data = self.df[self.df[feature].notna()]
            if len(valid_data) > 0:
                weighted_avg = (valid_data[feature] * valid_data['hours_played']).sum() / valid_data['hours_played'].sum()
                weighted_avgs[feature] = weighted_avg
            else:
                weighted_avgs[feature] = None
        
        return weighted_avgs
    
    def classify_moods(self):
        """
        Classify tracks into moods based on audio features.
        
        Returns:
        - DataFrame with added mood column
        """
        required_features = ['energy', 'valence']
        
        if not all(feature in self.df.columns for feature in required_features):
            raise ValueError("Energy and valence features required. Run enrich_with_audio_features() first")
        
        # Define mood classification function based on valence and energy
        def get_mood(energy, valence):
            if energy > 0.5 and valence > 0.5:
                return "Happy"
            elif energy > 0.5 and valence <= 0.5:
                return "Angry"
            elif energy <= 0.5 and valence > 0.5:
                return "Relaxed"
            else:
                return "Sad"
        
        # Apply mood classification
        self.df['mood'] = self.df.apply(
            lambda row: get_mood(row['energy'], row['valence']) 
            if pd.notna(row['energy']) and pd.notna(row['valence']) 
            else None, 
            axis=1
        )
        
        return self.df
    
    def mood_analysis(self):
        """
        Analyze listening patterns by mood.
        
        Returns:
        - Dictionary of mood analysis results
        """
        if 'mood' not in self.df.columns:
            self.classify_moods()
        
        # Filter out rows with no mood assigned
        mood_df = self.df[self.df['mood'].notna()]
        
        # If no moods could be assigned, return empty results
        if len(mood_df) == 0:
            return {
                "by_count": pd.Series(),
                "by_time": pd.Series()
            }
        
        # Mood distribution
        mood_counts = mood_df['mood'].value_counts()
        
        # Mood by time
        mood_time = mood_df.groupby('mood')['hours_played'].sum()
        
        # Mood by time of day
        mood_by_hour = mood_df.groupby(['hour', 'mood'])['minutes_played'].sum().unstack(fill_value=0)
        
        # Mood by day of week
        mood_by_weekday = mood_df.groupby(['weekday_name', 'mood'])['minutes_played'].sum().unstack(fill_value=0)
        
        return {
            "by_count": mood_counts,
            "by_time": mood_time,
            "by_hour": mood_by_hour,
            "by_weekday": mood_by_weekday
        }
    
    def audio_features_over_time(self, feature='energy'):
        """
        Track changes in audio features over time.
        
        Parameters:
        - feature: Audio feature to track
        
        Returns:
        - Series of monthly average values
        """
        if feature not in self.df.columns:
            raise ValueError(f"Feature {feature} not available. Run enrich_with_audio_features() first")
        
        # Filter out None/NaN values
        valid_data = self.df[self.df[feature].notna()]
        
        if len(valid_data) == 0:
            return pd.Series()
        
        # Monthly average of the feature
        monthly_avg = valid_data.groupby(['year', 'month']).apply(
            lambda x: (x[feature] * x['hours_played']).sum() / x['hours_played'].sum()
        )
        
        return monthly_avg
    
    def plot_audio_features_analysis(self):
        """
        Create visualizations for audio features analysis.
        
        Returns:
        - Dictionary of matplotlib figures
        """
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Check if audio features are available
        audio_features = ['energy', 'danceability', 'valence', 'tempo']
        available_features = [f for f in audio_features if f in self.df.columns]
        
        if not available_features:
            raise ValueError("No audio features available. Run enrich_with_audio_features() first")
        
        # Average audio features
        avg_features = self.average_audio_features()
        
        # Create radar chart of average features
        fig1, ax1 = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        
        # Select features for radar chart
        radar_features = ['danceability', 'energy', 'valence', 'acousticness', 'instrumentalness', 'liveness']
        radar_features = [f for f in radar_features if f in avg_features and avg_features[f] is not None]
        
        if radar_features:
            # Plot radar chart
            values = [avg_features[f] for f in radar_features]
            angles = np.linspace(0, 2*np.pi, len(radar_features), endpoint=False).tolist()
            values.append(values[0])
            angles.append(angles[0])
            radar_features.append(radar_features[0])
            
            ax1.plot(angles, values)
            ax1.fill(angles, values, alpha=0.1)
            ax1.set_xticks(angles[:-1])
            ax1.set_xticklabels(radar_features[:-1])
            ax1.set_title("Audio Features Profile")
        
        # Mood analysis
        if 'mood' not in self.df.columns:
            self.classify_moods()
        
        mood_data = self.mood_analysis()
        
        # Mood distribution pie chart
        fig2, ax2 = plt.subplots(figsize=(8, 8))
        if not mood_data["by_count"].empty:
            mood_data["by_count"].plot(kind='pie', autopct='%1.1f%%', ax=ax2)
            ax2.set_title("Mood Distribution")
            ax2.set_ylabel("")
        
        # Energy over time
        fig3, ax3 = plt.subplots(figsize=(12, 6))
        energy_over_time = self.audio_features_over_time('energy')
        if not energy_over_time.empty:
            energy_over_time.plot(ax=ax3)
            ax3.set_title("Energy Level Over Time")
            ax3.set_ylabel("Energy (0-1)")
            ax3.set_xlabel("Year-Month")
            
            # Format x-axis labels
            labels = [f"{year}-{month:02d}" for year, month in energy_over_time.index]
            ax3.set_xticks(range(len(labels)))
            ax3.set_xticklabels(labels, rotation=90)
        
        return {
            "audio_features_radar": fig1,
            "mood_distribution": fig2,
            "energy_over_time": fig3
        }
    
    # ==============================
    # Listening Session Analysis
    # ==============================
    
    def detect_sessions(self, gap_threshold=30):
        """
        Detect listening sessions based on time gaps between tracks.
        
        Parameters:
        - gap_threshold: Time gap in minutes that defines a new session
        
        Returns:
        - List of session dataframes
        """
        if self.df is None or len(self.df) == 0:
            return []
        
        # Sort by timestamp
        sorted_df = self.df.sort_values('endTime')
        
        # Calculate time difference between consecutive tracks
        sorted_df['time_diff'] = sorted_df['endTime'].diff()
        
        # Convert to minutes
        sorted_df['time_diff_minutes'] = sorted_df['time_diff'].dt.total_seconds() / 60
        
        # Identify new sessions (first track or gap > threshold)
        sorted_df['new_session'] = sorted_df['time_diff_minutes'].isna() | (sorted_df['time_diff_minutes'] > gap_threshold)
        
        # Assign session IDs
        sorted_df['session_id'] = sorted_df['new_session'].cumsum() - 1
        
        # Group by session ID
        sessions = [group for _, group in sorted_df.groupby('session_id')]
        
        # Store sessions as instance variable
        self.sessions = sessions
        
        return sessions
    
    def session_statistics(self):
        """
        Calculate statistics about listening sessions.
        
        Returns:
        - Dictionary of session statistics
        """
        if not hasattr(self, 'sessions') or not self.sessions:
            self.detect_sessions()
        
        # Check if we have any sessions
        if not self.sessions:
            return {
                "total_sessions": 0,
                "avg_session_length": 0,
                "median_session_length": 0,
                "avg_tracks_per_session": 0,
                "avg_artists_per_session": 0
            }
        
        # Calculate session lengths in minutes
        session_lengths = []
        tracks_per_session = []
        artists_per_session = []
        
        for session in self.sessions:
            # Session length = time between first and last track + duration of last track
            if len(session) > 1:
                # First track start time (endTime - duration)
                first_track_start = session['endTime'].min() - pd.Timedelta(minutes=session.iloc[0]['minutes_played'])
                # Last track end time
                last_track_end = session['endTime'].max()
                length_minutes = (last_track_end - first_track_start).total_seconds() / 60
            else:
                length_minutes = session['minutes_played'].iloc[0]
            
            session_lengths.append(length_minutes)
            tracks_per_session.append(len(session))
            artists_per_session.append(session['artistName'].nunique())
        
        # Create histogram of session lengths
        hist_edges = [0, 15, 30, 60, 120, 240, float('inf')]
        hist_counts, _ = np.histogram(session_lengths, bins=hist_edges)
        hist_ranges = [f"{low}-{high}min" if high < float('inf') else f"{low}min+" for low, high in zip(hist_edges[:-1], hist_edges[1:])]
        length_distribution = dict(zip(hist_ranges, hist_counts))
        
        return {
            "total_sessions": len(self.sessions),
            "avg_session_length": np.mean(session_lengths),
            "median_session_length": np.median(session_lengths),
            "avg_tracks_per_session": np.mean(tracks_per_session),
            "avg_artists_per_session": np.mean(artists_per_session),
            "session_length_distribution": length_distribution,
            "longest_session_minutes": max(session_lengths) if session_lengths else 0,
            "shortest_session_minutes": min(session_lengths) if session_lengths else 0
        }
    
    def session_patterns(self):
        """
        Analyze patterns in when sessions occur.
        
        Returns:
        - Dictionary of session patterns
        """
        if not hasattr(self, 'sessions') or not self.sessions:
            self.detect_sessions()
        
        # Check if we have any sessions
        if not self.sessions:
            return {
                "by_hour": {},
                "by_weekday": {},
                "by_month": {}
            }
        
        # Extract start time of each session
        session_starts = []
        session_weekdays = []
        session_months = []
        
        for session in self.sessions:
            # First track start time (endTime - duration)
            start_time = session['endTime'].min() - pd.Timedelta(minutes=session.iloc[0]['minutes_played'])
            session_starts.append(start_time.hour)
            session_weekdays.append(start_time.strftime('%A'))
            session_months.append(start_time.strftime('%B'))
        
        # Create distributions
        hour_counts = Counter(session_starts)
        weekday_counts = Counter(session_weekdays)
        month_counts = Counter(session_months)
        
        # Ensure all hours, weekdays, and months are represented
        all_hours = range(24)
        hour_distribution = {hour: hour_counts.get(hour, 0) for hour in all_hours}
        
        all_weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_distribution = {weekday: weekday_counts.get(weekday, 0) for weekday in all_weekdays}
        
        all_months = ['January', 'February', 'March', 'April', 'May', 'June', 
                     'July', 'August', 'September', 'October', 'November', 'December']
        month_distribution = {month: month_counts.get(month, 0) for month in all_months}
        
        return {
            "by_hour": hour_distribution,
            "by_weekday": weekday_distribution,
            "by_month": month_distribution
        }
    
    def session_content_analysis(self):
        """
        Analyze the content of sessions.
        
        Returns:
        - Dictionary of session content analysis
        """
        if not hasattr(self, 'sessions') or not self.sessions:
            self.detect_sessions()
        
        # Check if we have any sessions
        if not self.sessions:
            return {
                "avg_artist_continuity": 0,
                "avg_unique_artists_ratio": 0,
                "session_types": Counter()
            }
        
        # Calculate metrics for each session
        artist_continuity = []  # % of consecutive tracks by same artist
        unique_artists_ratio = []  # unique artists / total tracks
        
        for session in self.sessions:
            if len(session) > 1:
                # Calculate artist continuity
                same_artist_count = sum(session['artistName'].iloc[i] == session['artistName'].iloc[i+1] 
                                        for i in range(len(session)-1))
                continuity = same_artist_count / (len(session) - 1)
                artist_continuity.append(continuity)
                
                # Calculate unique artists ratio
                unique_ratio = session['artistName'].nunique() / len(session)
                unique_artists_ratio.append(unique_ratio)
        
        # Classify sessions
        session_types = []
        for session in self.sessions:
            # Single-artist sessions
            if len(session) > 1 and session['artistName'].nunique() == 1:
                session_types.append("single_artist")
            # Album listening (same artist, consecutive tracks)
            elif len(session) > 3 and session['artistName'].nunique() <= 2:
                session_types.append("album_listening")
            # Variety sessions (many different artists)
            elif len(session) > 1 and session['artistName'].nunique() / len(session) > 0.8:
                session_types.append("variety")
            # Default
            else:
                session_types.append("mixed")
        
        return {
            "avg_artist_continuity": np.mean(artist_continuity) if artist_continuity else 0,
            "avg_unique_artists_ratio": np.mean(unique_artists_ratio) if unique_artists_ratio else 0,
            "session_types": Counter(session_types)
        }
    
    def plot_session_analysis(self):
        """
        Create visualizations for session analysis.
        
        Returns:
        - Dictionary of matplotlib figures
        """
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Make sure sessions are detected
        if not hasattr(self, 'sessions') or not self.sessions:
            self.detect_sessions()
        
        # Check if we have any sessions
        if not self.sessions:
            return {}
        
        # Get statistics
        stats = self.session_statistics()
        patterns = self.session_patterns()
        content = self.session_content_analysis()
        
        # Session length distribution
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        if stats["session_length_distribution"]:
            lengths = list(stats["session_length_distribution"].keys())
            counts = list(stats["session_length_distribution"].values())
            ax1.bar(lengths, counts)
            ax1.set_title("Session Length Distribution")
            ax1.set_xlabel("Session Duration")
            ax1.set_ylabel("Number of Sessions")
            plt.setp(ax1.get_xticklabels(), rotation=45)
        
        # Session start hour distribution
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        hours = list(patterns["by_hour"].keys())
        counts = list(patterns["by_hour"].values())
        ax2.bar(hours, counts)
        ax2.set_title("Session Start Times")
        ax2.set_xlabel("Hour of Day")
        ax2.set_ylabel("Number of Sessions")
        ax2.set_xticks(range(0, 24, 2))
        
        # Session types pie chart
        fig3, ax3 = plt.subplots(figsize=(8, 8))
        if content["session_types"]:
            labels = list(content["session_types"].keys())
            sizes = list(content["session_types"].values())
            ax3.pie(sizes, labels=labels, autopct='%1.1f%%')
            ax3.set_title("Session Types")
        
        return {
            "length_distribution": fig1,
            "start_times": fig2,
            "session_types": fig3
        }
    
    # ==============================
    # Listening Context Prediction
    # ==============================
    
    def categorize_listening_contexts(self):
        """
        Categorize listening sessions into likely contexts based on audio features and time.
        
        Contexts: workout, commute, work, relaxation, party
        
        Returns:
        - DataFrame with added context column
        """
        # Ensure required columns exist
        if 'hour' not in self.df.columns:
            self.df['hour'] = self.df['endTime'].dt.hour
        if 'weekday' not in self.df.columns:
            self.df['weekday'] = self.df['endTime'].dt.dayofweek
        
        # Check if we have audio features
        has_audio_features = all(col in self.df.columns for col in ['energy', 'tempo'])
        
        # Define context rules
        def determine_context(row):
            # Default values if audio features missing
            energy = row.get('energy', 0.5) if has_audio_features else 0.5
            tempo = row.get('tempo', 120) if has_audio_features else 120
            
            # Workout: high energy, high tempo, morning/evening
            if has_audio_features and energy > 0.7 and tempo > 120 and (5 <= row['hour'] <= 9 or 17 <= row['hour'] <= 20):
                return "workout"
            
            # Commute: weekday, typical commute hours
            elif row['weekday'] < 5 and ((7 <= row['hour'] <= 9) or (16 <= row['hour'] <= 19)):
                return "commute"
            
            # Work: weekday, working hours, moderate energy
            elif row['weekday'] < 5 and 9 <= row['hour'] <= 17 and (not has_audio_features or energy < 0.7):
                return "work"
            
            # Party: weekend evenings, high energy
            elif row['weekday'] >= 5 and row['hour'] >= 20 and (not has_audio_features or energy > 0.7):
                return "party"
            
            # Relaxation: evenings, low energy
            elif row['hour'] >= 20 and (not has_audio_features or energy < 0.5):
                return "relaxation"
            
            # Default: other
            else:
                return "other"
        
        # Apply context categorization
        self.df['context'] = self.df.apply(determine_context, axis=1)
        
        return self.df
    
    def context_statistics(self):
        """
        Calculate statistics about listening contexts.
        
        Returns:
        - Dictionary of context statistics
        """
        if 'context' not in self.df.columns:
            self.categorize_listening_contexts()
        
        # Context distribution
        context_counts = self.df['context'].value_counts()
        context_distribution = context_counts / len(self.df)
        
        # Time spent in each context
        context_time = self.df.groupby('context')['minutes_played'].sum()
        
        # Context by hour
        context_by_hour = self.df.groupby(['hour', 'context']).size().unstack(fill_value=0)
        
        # Context by weekday
        context_by_weekday = self.df.groupby(['weekday_name', 'context']).size().unstack(fill_value=0)
        
        return {
            "distribution": context_distribution,
            "by_time": context_time,
            "by_hour": context_by_hour,
            "by_weekday": context_by_weekday
        }
    
    def train_context_predictor(self):
        """
        Train a simple model to predict listening context based on audio features and time.
        
        Returns:
        - Trained model
        """
        if 'context' not in self.df.columns:
            self.categorize_listening_contexts()
        
        # Import scikit-learn
        try:
            from sklearn.tree import DecisionTreeClassifier
        except ImportError:
            raise ImportError("scikit-learn is required for context prediction. Install with 'pip install scikit-learn'")
        
        # Select features for prediction
        features = ['hour', 'weekday']
        
        # Add audio features if available
        for feature in ['energy', 'tempo', 'danceability', 'valence']:
            if feature in self.df.columns:
                features.append(feature)
        
        # Check which features are available
        available_features = [f for f in features if f in self.df.columns]
        
        if len(available_features) < 2:
            raise ValueError("Not enough features available for prediction")
        
        # Filter out rows with missing values
        train_data = self.df.dropna(subset=available_features + ['context'])
        
        if len(train_data) == 0:
            raise ValueError("No valid data available for training after filtering missing values")
        
        # Prepare data
        X = train_data[available_features].values
        y = train_data['context'].values
        
        # Train a simple model (Decision Tree for interpretability)
        self.context_model = DecisionTreeClassifier(max_depth=5)
        self.context_model.fit(X, y)
        
        # Save feature names for prediction
        self.context_features = available_features
        
        return self.context_model
    
    def predict_context(self, **kwargs):
        """
        Predict listening context based on provided features.
        
        Parameters can include: energy, tempo, hour, weekday, etc.
        
        Returns:
        - Predicted context
        """
        if not hasattr(self, 'context_model'):
            self.train_context_predictor()
        
        # Prepare input features in the correct order
        features = []
        for feature in self.context_features:
            if feature in kwargs:
                features.append(kwargs[feature])
            else:
                raise ValueError(f"Missing required feature: {feature}")
        
        # Make prediction
        prediction = self.context_model.predict([features])[0]
        
        return prediction
    
    def suggest_for_context(self, context, limit=5):
        """
        Suggest tracks for a specific context based on past listening.
        
        Parameters:
        - context: The listening context (workout, work, etc.)
        - limit: Maximum number of suggestions
        
        Returns:
        - List of suggested tracks
        """
        if 'context' not in self.df.columns:
            self.categorize_listening_contexts()
        
        # Filter by context
        context_df = self.df[self.df['context'] == context]
        
        if len(context_df) == 0:
            return []
        
        # Get top tracks for this context
        top_tracks = context_df.groupby(['trackName', 'artistName']).size().nlargest(limit)
        
        # Format as list of dicts
        suggestions = [
            {"track": track, "artist": artist, "count": count}
            for (track, artist), count in top_tracks.items()
        ]
        
        return suggestions
    
    def plot_context_analysis(self):
        """
        Create visualizations for context analysis.
        
        Returns:
        - Dictionary of matplotlib figures
        """
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Make sure contexts are categorized
        if 'context' not in self.df.columns:
            self.categorize_listening_contexts()
        
        # Get context statistics
        stats = self.context_statistics()
        
        # Context distribution pie chart
        fig1, ax1 = plt.subplots(figsize=(8, 8))
        stats["distribution"].plot(kind='pie', autopct='%1.1f%%', ax=ax1)
        ax1.set_title("Listening Context Distribution")
        ax1.set_ylabel("")
        
        # Time spent in each context
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        stats["by_time"].plot(kind='bar', ax=ax2)
        ax2.set_title("Time Spent in Each Context")
        ax2.set_xlabel("Context")
        ax2.set_ylabel("Minutes")
        
        # Context by hour heatmap
        fig3, ax3 = plt.subplots(figsize=(12, 8))
        if not stats["by_hour"].empty:
            sns.heatmap(stats["by_hour"], cmap="YlGnBu", ax=ax3)
            ax3.set_title("Context by Hour of Day")
            ax3.set_xlabel("Context")
            ax3.set_ylabel("Hour")
        
        return {
            "context_distribution": fig1,
            "time_by_context": fig2,
            "context_by_hour": fig3
        }


# Update the existing SpotifyAnalyzer class with new features
def enhance_spotify_analyzer():
    """
    Add the new features to the SpotifyAnalyzer class.
    
    This function should be called after importing the SpotifyAnalyzer class.
    """
    from spotify_analyzer import SpotifyAnalyzer
    
    # Get all methods from the mixin
    mixin_methods = [method for method in dir(SpotifyFeaturesMixin) 
                    if callable(getattr(SpotifyFeaturesMixin, method)) 
                    and not method.startswith('__')]
    
    # Add each method to the SpotifyAnalyzer class
    for method_name in mixin_methods:
        method = getattr(SpotifyFeaturesMixin, method_name)
        setattr(SpotifyAnalyzer, method_name, method)
    
    print(f"Enhanced SpotifyAnalyzer with {len(mixin_methods)} new methods")
    return SpotifyAnalyzer


# Example usage in external code:
# 
from spotify_features import enhance_spotify_analyzer
from spotify_analyzer import SpotifyAnalyzer
import os

enhance_spotify_analyzer()
analyzer = SpotifyAnalyzer(["StreamingHistory_music_0.json"])

#Client id and secret from environment variables
analyzer.connect_to_spotify_api(client_id=os.environ.get('SPOTIPY_CLIENT_ID'), client_secret=os.environ.get('SPOTIPY_CLIENT_SECRET'))

analyzer.enrich_with_genres()
top_genres = analyzer.top_genres()

