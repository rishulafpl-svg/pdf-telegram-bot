#!/usr/bin/env python3
"""
Telegram PDF Bot - Railway.app (FIXED 401)
"""

import os
import base64
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes

# ===== CONFIG =====
BOT_TOKEN = '8463828441:AAExeLSEkpCQre2FaWmLfz1VnTOKV_RGcH8'
APPS_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbw3GeKYPq3VflVb-wVcpS5n8wpClRNolK6lU45idZbwbid9H9zT7VXn6ik-yOqOFzfG/exec'
YOUR_USER_ID = 1345952228

os.makedirs('downloads', exist_ok=True)

print("="*60)
print("🤖 PDF BOT - Railway.app (v2)")
print("="*60)
print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
print(f"✅ Apps Script: {APPS_SCRIPT_URL[:50]}...")
print(f"✅ User ID: {YOUR_USER_ID}")
print("="*60)

# ===== HELPERS =====
def clear_webhook():
    """Clear webhook"""
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
    """Handle /start"""
    if update.effective_user.id != YOUR_USER_ID:
        return
    
    await update.message.reply_text(
        "👋 **PDF Bot - Railway v2**\n\n"
        "📄 Send PDF → Auto upload!\n"
        "🤖 Running 24/7 on Railway.app!\n\n"
        "✅ 401 Error Fixed!",
        parse_mode='Markdown'
    )

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF uploads"""
    try:
        if update.effective_user.id != YOUR_USER_ID:
            await update.message.reply_text("❌ Unauthorized")
            return
        
        document = update.message.document
        file_name = document.file_name or f"file_{document.file_id}.pdf"
        
        print(f"\n📥 New file: {file_name}")
        
        # Download
        status_msg = await update.message.reply_text(
            f"📥 **Downloading...**\n`{file_name}`",
            parse_mode='Markdown'
        )
        
        file = await context.bot.get_file(document.file_id)
        file_path = f"downloads/{file_name}"
        await file.download_to_drive(file_path)
        
        print(f"✅ Downloaded: {file_name}")
        
        # Encode
        await status_msg.edit_text(
            f"🔄 **Encoding...**\n`{file_name}`",
            parse_mode='Markdown'
        )
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        file_base64 = base64.b64encode(file_data).decode('utf-8')
        print(f"✅ Encoded: {len(file_base64)} chars")
        
        # Upload
        await status_msg.edit_text(
            f"☁️ **Uploading to Drive...**\n`{file_name}`",
            parse_mode='Markdown'
        )
        
        print(f"🚀 POST to: {APPS_SCRIPT_URL}")
        print(f"📦 Payload size: {len(file_base64)} chars")
        
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
        print(f"📨 Body: {response.text[:500]}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                message = result.get('message', 'Done!')
                url = result.get('url', '')
                
                reply = f"✅ **Success!**\n\n{message}"
                if url:
                    reply += f"\n\n🔗 [Open in Drive]({url})"
                
                await update.message.reply_text(reply, parse_mode='Markdown')
                print(f"✅ Success: {message}")
                
            except:
                await update.message.reply_text(
                    f"✅ **Upload Complete!**\n\n{response.text[:300]}",
                    parse_mode='Markdown'
                )
        else:
            error_msg = f"⚠️ **Error {response.status_code}**\n\n`{response.text[:300]}`"
            await update.message.reply_text(error_msg, parse_mode='Markdown')
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
    """Run bot"""
    print("\n🚀 Starting bot...\n")
    
    clear_webhook()
    
    # Validate URL
    if 'YOUR_NEW' in APPS_SCRIPT_URL:
        print("❌ ERROR: Update APPS_SCRIPT_URL first!")
        print("🔗 Get new URL from Apps Script deployment\n")
        return
    
    # Create app
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    
    print("✅ Bot initialized!")
    print("⚡ BOT IS NOW RUNNING 24/7!\n")
    
    # Run
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
