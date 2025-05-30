#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Set Redis URL for local development
export REDIS_URL=redis://localhost:6379/0

# Set OpenAI API key - REPLACE WITH YOUR ACTUAL KEY
export OPENAI_API_KEY="your-openai-api-key-here"

# Check if OpenAI API key is set
if [ "$OPENAI_API_KEY" = "your-openai-api-key-here" ] || [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: OPENAI_API_KEY is not set or still has placeholder value!"
    echo "Please edit this script and replace 'your-openai-api-key-here' with your actual OpenAI API key"
    echo "Or set it as an environment variable before running this script:"
    echo "  export OPENAI_API_KEY='your-actual-key'"
    echo ""
    echo "The worker will start but API calls will fail without a valid key."
    echo ""
fi

# Run the worker
echo "Starting worker with local Redis configuration..."
python run_worker.py 