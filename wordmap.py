from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import re
import json

def create_word_map(text, max_words=100, background_color='white'):
    # Clean the text (remove punctuation and convert to lowercase)
    cleaned_text = re.sub(r'[^\w\s]', '', text.lower())
    
    # Count word frequencies
    word_counts = Counter(cleaned_text.split())
    
    # Create the word cloud
    wordcloud = WordCloud(
        max_words=max_words,
        background_color=background_color,
        width=800,
        height=400
    ).generate_from_frequencies(word_counts)
    
    # Display the word cloud
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.show()
    
    # Optionally save the image
    # wordcloud.to_file('wordmap.png')
    
    return wordcloud

    # Write play statistics to output file
lyrics_file = 'lyrics_info.json'
with open(lyrics_file, 'r', encoding='utf-8') as file:
          data = json.load(file)
full_text=""

for entry in data:
    full_text=full_text + (entry['lyricsInfo']['lyrics'])

    
# Example usage
create_word_map(full_text, max_words=100, background_color='white')