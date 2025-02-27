# spotify_cli.py
import argparse
import os
import glob
import json
import sys
from spotify_analyzer import SpotifyAnalyzer

def find_spotify_json_files(directory):
    """Find all Spotify JSON files in a directory"""
    pattern = os.path.join(directory, "*History*.json")
    files = glob.glob(pattern)
    
    if not files:
        print(f"No Spotify data files found in {directory}")
        print("Spotify history files are usually named like 'StreamingHistory0.json'")
        return []
    
    return files

def print_basic_stats(stats):
    """Print basic listening statistics"""
    print("\n=== SPOTIFY LISTENING STATISTICS ===")
    print(f"Period: {stats['start_date']} to {stats['end_date']} ({stats['date_range_days']} days)")
    print(f"Total tracks played: {stats['total_songs_played']:,}")
    print(f"Unique tracks: {stats['unique_tracks']:,}")
    print(f"Unique artists: {stats['unique_artists']:,}")
    print(f"Total listening time: {stats['total_listening_hours']:.2f} hours")
    print(f"Average daily listening: {stats['avg_daily_hours']:.2f} hours")

def print_top_artists(artists, limit=10):
    """Print top artists"""
    print("\n=== TOP ARTISTS ===")
    
    print("\nBy Play Count:")
    for i, (artist, count) in enumerate(artists["by_count"].items(), 1):
        if i > limit:
            break
        print(f"{i}. {artist}: {count} plays")
    
    print("\nBy Time Listened:")
    for i, (artist, hours) in enumerate(artists["by_time"].items(), 1):
        if i > limit:
            break
        print(f"{i}. {artist}: {hours:.2f} hours")

def print_top_tracks(tracks, limit=10):
    """Print top tracks"""
    print("\n=== TOP TRACKS ===")
    
    print("\nBy Play Count:")
    for i, ((track, artist), count) in enumerate(tracks["by_count"].items(), 1):
        if i > limit:
            break
        print(f"{i}. {track} - {artist}: {count} plays")
    
    print("\nBy Time Listened:")
    for i, ((track, artist), hours) in enumerate(tracks["by_time"].items(), 1):
        if i > limit:
            break
        print(f"{i}. {track} - {artist}: {hours:.2f} hours")

def print_listening_patterns(patterns):
    """Print listening patterns"""
    print("\n=== LISTENING PATTERNS ===")
    
    print("\nTop 5 Hours:")
    hourly = patterns["hourly"].sort_values(ascending=False).head(5)
    for hour, minutes in hourly.items():
        print(f"{hour}:00 - {minutes:.1f} minutes")
    
    print("\nDays of Week (most to least):")
    daily = patterns["daily"].sort_values(ascending=False)
    for day, minutes in daily.items():
        print(f"{day}: {minutes:.1f} minutes")

def print_streaks(streaks):
    """Print listening streaks"""
    print("\n=== LISTENING STREAKS ===")
    print(f"Days with activity: {streaks['days_with_activity']} out of {streaks['total_days_range']} days")
    print(f"Activity ratio: {streaks['activity_ratio']:.2%}")
    print(f"Longest streak: {streaks['longest_streak']} consecutive days")
    
    if streaks['longest_streak_start'] and streaks['longest_streak'] > 1:
        print(f"Longest streak period: {streaks['longest_streak_start']} to {streaks['longest_streak_end']}")

def main():
    parser = argparse.ArgumentParser(description="Analyze your Spotify listening data")
    
    # Main arguments
    parser.add_argument("data_path", help="Path to Spotify data file or directory containing JSON files")
    parser.add_argument("-o", "--output", help="Directory to save visualizations", default="spotify_analysis")
    parser.add_argument("-n", "--limit", help="Number of top items to show", type=int, default=10)
    
    # Actions
    parser.add_argument("--stats", action="store_true", help="Show basic statistics")
    parser.add_argument("--artists", action="store_true", help="Show top artists")
    parser.add_argument("--tracks", action="store_true", help="Show top tracks")
    parser.add_argument("--patterns", action="store_true", help="Show listening patterns")
    parser.add_argument("--streaks", action="store_true", help="Show listening streaks")
    parser.add_argument("--all", action="store_true", help="Show all information")
    parser.add_argument("--report", action="store_true", help="Generate a full report with visualizations")
    
    args = parser.parse_args()
    
    # Determine if path is a file or directory
    if os.path.isdir(args.data_path):
        # Find all Spotify JSON files in the directory
        json_files = find_spotify_json_files(args.data_path)
        if not json_files:
            sys.exit(1)
    elif os.path.isfile(args.data_path) and args.data_path.endswith('.json'):
        # Single file
        json_files = [args.data_path]
    else:
        print(f"Error: {args.data_path} is not a valid JSON file or directory")
        sys.exit(1)
    
    # Initialize analyzer
    try:
        analyzer = SpotifyAnalyzer(json_files)
        
        # If no specific actions were chosen, show basic stats
        if not (args.stats or args.artists or args.tracks or args.patterns or
                args.streaks or args.all or args.report):
            args.stats = True
        
        # Process requested actions
        if args.stats or args.all:
            stats = analyzer.basic_stats()
            print_basic_stats(stats)
        
        if args.artists or args.all:
            artists = analyzer.top_artists(args.limit)
            print_top_artists(artists, args.limit)
        
        if args.tracks or args.all:
            tracks = analyzer.top_tracks(args.limit)
            print_top_tracks(tracks, args.limit)
        
        if args.patterns or args.all:
            patterns = analyzer.listening_by_time()
            print_listening_patterns(patterns)
        
        if args.streaks or args.all:
            streaks = analyzer.listening_streaks()
            print_streaks(streaks)
        
        if args.report:
            print(f"\nGenerating full report with visualizations...")
            analyzer.generate_report(args.output)
            print(f"Report saved to {args.output} directory")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()