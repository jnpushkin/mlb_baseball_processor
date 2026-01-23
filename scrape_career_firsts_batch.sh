#!/bin/bash
# Career Firsts Batch Scraper
# Runs the scraper multiple times with delays between rate limit errors
# Usage: ./scrape_career_firsts_batch.sh [number_of_attempts]

cd "$(dirname "$0")"

ATTEMPTS=${1:-20}  # Default 20 attempts
DELAY_BETWEEN=900  # 15 minutes between attempts

echo "Starting career firsts batch scraper"
echo "Will make $ATTEMPTS attempts with ${DELAY_BETWEEN}s delays between rate limits"
echo "Press Ctrl+C to stop"
echo ""

for i in $(seq 1 $ATTEMPTS); do
    echo "=========================================="
    echo "Attempt $i of $ATTEMPTS - $(date)"
    echo "=========================================="

    python3 -u -m baseball_processor.scrapers.career_firsts_scraper --delay 3.1 2>&1

    EXIT_CODE=$?

    # Check how many are cached
    CACHED=$(python3 -c "import json; print(len(json.load(open('cache/career_firsts/career_firsts.json'))))" 2>/dev/null || echo "?")
    echo ""
    echo "Currently cached: $CACHED players"

    if [ "$CACHED" = "2281" ]; then
        echo "All players scraped! Done."
        break
    fi

    if [ $i -lt $ATTEMPTS ]; then
        echo "Waiting ${DELAY_BETWEEN}s before next attempt..."
        sleep $DELAY_BETWEEN
    fi
done

echo ""
echo "Batch scraping complete."
echo "Final cache size: $(python3 -c "import json; print(len(json.load(open('cache/career_firsts/career_firsts.json'))))" 2>/dev/null) players"
