"""
Title-based vector deduplication using SentenceTransformer.
Computes cosine similarity between article titles and removes duplicates.
"""

import json
import sys
import os
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class NewsDeduplicator:
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize the deduplicator with SentenceTransformer model.
        
        Args:
            similarity_threshold: Cosine similarity threshold for considering articles as duplicates
        """
        self.similarity_threshold = similarity_threshold
        print("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully!")
    
    def compute_title_embeddings(self, articles: List[Dict]) -> np.ndarray:
        """
        Compute embeddings for all article titles.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            numpy array of title embeddings
        """
        titles = [article.get('title', '') for article in articles]
        embeddings = self.model.encode(titles)
        return embeddings
    
    def find_duplicates(self, embeddings: np.ndarray) -> List[int]:
        """
        Find duplicate articles based on cosine similarity of title embeddings.
        
        Args:
            embeddings: Array of title embeddings
            
        Returns:
            List of indices to remove (duplicate articles)
        """
        similarity_matrix = cosine_similarity(embeddings)
        duplicates_to_remove = set()
        
        n_articles = len(embeddings)
        for i in range(n_articles):
            if i in duplicates_to_remove:
                continue
                
            for j in range(i + 1, n_articles):
                if j in duplicates_to_remove:
                    continue
                    
                similarity = similarity_matrix[i][j]
                if similarity >= self.similarity_threshold:
                    # Keep the first occurrence (i), remove the duplicate (j)
                    duplicates_to_remove.add(j)
                    print(f"Duplicate found (similarity: {similarity:.3f}): "
                          f"Removing article {j}, keeping article {i}")
        
        return list(duplicates_to_remove)
    
    def deduplicate_articles(self, input_file: str, output_file: str) -> List[Dict]:
        """
        Deduplicate articles from input file and save to output file.
        
        Args:
            input_file: Path to input JSON file with raw articles
            output_file: Path to output JSON file for deduplicated articles
            
        Returns:
            List of deduplicated articles
        """
        # Load articles from input file
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        if not articles:
            print("No articles found in input file.")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return []
        
        print(f"Processing {len(articles)} articles for deduplication...")
        
        # Compute title embeddings
        embeddings = self.compute_title_embeddings(articles)
        
        # Find duplicates
        duplicates_to_remove = self.find_duplicates(embeddings)
        
        # Remove duplicates (keep first occurrence)
        deduplicated_articles = []
        for i, article in enumerate(articles):
            if i not in duplicates_to_remove:
                deduplicated_articles.append(article)
        
        # Save deduplicated articles
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(deduplicated_articles, f, ensure_ascii=False, indent=2)
        
        removed_count = len(articles) - len(deduplicated_articles)
        print(f"Deduplication completed:")
        print(f"  Original articles: {len(articles)}")
        print(f"  Duplicates removed: {removed_count}")
        print(f"  Final articles: {len(deduplicated_articles)}")
        print(f"  Results saved to: {output_file}")
        
        return deduplicated_articles


def main():
    """Command line interface."""
    if len(sys.argv) != 2:
        print("Usage: python -m news_bot.dedup YYYY-MM-DD")
        sys.exit(1)
    
    date = sys.argv[1]
    
    # Validate date format
    try:
        import datetime
        datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        print("Error: Date must be in YYYY-MM-DD format")
        sys.exit(1)
    
    input_file = f"raw_{date}.json"
    output_file = f"dedup_{date}.json"
    
    try:
        deduplicator = NewsDeduplicator(similarity_threshold=0.85)
        deduplicated_articles = deduplicator.deduplicate_articles(input_file, output_file)
        
        if len(deduplicated_articles) > 0:
            print(f"✅ Success: Deduplicated to {len(deduplicated_articles)} unique articles")
        else:
            print("⚠️  Warning: No articles remaining after deduplication")
            
    except Exception as e:
        print(f"❌ Error during deduplication: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()