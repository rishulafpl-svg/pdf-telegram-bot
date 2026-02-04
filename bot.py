#!/usr/bin/env python3
"""
Telegram PDF Bot - Railway.app Version
Auto-uploads PDFs to Google Drive
"""

import os
import time
import asyncio
import requests
import base64
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# ============================================
# CONFIG
# ============================================

BOT_TOKEN = '8463828441:AAExeLSEkpCQre2FaWmLfz1VnTOKV_RGcH8'
YOUR_USER_ID = 1345952228
APPS_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbxAg_JEoCPxUvVv_2fu6VoHLaMNPcmjvio6Ii5uUUQVwM7_CLyrkoGmw1qhPJEPZkGL/exec'

os.makedirs('downloads', exist_ok=True)

print("="*60)
print("🤖 PDF BOT - Railway.app")
print("="*60)
print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
print(f"✅ User ID: {YOUR_USER_ID}")
print(f"✅ Apps Script: {APPS_SCRIPT_URL[:50]}...")
print("="*60 + "\n")

# ============================================
# HELPER FUNCTIONS
# ============================================

def clear_bot_conflicts():
    """Clear webhook and pending updates"""
    print("🔄 Clearing bot conflicts...")
    
    try:
        requests.get(
            f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true',
            timeout=10
        )
        print("✅ Webhook cleared")
        time.sleep(1)
        
        r = requests.get(
            f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset=-1',
            timeout=10
        )
        
        if r.status_code == 200:
            data = r.json()
            if data.get('result'):
                latest_id = max([u['update_id'] for u in data['result']]) + 1
                requests.get(
                    f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={latest_id}',
                    timeout=10
                )
                print("✅ Cleared pending updates")
        
        print("✅ Bot reset complete!\n")
        
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}\n")

# ============================================
# TELEGRAM HANDLERS
# ============================================

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF uploads"""
    try:
        if update.effective_user.id != YOUR_USER_ID:
            await update.message.reply_text("❌ Unauthorized")
            return
        
        document = update.message.document
        file_name = document.file_name or f"file_{document.file_id}.pdf"
        chat_id = update.effective_chat.id
        
        print(f"\n{'='*60}")
        print(f"📥 New file: {file_name}")
        print(f"👤 From: {update.effective_user.id}")
        print(f"{'='*60}\n")
        
        # Step 1: Download
        status_msg = await update.message.reply_text(
            f"📥 **Downloading...**\n`{file_name}`",
            parse_mode='Markdown'
        )
        
        file = await context.bot.get_file(document.file_id)
        file_path = f"downloads/{file_name}"
        await file.download_to_drive(file_path)
        
        print(f"✅ Downloaded: {file_name}")
        
        # Step 2: Read and encode file
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        file_base64 = base64.b64encode(file_data).decode('utf-8')
        print(f"📦 Encoded: {len(file_base64)} chars")
        
        # Step 3: Upload to Drive via Apps Script
        await status_msg.edit_text(
            f"☁️ **Uploading to Drive...**\n`{file_name}`",
            parse_mode='Markdown'
        )
        
        print("🚀 Calling Apps Script...")
        
        try:
            response = requests.post(
                APPS_SCRIPT_URL,
                json={
                    'trigger': 'upload_and_process',
                    'source': 'telegram_railway',
                    'file_name': file_name,
                    'file_data': file_base64
                },
                timeout=180
            )
            
            print(f"📡 Response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                message = result.get('message', 'Done!')
                
                print(f"✅ Success: {message}")
                
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ **Complete!**\n\n{message}",
                    parse_mode='Markdown'
                )
            else:
                print(f"⚠️ Status: {response.status_code}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ Response: {response.status_code}",
                    parse_mode='Markdown'
                )
        
        except requests.exceptions.Timeout:
            print("⏳ Timeout (file may still be processing)")
            await context.bot.send_message(
                chat_id=chat_id,
                text="⏳ **Processing...**\n\nCheck Drive in 1-2 min!",
                parse_mode='Markdown'
            )
        
        except Exception as e:
            print(f"❌ Error: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Error: {str(e)[:100]}",
                parse_mode='Markdown'
            )
        
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Cleaned: {file_path}\n")
    
    except Exception as e:
        print(f"❌ Handler Error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle commands"""
    if update.effective_user.id != YOUR_USER_ID:
        return
    
    text = update.message.text.lower()
    
    if text in ['/start', 'hi', 'hello']:
        await update.message.reply_text(
            "👋 **PDF Bot - Railway**\n\n"
            "📄 Send PDF → Auto upload to Drive!\n"
            "🤖 Apps Script processes daily at 9 AM\n\n"
            "🚀 24/7 Running on Railway.app!",
            parse_mode='Markdown'
        )
    
    elif text == '/status':
        await update.message.reply_text(
            "✅ **Bot Status: Online**\n\n"
            "🏃 Running on Railway.app\n"
            "⚡ Ready to process PDFs!",
            parse_mode='Markdown'
        )


# ============================================
# MAIN
# ============================================

async def main():
    """Initialize and run bot"""
    
    print("🚀 Starting bot...\n")
    
    # Clear conflicts
    clear_bot_conflicts()
    
    # Create app
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.TEXT, handle_text))
    
    print("✅ Bot initialized!")
    print("⚡ BOT IS NOW RUNNING 24/7!\n")
    
    # Start
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    # Keep alive
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopped")
        await app.stop()


if __name__ == '__main__':
    print("🔥 Railway.app Telegram Bot Starting...\n")
    asyncio.run(main())
