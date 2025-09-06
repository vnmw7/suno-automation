"""AI Review Configuration

This module contains configuration settings for the AI review system,
including rate limiting and model selection options.
"""

# Model Configuration
# Switch between 'gemini-2.5-pro' and 'gemini-2.5-flash' based on your needs
# Pro: More accurate but only 2 RPM on free tier
# Flash: Slightly less accurate but 15 RPM on free tier
USE_FLASH_MODEL = False  # Set to True to use Flash model with higher rate limits

# Rate Limiting Configuration
# These values are for the free tier. Update if you have a paid plan.
if USE_FLASH_MODEL:
    # Gemini 2.5 Flash limits (free tier)
    REQUESTS_PER_MINUTE = 15
    DELAY_BETWEEN_API_CALLS = 4  # seconds (60/15) - Used between upload, 1st prompt, 2nd prompt
    DELAY_BETWEEN_SONGS = 10  # seconds - Used between different song reviews
else:
    # Gemini 2.5 Pro limits (free tier) 
    REQUESTS_PER_MINUTE = 2
    DELAY_BETWEEN_API_CALLS = 31  # seconds (60/2) - Used between upload, 1st prompt, 2nd prompt
    DELAY_BETWEEN_SONGS = 31  # seconds - Used between different song reviews
    
# Note: Each song review makes 3 API calls:
# 1. Upload file to Google AI
# 2. First prompt (transcription and initial review)
# 3. Second prompt (lyrics comparison)
# DELAY_BETWEEN_API_CALLS is applied after each of these to prevent quota errors

# Paid tier limits (if you upgrade)
# Pro: 360 RPM, Flash: 1000 RPM
PAID_TIER = False
if PAID_TIER:
    if USE_FLASH_MODEL:
        REQUESTS_PER_MINUTE = 1000
        DELAY_BETWEEN_API_CALLS = 0.06  # seconds
        DELAY_BETWEEN_SONGS = 0.15  # seconds
    else:
        REQUESTS_PER_MINUTE = 360
        DELAY_BETWEEN_API_CALLS = 0.17  # seconds  
        DELAY_BETWEEN_SONGS = 0.4  # seconds

# Processing mode
PROCESS_SEQUENTIALLY = True  # Set to False to process in parallel (only with paid tier)