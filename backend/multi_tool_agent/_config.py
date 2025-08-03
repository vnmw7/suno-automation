# TODO: Move THINKING_BUDGET to environment variables for better security and flexibility
# TOFIX: Add model fallback options if primary model is unavailable
# TODO: Add configuration for:
# - Retry attempts
# - Timeout values
# - Temperature settings
# - Max tokens

# AI Model Configuration
AI_MODEL_LITE = "gemini-2.5-flash"
AI_MODEL_PRO = "gemini-2.5-pro"

# Thinking Budget Configuration
# Controls the number of tokens the model uses for internal reasoning before responding
# For Gemini 2.5 Pro: Valid range is 128-32768 tokens
# Higher values allow more sophisticated reasoning but increase costs
# Current setting (24576) allows extensive reasoning for complex Bible analysis
THINKING_BUDGET_LITE = 24576
THINKING_BUDGET_PRO = 32768
# TODO: Add validation to ensure THINKING_BUDGET is within the valid range (128-32768 tokens)
