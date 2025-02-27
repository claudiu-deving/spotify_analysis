# spotify_analyzer.py
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
from collections import Counter

class SpotifyAnalyzer:
    def __init__(self, data_files):
        """
        Initialize the Spotify data analyzer.
        
        Parameters:
        data_files (str or list): Path to the JSON file(s) containing Spotify data
        """
        self.data_files = data_files if isinstance(data_files, list) else [data_files]
        self.df = None
        self.load_data()
        
    def load_data(self):
        """Load Spotify streaming data from JSON files"""
        data = []
        
        for file_path in self.data_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    if isinstance(file_data, list):
                        data.extend(file_data)
                    else:
                        data.append(file_data)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        if not data:
            raise ValueError("No data could be loaded from the provided files")
            
        print(f"Loaded {len(data)} streaming records")
        
        # Convert to DataFrame
        self.df = pd.DataFrame(data)
        
        # Convert endTime to datetime
        self.df['endTime'] = pd.to_datetime(self.df['endTime'])
        
        # Extract date components
        self.df['date'] = self.df['endTime'].dt.date
        self.df['year'] = self.df['endTime'].dt.year
        self.df['month'] = self.df['endTime'].dt.month
        self.df['month_name'] = self.df['endTime'].dt.strftime('%B')
        self.df['day'] = self.df['endTime'].dt.day
        self.df['weekday'] = self.df['endTime'].dt.dayofweek
        self.df['weekday_name'] = self.df['endTime'].dt.strftime('%A')
        self.df['hour'] = self.df['endTime'].dt.hour
        
        # Convert ms to more readable units
        self.df['minutes_played'] = self.df['msPlayed'] / 60000
        self.df['hours_played'] = self.df['msPlayed'] / 3600000
        
        # Filter out very short plays (likely skips)
        self.df = self.df[self.df['msPlayed'] > 30000]
        
        return self.df
        
    def basic_stats(self):
        """Get basic stats about your listening habits"""
        total_songs = len(self.df)
        unique_tracks = self.df['trackName'].nunique()
        unique_artists = self.df['artistName'].nunique()
        
        total_ms = self.df['msPlayed'].sum()
        total_hours = total_ms / 3600000
        
        date_range = (self.df['endTime'].max() - self.df['endTime'].min()).days
        avg_daily_listening = total_hours / date_range if date_range > 0 else 0
        
        return {
            "total_songs_played": total_songs,
            "unique_tracks": unique_tracks,
            "unique_artists": unique_artists,
            "total_listening_hours": total_hours,
            "date_range_days": date_range,
            "avg_daily_hours": avg_daily_listening,
            "start_date": self.df['endTime'].min().date(),
            "end_date": self.df['endTime'].max().date()
        }
    
    def top_artists(self, limit=10):
        """Get your most listened to artists"""
        # By play count
        top_by_count = self.df['artistName'].value_counts().nlargest(limit)
        
        # By time listened
        artist_time = self.df.groupby('artistName')['hours_played'].sum().nlargest(limit)
        
        return {
            "by_count": top_by_count,
            "by_time": artist_time
        }
    
    def top_tracks(self, limit=10):
        """Get your most listened to tracks"""
        # By play count
        top_by_count = self.df.groupby(['trackName', 'artistName']).size().nlargest(limit)
        
        # By time listened
        track_time = self.df.groupby(['trackName', 'artistName'])['hours_played'].sum().nlargest(limit)
        
        return {
            "by_count": top_by_count,
            "by_time": track_time
        }
    
    def listening_by_time(self):
        """Analyze listening patterns by time (hour, day, month)"""
        # By hour
        hourly = self.df.groupby('hour')['minutes_played'].sum()
        
        # By day of week
        daily = self.df.groupby('weekday_name')['minutes_played'].sum()
        # Ensure correct day order
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily = daily.reindex(day_order)
        
        # By month
        monthly = self.df.groupby(['year', 'month', 'month_name'])['hours_played'].sum().reset_index()
        
        return {
            "hourly": hourly,
            "daily": daily,
            "monthly": monthly
        }
    
    def artist_diversity(self):
        """Analyze artist diversity over time"""
        monthly_unique = self.df.groupby(['year', 'month'])['artistName'].nunique()
        
        # Calculate repeats vs. new discoveries
        artist_first_listen = self.df.groupby('artistName')['endTime'].min()
        self.df['is_first_listen'] = self.df.apply(
            lambda row: artist_first_listen[row['artistName']] == row['endTime'], 
            axis=1
        )
        
        # Monthly ratio of new artists
        monthly_listens = self.df.groupby(['year', 'month']).size()
        monthly_new = self.df[self.df['is_first_listen']].groupby(['year', 'month']).size()
        monthly_ratio = (monthly_new / monthly_listens).fillna(0)
        
        return {
            "monthly_unique": monthly_unique,
            "monthly_discovery_ratio": monthly_ratio
        }
    
    def listening_streaks(self):
        """Analyze daily listening streaks"""
        # Get sorted list of days with listening activity
        active_days = sorted(self.df['date'].unique())
        
        if len(active_days) == 0:
            return {"longest_streak": 0}
        
        # Find the longest streak
        longest_streak = current_streak = 1
        longest_end = active_days[0]
        
        for i in range(1, len(active_days)):
            # If consecutive day
            if (active_days[i] - active_days[i-1]).days == 1:
                current_streak += 1
                if current_streak > longest_streak:
                    longest_streak = current_streak
                    longest_end = active_days[i]
            else:
                current_streak = 1
        
        longest_start = longest_end - pd.Timedelta(days=longest_streak-1)
        
        return {
            "days_with_activity": len(active_days),
            "total_days_range": (active_days[-1] - active_days[0]).days + 1,
            "activity_ratio": len(active_days) / ((active_days[-1] - active_days[0]).days + 1),
            "longest_streak": longest_streak,
            "longest_streak_start": longest_start,
            "longest_streak_end": longest_end
        }
    
    def listening_heatmap_data(self):
        """Get data for hour × day listening heatmap"""
        # Create a pivot table of weekday x hour
        heatmap_data = self.df.pivot_table(
            values='minutes_played',
            index='weekday',
            columns='hour',
            aggfunc='sum',
            fill_value=0
        )
        
        # Map day numbers to names and ensure correct order
        day_mapping = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 
                     3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
        heatmap_data.index = [day_mapping[day] for day in heatmap_data.index]
        
        return heatmap_data
    
    def mood_analysis(self, acoustic_energy_ratio=0.5):
        """
        Placeholder for analyzing mood based on track characteristics.
        
        Note: This requires additional data not in the basic export, such as track 
        audio features from the Spotify API (danceability, energy, etc.)
        """
        # This is a placeholder function - to implement fully, you would need to:
        # 1. Use the Spotify API to fetch audio features for each track
        # 2. Create mood categories based on combinations of features
        # 3. Analyze listening patterns by mood
        
        # Example features to fetch from Spotify API: 
        # - Danceability
        # - Energy
        # - Acousticness
        # - Valence (musical positiveness)
        # - Tempo
        
        # Example mood categories:
        # - Happy (high valence, high energy)
        # - Sad (low valence, low energy)
        # - Energetic (high energy, high tempo)
        # - Calm (high acousticness, low energy)
        
        return "Mood analysis requires audio features from the Spotify API"
    
    def plot_top_artists(self, limit=10):
        """Plot top artists by play count and time"""
        top = self.top_artists(limit)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # By count
        top["by_count"].plot(kind='barh', ax=ax1)
        ax1.set_title(f"Top {limit} Artists by Play Count")
        ax1.set_xlabel("Number of Plays")
        ax1.invert_yaxis()  # To have the highest at the top
        
        # By time
        top["by_time"].plot(kind='barh', ax=ax2)
        ax2.set_title(f"Top {limit} Artists by Time Listened")
        ax2.set_xlabel("Hours")
        ax2.invert_yaxis()  # To have the highest at the top
        
        plt.tight_layout()
        return fig
    
    def plot_top_tracks(self, limit=10):
        """Plot top tracks by play count and time"""
        top = self.top_tracks(limit)
        
        # Create separate figures for better readability with long track names
        fig1, ax1 = plt.subplots(figsize=(10, 8))
        fig2, ax2 = plt.subplots(figsize=(10, 8))
        
        # By count - Create readable labels with both track and artist
        top_count_df = top["by_count"].reset_index()
        labels = [f"{row['trackName']} - {row['artistName']}" for _, row in top_count_df.iterrows()]
        ax1.barh(range(len(labels)), top_count_df[0].values)
        ax1.set_yticks(range(len(labels)))
        ax1.set_yticklabels(labels)
        ax1.set_title(f"Top {limit} Tracks by Play Count")
        ax1.set_xlabel("Number of Plays")
        ax1.invert_yaxis()  # To have the highest at the top
        
        # By time
        top_time_df = top["by_time"].reset_index()
        labels = [f"{row['trackName']} - {row['artistName']}" for _, row in top_time_df.iterrows()]
        ax2.barh(range(len(labels)), top_time_df["hours_played"].values)
        ax2.set_yticks(range(len(labels)))
        ax2.set_yticklabels(labels)
        ax2.set_title(f"Top {limit} Tracks by Time Listened")
        ax2.set_xlabel("Hours")
        ax2.invert_yaxis()  # To have the highest at the top
        
        plt.tight_layout()
        return fig1, fig2
    
    def plot_listening_patterns(self):
        """Plot listening patterns by time (hour, day, month)"""
        time_data = self.listening_by_time()
        
        # Create three separate figures
        fig1, ax1 = plt.subplots(figsize=(12, 5))
        fig2, ax2 = plt.subplots(figsize=(12, 5))
        fig3, ax3 = plt.subplots(figsize=(14, 5))
        
        # Hourly pattern
        time_data["hourly"].plot(kind='bar', ax=ax1)
        ax1.set_title("Listening by Hour of Day")
        ax1.set_xlabel("Hour")
        ax1.set_ylabel("Minutes")
        ax1.set_xticks(range(0, 24, 2))  # Show every other hour for clarity
        
        # Daily pattern
        time_data["daily"].plot(kind='bar', ax=ax2)
        ax2.set_title("Listening by Day of Week")
        ax2.set_xlabel("Day")
        ax2.set_ylabel("Minutes")
        
        # Monthly pattern - plot as line chart with years as different lines
        monthly = time_data["monthly"]
        
        # Get month names in correct order
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        
        # Plot each year as a separate line
        for year in monthly['year'].unique():
            year_data = monthly[monthly['year'] == year]
            
            # Sort by month number to ensure correct ordering
            year_data = year_data.sort_values('month')
            
            ax3.plot(year_data['month_name'], year_data['hours_played'], 
                    marker='o', linewidth=2, label=str(year))
            
        ax3.set_title("Listening by Month")
        ax3.set_xlabel("Month")
        ax3.set_ylabel("Hours")
        ax3.legend(title="Year")
        
        # Set x-tick labels to month names in correct order
        ax3.set_xticks(range(len(month_names)))
        ax3.set_xticklabels(month_names, rotation=45)
        
        plt.tight_layout()
        return fig1, fig2, fig3
    
    def plot_listening_heatmap(self):
        """Plot hour × day listening heatmap"""
        heatmap_data = self.listening_heatmap_data()
        
        fig, ax = plt.subplots(figsize=(14, 7))
        sns.heatmap(heatmap_data, cmap="YlGnBu", annot=False, fmt=".1f", ax=ax)
        ax.set_title("Listening Activity Heatmap (Hour × Day)")
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Day of Week")
        
        plt.tight_layout()
        return fig
    
    def plot_artist_diversity(self):
        """Plot artist diversity over time"""
        diversity = self.artist_diversity()
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        # Unique artists per month
        diversity["monthly_unique"].plot(kind='bar', ax=ax1)
        ax1.set_title("Unique Artists per Month")
        ax1.set_xlabel("")  # We'll add this to the bottom subplot
        ax1.set_ylabel("Number of Unique Artists")
        
        # Discovery ratio per month
        diversity["monthly_discovery_ratio"].plot(kind='bar', ax=ax2)
        ax2.set_title("Ratio of New Artist Discoveries")
        ax2.set_xlabel("Year-Month")
        ax2.set_ylabel("Proportion of New Artists")
        ax2.set_ylim(0, 1)
        
        # Format x-axis labels to be more readable
        labels = [f"{year}-{month:02d}" for year, month in diversity["monthly_unique"].index]
        ax2.set_xticklabels(labels, rotation=90)
        
        plt.tight_layout()
        return fig
    
    def generate_report(self, output_dir="spotify_analysis"):
        """Generate a complete analysis report with visualizations"""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Basic stats
        stats = self.basic_stats()
        with open(f"{output_dir}/basic_stats.txt", "w") as f:
            f.write("=== SPOTIFY LISTENING ANALYSIS ===\n\n")
            f.write(f"Period: {stats['start_date']} to {stats['end_date']} ({stats['date_range_days']} days)\n")
            f.write(f"Total tracks played: {stats['total_songs_played']}\n")
            f.write(f"Unique tracks: {stats['unique_tracks']}\n")
            f.write(f"Unique artists: {stats['unique_artists']}\n")
            f.write(f"Total listening time: {stats['total_listening_hours']:.2f} hours\n")
            f.write(f"Average daily listening: {stats['avg_daily_hours']:.2f} hours\n\n")
        
        # Top artists and tracks
        top_artists = self.top_artists()
        top_tracks = self.top_tracks()
        
        with open(f"{output_dir}/top_artists_tracks.txt", "w") as f:
            f.write("=== TOP ARTISTS ===\n\n")
            f.write("By Play Count:\n")
            for i, (artist, count) in enumerate(top_artists["by_count"].items(), 1):
                f.write(f"{i}. {artist}: {count} plays\n")
            
            f.write("\nBy Time Listened:\n")
            for i, (artist, hours) in enumerate(top_artists["by_time"].items(), 1):
                f.write(f"{i}. {artist}: {hours:.2f} hours\n")
            
            f.write("\n\n=== TOP TRACKS ===\n\n")
            f.write("By Play Count:\n")
            for i, ((track, artist), count) in enumerate(top_tracks["by_count"].items(), 1):
                f.write(f"{i}. {track} - {artist}: {count} plays\n")
            
            f.write("\nBy Time Listened:\n")
            for i, ((track, artist), hours) in enumerate(top_tracks["by_time"].items(), 1):
                f.write(f"{i}. {track} - {artist}: {hours:.2f} hours\n")
        
        # Streaks
        streak_info = self.listening_streaks()
        with open(f"{output_dir}/listening_streaks.txt", "w") as f:
            f.write("=== LISTENING STREAKS ===\n\n")
            f.write(f"Days with activity: {streak_info['days_with_activity']} out of {streak_info['total_days_range']} days\n")
            f.write(f"Activity ratio: {streak_info['activity_ratio']:.2%}\n")
            f.write(f"Longest streak: {streak_info['longest_streak']} consecutive days\n")
            f.write(f"Longest streak period: {streak_info['longest_streak_start']} to {streak_info['longest_streak_end']}\n")
        
        # Save plots
        self.plot_top_artists().savefig(f"{output_dir}/top_artists.png")
        
        track_fig1, track_fig2 = self.plot_top_tracks()
        track_fig1.savefig(f"{output_dir}/top_tracks_by_count.png")
        track_fig2.savefig(f"{output_dir}/top_tracks_by_time.png")
        
        hour_fig, day_fig, month_fig = self.plot_listening_patterns()
        hour_fig.savefig(f"{output_dir}/listening_by_hour.png")
        day_fig.savefig(f"{output_dir}/listening_by_day.png")
        month_fig.savefig(f"{output_dir}/listening_by_month.png")
        
        self.plot_listening_heatmap().savefig(f"{output_dir}/listening_heatmap.png")
        self.plot_artist_diversity().savefig(f"{output_dir}/artist_diversity.png")
        
        print(f"Analysis complete! Results saved to '{output_dir}' directory.")


# Example usage:
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python spotify_analyzer.py <path_to_json_file(s)>")
        sys.exit(1)
    
    json_files = sys.argv[1:]
    analyzer = SpotifyAnalyzer(json_files)
    analyzer.generate_report()