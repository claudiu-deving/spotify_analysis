# Spotify Listening Analysis

**NOTE**: 
This is an experiment, the entire project was written by the enhanced Claude 3.7 LLM.

This project provides tools to analyze your personal Spotify listening history using the data export provided by Spotify.

## Features

- **Comprehensive analysis** of your listening habits
- **Interactive dashboard** with visualizations using Streamlit
- **Command-line tool** for quick insights
- **Full report generation** with charts and statistics

## Getting Your Spotify Data

1. Log in to your Spotify account
2. Go to your [Privacy Settings](https://www.spotify.com/account/privacy/)
3. Click on "Request your data"
4. You'll receive an email with a download link within a few days
5. Extract the ZIP file and locate the JSON files (typically named like "StreamingHistory0.json")

## Project Components

This project consists of three main components:

1. **Core Analyzer Library** (`spotify_analyzer.py`) - The main class that processes and analyzes your Spotify data
2. **Interactive Dashboard** (`spotify_dashboard.py`) - A Streamlit web app for interactive data exploration
3. **Command-line Tool** (`spotify_cli.py`) - A CLI tool for quick analysis and report generation

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Interactive Dashboard

The dashboard provides the most user-friendly way to explore your data:

```bash
streamlit run spotify_dashboard.py
```

Then open your web browser to the URL displayed (typically http://localhost:8501) and upload your JSON files through the interface.

### Command-line Tool

For quick analysis or to generate reports without the dashboard:

```bash
# Show basic statistics
python spotify_cli.py /path/to/your/spotify/data

# Show top artists
python spotify_cli.py /path/to/your/spotify/data --artists

# Show top tracks
python spotify_cli.py /path/to/your/spotify/data --tracks

# Generate a full report with visualizations
python spotify_cli.py /path/to/your/spotify/data --report

# Show all information at once
python spotify_cli.py /path/to/your/spotify/data --all

# Specify the number of top items to display
python spotify_cli.py /path/to/your/spotify/data --all --limit 20

# Specify output directory for report
python spotify_cli.py /path/to/your/spotify/data --report --output my_spotify_report
```

### Using the Analyzer Directly

For more advanced usage or custom analysis, you can import the analyzer in your own scripts:

```python
from spotify_analyzer import SpotifyAnalyzer

# Initialize with one or more JSON files
analyzer = SpotifyAnalyzer("StreamingHistory0.json")
# or
analyzer = SpotifyAnalyzer(["StreamingHistory0.json", "StreamingHistory1.json"])

# Get basic statistics
stats = analyzer.basic_stats()
print(f"Total listening hours: {stats['total_listening_hours']:.2f}")

# Get top artists
top_artists = analyzer.top_artists(limit=10)
print("Top artist:", top_artists["by_count"].index[0])

# Generate visualizations
analyzer.plot_listening_heatmap()
plt.show()

# Generate full report
analyzer.generate_report(output_dir="my_report")
```

## Available Analysis

The analysis includes:

- **Basic Statistics**: Total listening time, unique artists/tracks, daily averages
- **Top Content**: Most played artists and tracks by both count and time
- **Listening Patterns**: Analysis by hour of day, day of week, and month
- **Listening Heatmap**: Visual display of when you listen the most
- **Streaks**: Analysis of consecutive days with listening activity
- **Artist Diversity**: Tracking unique artists and new discoveries over time

## Example Visualizations

The project generates several visualizations including:

- Bar charts of top artists and tracks
- Time-based listening patterns
- Day/hour heatmaps of listening activity
- Monthly listening trends
- Artist diversity charts

## Requirements

- Python 3.7+
- pandas
- matplotlib
- seaborn
- streamlit (for dashboard)
- plotly (for dashboard)

See `requirements.txt` for the complete list of dependencies.

## Limitations

- This project analyzes the data export provided by Spotify, which only includes basic listening history
- For more advanced analysis (like audio features, mood analysis, etc.), you would need to supplement this data with the Spotify API
- The data export may not include your entire listening history (Spotify typically provides up to one year)

## Future Improvements

Some potential enhancements for future versions:

- Integration with Spotify API to fetch audio features and enhance analysis
- Playlist analysis to understand your curated collections
- Mood analysis based on audio features
- Genre analysis and categorization
- Collaborative filtering to recommend new music
