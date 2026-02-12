#!/usr/bin/env python3
"""
Telegram PDF Bot - Railway.app (Clean Final Version)
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
print("🤖 PDF BOT - Railway (Clean)")
print("="*60)


# ===== HANDLERS =====

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_USER_ID:
        return
    
    await update.message.reply_text("👋 PDF Bot Ready. Send a PDF.")


async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        if update.effective_user.id != YOUR_USER_ID:
            await update.message.reply_text("❌ Unauthorized")
            return
        
        document = update.message.document
        file_name = document.file_name or f"{document.file_id}.pdf"

        print(f"\n📥 New file: {file_name}")

        # ===== SINGLE STATUS MESSAGE =====
        status_msg = await update.message.reply_text(
            f"📥 Downloading...\n{file_name}"
        )

        # Download
        file = await context.bot.get_file(document.file_id)
        file_path = f"downloads/{file_name}"
        await file.download_to_drive(file_path)

        print("✅ Downloaded")

        # Encoding
        await status_msg.edit_text(
            f"🔄 Encoding...\n{file_name}"
        )

        with open(file_path, 'rb') as f:
            file_base64 = base64.b64encode(f.read()).decode('utf-8')

        print("✅ Encoded")

        # Uploading
        await status_msg.edit_text(
            f"☁️ Uploading to Drive...\n{file_name}"
        )

        response = requests.post(
            APPS_SCRIPT_URL,
            json={
                'trigger': 'upload_and_process',
                'file_name': file_name,
                'file_data': file_base64
            },
            headers={'Content-Type': 'application/json'},
            timeout=180
        )

        print(f"📨 Status: {response.status_code}")

        # Final result
        if response.status_code == 200:
            result = response.json()

            if result.get("status") == "success":
                # Replace the SAME message with final result
                await status_msg.edit_text(result.get("message"))
                print("✅ Success sent to Telegram")
            else:
                await status_msg.edit_text(
                    f"❌ Error:\n{result.get('message')}"
                )
        else:
            await status_msg.edit_text(
                f"⚠️ Server Error {response.status_code}"
            )

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
            print("🗑️ File cleaned")

    except Exception as e:
        error_str = str(e)
        print("❌ Exception:", error_str)
        await update.message.reply_text(f"❌ Error: {error_str[:200]}")


# ===== MAIN =====

def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

    print("🚀 Bot Running...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == '__main__':
    main()
