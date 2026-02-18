#!/usr/bin/env python3
"""
Telegram PDF Bot - Railway.app (Final Stable Version)
"""

import os
import base64
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes

# ===== CONFIG =====
BOT_TOKEN = '8463828441:AAExeLSEkpCQre2FaWmLfz1VnTOKV_RGcH8'
APPS_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbyVjl1CfmAHaCZY2khharNDGHZew-UTwe5wXy-hTVhNjIotgJZJVs653FB884Zr4BvV/exec'
YOUR_USER_ID = 1345952228

os.makedirs('downloads', exist_ok=True)


# ===== HANDLERS =====

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_USER_ID:
        return
    await update.message.reply_text("👋 PDF Bot Live.\nSend a PDF.")


async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    file_name = None
    status_msg = None

    try:
        if update.effective_user.id != YOUR_USER_ID:
            await update.message.reply_text("❌ Unauthorized")
            return

        document = update.message.document
        file_name = document.file_name or f"{document.file_id}.pdf"

        # ===== SINGLE LIVE MESSAGE =====
        status_msg = await update.message.reply_text(
            f"📥 Downloading...\n{file_name}"
        )

        # ===== DOWNLOAD =====
        file = await context.bot.get_file(document.file_id)
        file_path = f"downloads/{file_name}"
        await file.download_to_drive(file_path)

        # ===== ENCODE =====
        await status_msg.edit_text(
            f"🔄 Encoding...\n{file_name}"
        )

        with open(file_path, 'rb') as f:
            file_base64 = base64.b64encode(f.read()).decode('utf-8')

        # ===== UPLOAD =====
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
            timeout=180
        )

        if response.status_code != 200:
            await status_msg.edit_text(
                f"❌ Error processing:\n\n📄 {file_name}\n\nServer Error {response.status_code}"
            )
            return

        result = response.json()

        if result.get("status") != "success":
            await status_msg.edit_text(
                f"❌ Error processing:\n\n📄 {file_name}\n\n{result.get('message')}"
            )
            return

        # ===== SUCCESS =====
        summary_link = result.get("docUrl") or (
            f"https://docs.google.com/document/d/{result.get('docId')}"
            if result.get("docId") else ""
        )

        final_message = (
            f"✅ Success!\n\n"
            f"📄 {file_name}\n"
            f"Uploaded and summarized\n\n"
            f"📘 Daily Summary:\n{summary_link}"
        )

        await status_msg.edit_text(final_message)

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:

        error_str = str(e)

        # Clean Gemini 429
        if "429" in error_str:
            clean_error = (
                "Gemini API quota exceeded (429).\n"
                "Check billing or reduce request frequency."
            )
        elif "401" in error_str:
            clean_error = "Authentication error (401). Check API key."
        else:
            clean_error = error_str.split("\n")[0][:300]

        final_error = (
            f"❌ Error processing:\n\n"
            f"📄 {file_name if file_name else 'Unknown File'}\n\n"
            f"{clean_error}"
        )

        if status_msg:
            await status_msg.edit_text(final_error)
        else:
            await update.message.reply_text(final_error)


# ===== MAIN =====

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
