#!/usr/bin/env python3
"""
Telegram PDF Bot - Railway.app (CLEAN FIXED VERSION)
"""

import os
import base64
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes

# ===== CONFIG =====
BOT_TOKEN = '8463828441:AAExeLSEkpCQre2FaWmLfz1VnTOKV_RGcH8'
APPS_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbzEB5Ddy4wV6LcSYb869YC4LJ2Pr8DC4oV53FpXJLQjagdndSGYUYT0tgVyG2nFgCUN/exec'
YOUR_USER_ID = 1345952228

os.makedirs('downloads', exist_ok=True)

print("="*60)
print("🤖 PDF BOT - Railway.app (v3 CLEAN)")
print("="*60)
print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
print(f"✅ Apps Script: {APPS_SCRIPT_URL[:50]}...")
print(f"✅ User ID: {YOUR_USER_ID}")
print("="*60)


# ===== HELPERS =====
def clear_webhook():
    try:
        requests.get(
            f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook',
            timeout=10
        )
        print("✅ Webhook cleared\n")
    except Exception as e:
        print(f"⚠️ Webhook: {e}\n")


# ===== HANDLERS =====
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_USER_ID:
        return
    
    await update.message.reply_text(
        "👋 PDF Bot Ready.\n\nSend a PDF."
    )


async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        if update.effective_user.id != YOUR_USER_ID:
            await update.message.reply_text("❌ Unauthorized")
            return
        
        document = update.message.document
        file_name = document.file_name or f"file_{document.file_id}.pdf"
        
        print(f"\n📥 New file: {file_name}")
        
        # Download
        status_msg = await update.message.reply_text("📥 Downloading...")
        
        file = await context.bot.get_file(document.file_id)
        file_path = f"downloads/{file_name}"
        await file.download_to_drive(file_path)
        
        print(f"✅ Downloaded: {file_name}")
        
        # Encode
        await status_msg.edit_text("🔄 Encoding...")
        
        with open(file_path, 'rb') as f:
            file_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        print(f"✅ Encoded: {len(file_base64)} chars")
        
        # Upload
        await status_msg.edit_text("☁️ Uploading...")
        
        response = requests.post(
            APPS_SCRIPT_URL,
            json={
                'trigger': 'upload_and_process',
                'source': 'telegram_railway',
                'file_name': file_name,
                'file_data': file_base64
            },
            headers={'Content-Type': 'application/json'},
            timeout=180
        )
        
        print(f"📨 Status: {response.status_code}")
        
        if response.status_code == 200:

            try:
                result = response.json()

                if result.get("status") == "success":
                    # Use EXACT message from Apps Script
                    await update.message.reply_text(result.get("message"))
                    print("✅ Message delivered to Telegram")
                else:
                    await update.message.reply_text(
                        f"❌ Error:\n{result.get('message')}"
                    )

            except Exception as parse_error:
                print("❌ JSON parse failed:", parse_error)
                await update.message.reply_text("❌ Unexpected server response.")

        else:
            await update.message.reply_text(
                f"⚠️ Server Error {response.status_code}"
            )
            print(f"❌ Error: {response.status_code}")
        
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Cleaned: {file_path}\n")
    
    except Exception as e:
        error_str = str(e)
        print(f"❌ Exception: {error_str}")
        await update.message.reply_text(f"❌ Error: {error_str[:200]}")


# ===== MAIN =====
def main():

    print("\n🚀 Starting bot...\n")
    
    clear_webhook()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    
    print("✅ Bot initialized!")
    print("⚡ BOT IS NOW RUNNING 24/7!\n")
    
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == '__main__':
    main()
