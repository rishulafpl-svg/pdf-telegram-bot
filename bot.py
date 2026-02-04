import os
import base64
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# ===== CONFIG =====
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
APPS_SCRIPT_URL = os.getenv('APPS_SCRIPT_URL')

print(f'🔑 Bot Token: {TELEGRAM_TOKEN[:10]}...')
print(f'🔗 Apps Script URL: {APPS_SCRIPT_URL}')

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF documents"""
    try:
        print(f'📥 PDF received from user {update.message.from_user.id}')
        await update.message.reply_text('📥 PDF Received! Processing...')
        
        # Get document
        document = update.message.document
        file_name = document.file_name
        file_size = document.file_size
        
        print(f'📄 File: {file_name} ({file_size} bytes)')
        
        # Size check (50 MB limit)
        if file_size > 50 * 1024 * 1024:
            await update.message.reply_text('❌ File too large! Max 50 MB.')
            return
        
        await update.message.reply_text(f'📥 Downloading: {file_name}...')
        
        # Download file
        file = await context.bot.get_file(document.file_id)
        file_bytes = await file.download_as_bytearray()
        
        print(f'✅ Downloaded: {len(file_bytes)} bytes')
        await update.message.reply_text(f'✅ Downloaded: {file_name}\n📦 Size: {len(file_bytes)} bytes')
        
        # Encode to base64
        print('🔄 Encoding to base64...')
        file_base64 = base64.b64encode(file_bytes).decode('utf-8')
        
        print(f'✅ Encoded: {len(file_base64)} chars')
        await update.message.reply_text(f'📦 Encoded: {len(file_base64)} chars')
        
        # Prepare payload
        payload = {
            'trigger': 'upload_and_process',
            'file_name': file_name,
            'file_data': file_base64
        }
        
        print('🚀 Sending to Apps Script...')
        await update.message.reply_text('🚀 Calling Apps Script...')
        
        # Send POST request
        print(f'📡 POST to: {APPS_SCRIPT_URL}')
        response = requests.post(
            APPS_SCRIPT_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f'📨 Response status: {response.status_code}')
        print(f'📨 Response body: {response.text}')
        
        await update.message.reply_text(f'📨 Response: {response.status_code}')
        
        # Parse response
        if response.status_code == 200:
            try:
                result = response.json()
                message = result.get('message', 'Success!')
                url = result.get('url', '')
                
                reply = f'✅ Success: {message}'
                if url:
                    reply += f'\n\n🔗 Drive Link:\n{url}'
                
                await update.message.reply_text(reply)
                print(f'✅ Success: {message}')
                
            except Exception as e:
                await update.message.reply_text(f'✅ Upload complete!\n\n{response.text}')
        else:
            error_msg = f'❌ Apps Script Error: {response.status_code}\n\n{response.text}'
            await update.message.reply_text(error_msg)
            print(f'❌ Error: {error_msg}')
        
    except Exception as e:
        error = str(e)
        print(f'❌ Exception: {error}')
        await update.message.reply_text(f'❌ Error: {error}')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    await update.message.reply_text(
        '👋 Welcome to PDF BOT!\n\n'
        '📄 Send me a PDF file and I will:\n'
        '1. Upload it to Google Drive\n'
        '2. Process it with AI\n\n'
        '🤖 Bot is running on Railway.app'
    )

def main():
    """Start the bot"""
    if not TELEGRAM_TOKEN:
        print('❌ TELEGRAM_BOT_TOKEN not set!')
        return
    
    if not APPS_SCRIPT_URL:
        print('❌ APPS_SCRIPT_URL not set!')
        return
    
    print('🚀 Building application...')
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    print('📋 Adding handlers...')
    # Handle PDF documents
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    
    # Handle text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print('🔥 PDF BOT STARTING...')
    print('📡 Railway.app Telegram Bot - Ready!')
    print(f'🔗 Apps Script URL configured')
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    
    # Start polling
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
