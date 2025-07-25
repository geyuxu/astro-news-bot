# TODO: Implement title-based vector deduplication
# Load SentenceTransformer('all-MiniLM-L6-v2')
# Read raw_{date}.json, compute cosine similarity (threshold 0.85)
# Remove duplicates, keep first occurrence, save to dedup_{date}.json