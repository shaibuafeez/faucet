import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from collections import defaultdict
import time

# Replace with your Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7406720444:AAF5RTlVIwhtK4w6kg-yasi-gWehsOQ2tiI"

# SUI Testnet Faucet API endpoint
FAUCET_URL = "https://faucet.testnet.sui.io/gas"

# Update these constants
RATE_LIMIT_SECONDS = 86400  # 24 hours (1 day)
MAX_REQUESTS_PER_PERIOD = 3

# Add this line to define user_requests
user_requests = defaultdict(lambda: {"last_request": 0, "count": 0})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to the SUI Testnet Faucet Bot! Send me your SUI wallet address to receive testnet tokens."
    )

async def handle_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    wallet_address = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Basic validation of the wallet address
    if not wallet_address.startswith("0x") or len(wallet_address) != 66:
        await update.message.reply_text("Invalid SUI wallet address. Please try again.")
        return

    # Check rate limit
    current_time = time.time()
    if current_time - user_requests[user_id]["last_request"] > RATE_LIMIT_SECONDS:
        user_requests[user_id] = {"last_request": current_time, "count": 1}
    else:
        user_requests[user_id]["count"] += 1

    if user_requests[user_id]["count"] > MAX_REQUESTS_PER_PERIOD:
        time_left = int(RATE_LIMIT_SECONDS - (current_time - user_requests[user_id]["last_request"]))
        hours, remainder = divmod(time_left, 3600)
        minutes, seconds = divmod(remainder, 60)
        await update.message.reply_text(f"Rate limit exceeded. You can make {MAX_REQUESTS_PER_PERIOD} requests per day. "
                                        f"Please try again in {hours}h {minutes}m {seconds}s.")
        return

    # Request tokens from the faucet
    try:
        response = requests.post(FAUCET_URL, json={"FixedAmountRequest": {"recipient": wallet_address}})
        response.raise_for_status()
        
        remaining_requests = MAX_REQUESTS_PER_PERIOD - user_requests[user_id]["count"]
        await update.message.reply_text(f"Tokens sent successfully! Check your wallet for the new balance. "
                                        f"You have {remaining_requests} requests remaining today.")
    except requests.RequestException as e:
        if e.response and e.response.status_code == 429:
            await update.message.reply_text("The faucet is currently rate-limited. Please try again later.")
        else:
            await update.message.reply_text(f"Error requesting tokens: {str(e)}")

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_address))

    application.run_polling()

if __name__ == "__main__":
    main()
