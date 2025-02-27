# test_spotify_features.py
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from spotify_analyzer import SpotifyAnalyzer

class MockSpotifyAPI:
    """Mock class for Spotify API tests"""
    def __init__(self):
        self.audio_features_response = {
            "danceability": 0.735,
            "energy": 0.578,
            "key": 5,
            "loudness": -11.84,
            "mode": 0,
            "speechiness": 0.0461,
            "acousticness": 0.514,
            "instrumentalness": 0.0902,
            "liveness": 0.159,
            "valence": 0.636,
            "tempo": 98.002,
            "id": "test_id",
            "duration_ms": 255349
        }
        
        self.artist_response = {
            "genres": ["pop", "dance pop", "pop dance"],
            "id": "test_artist_id",
            "name": "Test Artist"
        }
    
    def audio_features(self, track_ids):
        """Mock audio_features method"""
        return [self.audio_features_response for _ in track_ids]
    
    def artist(self, artist_id):
        """Mock artist method"""
        return self.artist_response


class TestGenreAnalysis(unittest.TestCase):
    """Test cases for Genre Analysis feature"""
    
    def setUp(self):
        """Set up test data"""
        # Create a sample DataFrame
        self.df = pd.DataFrame({
            'endTime': pd.date_range(start='2022-01-01', periods=5),
            'artistName': ['Artist A', 'Artist B', 'Artist A', 'Artist C', 'Artist B'],
            'trackName': ['Track 1', 'Track 2', 'Track 3', 'Track 4', 'Track 5'],
            'msPlayed': [240000, 180000, 210000, 195000, 225000],
            'trackId': ['id1', 'id2', 'id3', 'id4', 'id5']
        })
        
        # Create analyzer with mock data
        self.analyzer = SpotifyAnalyzer.__new__(SpotifyAnalyzer)
        self.analyzer.df = self.df
        self.analyzer.df['minutes_played'] = self.analyzer.df['msPlayed'] / 60000
        self.analyzer.df['hours_played'] = self.analyzer.df['msPlayed'] / 3600000
        
        # Mock Spotify API
        self.analyzer.sp = MockSpotifyAPI()
    
    def test_connect_to_spotify_api(self):
        """Test connection to Spotify API"""
        # This would normally require real credentials
        # For the mock test, we'll just verify the method exists
        self.assertTrue(hasattr(self.analyzer, 'connect_to_spotify_api'))
    
    def test_enrich_with_genres(self):
        """Test genre enrichment"""
        # Call the method
        self.analyzer.enrich_with_genres()
        
        # Check if genres column was added
        self.assertIn('genres', self.analyzer.df.columns)
        
        # Check if all rows have genre data
        self.assertTrue(all(isinstance(genres, list) for genres in self.analyzer.df['genres']))
    
    def test_top_genres(self):
        """Test calculation of top genres"""
        # Add mock genre data
        self.analyzer.df['genres'] = [
            ['pop', 'rock'], 
            ['pop'], 
            ['rock', 'alternative'], 
            ['electronic', 'dance'], 
            ['pop', 'dance']
        ]
        
        # Calculate top genres
        top_genres = self.analyzer.top_genres(limit=3)
        
        # Check results
        self.assertIn('by_count', top_genres)
        self.assertIn('by_time', top_genres)
        self.assertEqual(top_genres['by_count'].iloc[0], 3)  # 'pop' should be top with 3 occurrences
    
    def test_genre_diversity(self):
        """Test genre diversity calculation"""
        # Add mock genre data with timestamps
        self.analyzer.df['genres'] = [
            ['pop', 'rock'], 
            ['pop'], 
            ['rock', 'alternative'], 
            ['electronic', 'dance'], 
            ['pop', 'dance']
        ]
        
        # Calculate genre diversity
        diversity = self.analyzer.genre_diversity()
        
        # Check results
        self.assertIn('monthly_unique', diversity)
        self.assertIn('unique_genres_count', diversity)
        self.assertEqual(diversity['unique_genres_count'], 5)  # 5 unique genres


class TestAudioFeaturesAnalysis(unittest.TestCase):
    """Test cases for Audio Features Analysis feature"""
    
    def setUp(self):
        """Set up test data"""
        # Create a sample DataFrame
        self.df = pd.DataFrame({
            'endTime': pd.date_range(start='2022-01-01', periods=5),
            'artistName': ['Artist A', 'Artist B', 'Artist A', 'Artist C', 'Artist B'],
            'trackName': ['Track 1', 'Track 2', 'Track 3', 'Track 4', 'Track 5'],
            'msPlayed': [240000, 180000, 210000, 195000, 225000],
            'trackId': ['id1', 'id2', 'id3', 'id4', 'id5']
        })
        
        # Create analyzer with mock data
        self.analyzer = SpotifyAnalyzer.__new__(SpotifyAnalyzer)
        self.analyzer.df = self.df
        self.analyzer.df['minutes_played'] = self.analyzer.df['msPlayed'] / 60000
        self.analyzer.df['hours_played'] = self.analyzer.df['msPlayed'] / 3600000
        
        # Mock Spotify API
        self.analyzer.sp = MockSpotifyAPI()
    
    def test_enrich_with_audio_features(self):
        """Test audio features enrichment"""
        # Call the method
        self.analyzer.enrich_with_audio_features()
        
        # Check if audio feature columns were added
        for feature in ['danceability', 'energy', 'tempo']:
            self.assertIn(feature, self.analyzer.df.columns)
    
    def test_average_audio_features(self):
        """Test calculation of average audio features"""
        # Add mock audio feature data
        self.analyzer.df['energy'] = [0.8, 0.6, 0.7, 0.5, 0.9]
        self.analyzer.df['danceability'] = [0.7, 0.5, 0.6, 0.8, 0.7]
        
        # Calculate average features
        avg_features = self.analyzer.average_audio_features()
        
        # Check results
        self.assertIn('energy', avg_features)
        self.assertIn('danceability', avg_features)
        
        # Verify weighted average calculation
        total_hours = self.analyzer.df['hours_played'].sum()
        expected_energy = sum(self.analyzer.df['energy'] * self.analyzer.df['hours_played']) / total_hours
        self.assertAlmostEqual(avg_features['energy'], expected_energy)
    
    def test_classify_moods(self):
        """Test mood classification"""
        # Add mock audio feature data
        self.analyzer.df['energy'] = [0.8, 0.3, 0.7, 0.2, 0.9]
        self.analyzer.df['valence'] = [0.7, 0.2, 0.3, 0.8, 0.6]
        
        # Classify moods
        self.analyzer.classify_moods()
        
        # Check if mood column was added
        self.assertIn('mood', self.analyzer.df.columns)
        
        # Check if moods were classified correctly
        expected_moods = ['Happy', 'Sad', 'Angry', 'Relaxed', 'Happy']
        for i, mood in enumerate(expected_moods):
            self.assertEqual(self.analyzer.df.iloc[i]['mood'], mood)


class TestListeningSessionAnalysis(unittest.TestCase):
    """Test cases for Listening Session Analysis feature"""
    
    def setUp(self):
        """Set up test data"""
        # Create a sample DataFrame with specific timestamps to test session detection
        timestamps = [
            '2022-01-01 10:00:00',  # Session 1
            '2022-01-01 10:04:00',  # Session 1
            '2022-01-01 10:08:00',  # Session 1
            '2022-01-01 14:00:00',  # Session 2 (gap > 30 min)
            '2022-01-01 14:05:00',  # Session 2
            '2022-01-02 09:00:00',  # Session 3 (new day)
            '2022-01-02 09:05:00',  # Session 3
            '2022-01-02 09:10:00'   # Session 3
        ]
        
        self.df = pd.DataFrame({
            'endTime': pd.to_datetime(timestamps),
            'artistName': ['Artist A', 'Artist A', 'Artist B', 
                           'Artist C', 'Artist C', 
                           'Artist D', 'Artist E', 'Artist D'],
            'trackName': [f'Track {i+1}' for i in range(8)],
            'msPlayed': [240000, 180000, 210000, 195000, 225000, 230000, 210000, 180000]
        })
        
        # Add minutes played
        self.df['minutes_played'] = self.df['msPlayed'] / 60000
        
        # Create analyzer with mock data
        self.analyzer = SpotifyAnalyzer.__new__(SpotifyAnalyzer)
        self.analyzer.df = self.df
    
    def test_detect_sessions(self):
        """Test detection of listening sessions"""
        # Detect sessions with 30-minute gap threshold
        sessions = self.analyzer.detect_sessions(gap_threshold=30)
        
        # Check if correct number of sessions was detected
        self.assertEqual(len(sessions), 3)
        
        # Check if sessions contain correct tracks
        self.assertEqual(len(sessions[0]), 3)  # First session has 3 tracks
        self.assertEqual(len(sessions[1]), 2)  # Second session has 2 tracks
        self.assertEqual(len(sessions[2]), 3)  # Third session has 3 tracks
    
    def test_session_statistics(self):
        """Test calculation of session statistics"""
        # First detect sessions
        self.analyzer.detect_sessions()
        
        # Calculate statistics
        stats = self.analyzer.session_statistics()
        
        # Check results
        self.assertEqual(stats['total_sessions'], 3)
        self.assertIn('avg_session_length', stats)
        self.assertIn('avg_tracks_per_session', stats)
        self.assertAlmostEqual(stats['avg_tracks_per_session'], 8/3)  # 8 tracks in 3 sessions
    
    def test_session_patterns(self):
        """Test detection of session patterns"""
        # First detect sessions
        self.analyzer.detect_sessions()
        
        # Analyze patterns
        patterns = self.analyzer.session_patterns()
        
        # Check results
        self.assertIn('by_hour', patterns)
        self.assertIn('by_weekday', patterns)
        self.assertIn('by_month', patterns)
        
        # Check hour distribution
        self.assertEqual(patterns['by_hour'][10], 1)  # First session starts at 10
        self.assertEqual(patterns['by_hour'][14], 1)  # Second session starts at 14
        self.assertEqual(patterns['by_hour'][9], 1)   # Third session starts at 9
    
    def test_session_content_analysis(self):
        """Test analysis of session content"""
        # First detect sessions
        self.analyzer.detect_sessions()
        
        # Analyze content
        content = self.analyzer.session_content_analysis()
        
        # Check results
        self.assertIn('avg_artist_continuity', content)
        self.assertIn('avg_unique_artists_ratio', content)
        self.assertIn('session_types', content)


class TestListeningContextPrediction(unittest.TestCase):
    """Test cases for Listening Context Prediction feature"""
    
    def setUp(self):
        """Set up test data"""
        # Create a sample DataFrame with features needed for context prediction
        self.df = pd.DataFrame({
            'endTime': pd.to_datetime([
                '2022-01-03 07:00:00',  # Monday morning (workout)
                '2022-01-03 12:00:00',  # Monday noon (work)
                '2022-01-03 18:00:00',  # Monday evening (commute)
                '2022-01-03 22:00:00',  # Monday night (relaxation)
                '2022-01-08 21:00:00',  # Saturday night (party)
            ]),
            'artistName': ['Artist A', 'Artist B', 'Artist C', 'Artist D', 'Artist E'],
            'trackName': [f'Track {i+1}' for i in range(5)],
            'msPlayed': [240000, 180000, 210000, 195000, 225000]
        })
        
        # Add required columns
        self.df['minutes_played'] = self.df['msPlayed'] / 60000
        self.df['hour'] = self.df['endTime'].dt.hour
        self.df['weekday'] = self.df['endTime'].dt.dayofweek
        
        # Add audio features
        self.df['energy'] = [0.9, 0.4, 0.6, 0.3, 0.8]
        self.df['tempo'] = [160, 100, 120, 80, 140]
        
        # Create analyzer with mock data
        self.analyzer = SpotifyAnalyzer.__new__(SpotifyAnalyzer)
        self.analyzer.df = self.df
    
    def test_categorize_listening_contexts(self):
        """Test categorization of listening contexts"""
        # Categorize contexts
        self.analyzer.categorize_listening_contexts()
        
        # Check if context column was added
        self.assertIn('context', self.analyzer.df.columns)
        
        # Check context assignments
        contexts = self.analyzer.df['context'].tolist()
        expected_contexts = ['workout', 'work', 'commute', 'relaxation', 'party']
        self.assertEqual(contexts, expected_contexts)
    
    def test_context_statistics(self):
        """Test calculation of context statistics"""
        # First categorize contexts
        self.analyzer.categorize_listening_contexts()
        
        # Calculate statistics
        stats = self.analyzer.context_statistics()
        
        # Check results
        self.assertIn('distribution', stats)
        self.assertIn('by_time', stats)
        self.assertIn('by_hour', stats)
        self.assertIn('by_weekday', stats)
        
        # Check distribution
        for context in ['workout', 'work', 'commute', 'relaxation', 'party']:
            self.assertIn(context, stats['distribution'])
            self.assertEqual(stats['distribution'][context], 0.2)  # Each context appears once
    
    def test_train_context_predictor(self):
        """Test training of context predictor"""
        # This test requires scikit-learn
        # If available in the environment, we can test the model training
        try:
            from sklearn.tree import DecisionTreeClassifier
            
            # First categorize contexts
            self.analyzer.categorize_listening_contexts()
            
            # Train predictor
            model = self.analyzer.train_context_predictor()
            
            # Check if model was created
            self.assertIsNotNone(model)
            self.assertTrue(hasattr(self.analyzer, 'context_model'))
            self.assertTrue(hasattr(self.analyzer, 'context_features'))
            
        except ImportError:
            # Skip test if scikit-learn is not available
            self.skipTest("scikit-learn not available")
    
    def test_predict_context(self):
        """Test prediction of listening context"""
        # This test requires scikit-learn
        try:
            from sklearn.tree import DecisionTreeClassifier
            
            # First categorize contexts and train model
            self.analyzer.categorize_listening_contexts()
            self.analyzer.train_context_predictor()
            
            # Test predictions
            workout_context = self.analyzer.predict_context(
                energy=0.85, tempo=150, hour=7, weekday=0
            )
            self.assertEqual(workout_context, 'workout')
            
            relaxation_context = self.analyzer.predict_context(
                energy=0.2, tempo=85, hour=22, weekday=3
            )
            self.assertEqual(relaxation_context, 'relaxation')
            
        except ImportError:
            # Skip test if scikit-learn is not available
            self.skipTest("scikit-learn not available")


if __name__ == '__main__':
    unittest.main()