#!/bin/bash
# Script to set up a daily cron job to reset the demo user's books

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESET_SCRIPT="$PROJECT_DIR/reset_demo_user.py"
LOG_FILE="$PROJECT_DIR/demo_reset.log"

# Make the reset script executable
chmod +x "$RESET_SCRIPT"

# Create a temporary crontab file
TEMP_CRONTAB=$(mktemp)

# Export current crontab
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "# New crontab" > "$TEMP_CRONTAB"

# Check if the cron job already exists
if ! grep -q "reset_demo_user.py" "$TEMP_CRONTAB"; then
    # Add the cron job to run daily at 3:00 AM
    echo "# Reset demo user books daily at 3:00 AM" >> "$TEMP_CRONTAB"
    echo "0 3 * * * cd $PROJECT_DIR && $RESET_SCRIPT >> $LOG_FILE 2>&1" >> "$TEMP_CRONTAB"
    
    # Install the new crontab
    crontab "$TEMP_CRONTAB"
    echo "Cron job installed to reset demo user daily at 3:00 AM"
else
    echo "Cron job already exists"
fi

# Clean up
rm "$TEMP_CRONTAB"

echo "Setup complete. The demo user's books will be reset daily at 3:00 AM."
echo "Logs will be written to: $LOG_FILE"
