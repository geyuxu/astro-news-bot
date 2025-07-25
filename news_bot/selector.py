# TODO: Implement topic-based news selection
# Load dedup_{date}.json, apply topic weights: {"AI":2,"Tech":2,"Economy":2}
# Use OpenAI GPT-4o to select 6 best news items based on topic weights
# Fallback to random 6 items on LLM failure, save to select_{date}.json