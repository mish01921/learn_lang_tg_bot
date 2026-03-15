import os
import logging
import asyncio
import base64
import re
from io import BytesIO
from gtts import gTTS
from aiogram import Bot
from aiogram.types import FSInputFile, Message

from src.database.models import get_voice_file_id, save_voice_file_id
from src.data.api_words import get_word_data, _get_http_session
from src.core.config import GEMINI_API_KEY
from src.bot.ui import get_pronunciation_feedback_keyboard

async def send_word_pronunciation(bot: Bot, chat_id: int, word: str, accent: str = "us"):
    """Sends word pronunciation as a voice message, with caching and TTS fallback. Supports 'us' and 'uk' accents."""
    word = word.strip().lower()
    cache_key = f"{word}_{accent}"
    
    # 1. Check cache
    file_id = await get_voice_file_id(cache_key)
    if file_id:
        try:
            return await bot.send_voice(chat_id, file_id)
        except Exception:
            logging.warning(f"Cached file_id {file_id} for word '{cache_key}' is invalid or expired.")

    # 2. Use gTTS with specific accent
    # US: tld='com', UK: tld='co.uk'
    tld = 'co.uk' if accent == "uk" else 'com'
    temp_filename = f"temp_pron_{accent}_{word}_{chat_id}.mp3"
    
    try:
        tts = gTTS(text=word, lang='en', tld=tld)
        await asyncio.to_thread(tts.save, temp_filename)
        
        voice_file = FSInputFile(temp_filename)
        msg = await bot.send_voice(chat_id, voice_file)
        
        if msg.voice:
            await save_voice_file_id(cache_key, msg.voice.file_id)
        return msg
    except Exception:
        logging.exception(f"gTTS {accent} failed for word '{word}'")
        await bot.send_message(chat_id, f"⚠️ Չհաջողվեց բեռնել {accent.upper()} արտասանությունը։")
    finally:
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except Exception:
                pass

async def verify_pronunciation_with_ai(bot: Bot, message: Message, target_word: str):
    """Downloads voice from Telegram and sends to Gemini for ELSA-style analysis."""
    if not GEMINI_API_KEY:
        return await message.answer("⚠️ Gemini API-ն կազմաձևված չէ։")

    target_word = target_word.strip().lower()
    voice = message.voice
    if not voice:
        return await message.answer("⚠️ Ձայնային հաղորդագրություն չի գտնվել։")

    status_msg = await message.answer("🧐 Լսում եմ և վերլուծում...")

    try:
        # 1. Download voice file
        file_info = await bot.get_file(voice.file_id)
        file_path = file_info.file_path
        
        # Download as BytesIO
        audio_content = await bot.download_file(file_path)
        audio_data = audio_content.read()
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')

        # 2. Prepare Gemini prompt
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-3-flash-preview:generateContent?key={GEMINI_API_KEY}"
        )
        
        prompt = (
            f"You are a world-class English pronunciation coach focusing on General American accent.\n"
            f"The user is trying to pronounce the English word: '{target_word}'.\n"
            f"Please listen to the attached audio and provide a detailed analysis based STRICTLY on American English standards:\n"
            f"1. **Score**: Give a score from 0 to 100.\n"
            f"2. **Specific Errors**: Identify exactly which letters or phonemes were wrong according to American pronunciation.\n"
            f"3. **Articulation Guide**: For each error, provide detailed physical instructions:\n"
            f"   - **Tongue Position**: Where should the tongue be?\n"
            f"   - **Mouth/Lip Shape**: Should the mouth be open, lips rounded, etc.?\n"
            f"   - **Airflow**: Is it a voiced or voiceless sound? How should the air flow?\n"
            f"4. **Armenian Comparison**: Compare the tricky sounds to Armenian sounds to help the user understand better.\n"
            f"5. **Visual Guide Link**: If the user needs to see the mouth animation, suggest they look at the interactive Google Pronunciation tool: https://www.google.com/search?q=how+to+pronounce+{target_word}\n"
            f"6. **Format**: Use clear sections with emojis for Telegram (Markdown).\n\n"
            f"IMPORTANT: Respond in Armenian (հայերեն), but keep the English technical terms in English. Remind the user that you are evaluating based on American accent."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "audio/ogg",
                                "data": audio_b64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "topP": 0.8,
                "topK": 40
            }
        }

        # 3. Request analysis
        session = await _get_http_session()
        async with session.post(url, json=payload, timeout=30) as res:
            if res.status != 200:
                error_body = await res.text()
                logging.error(f"Gemini Audio API error: {res.status} - {error_body}")
                return await status_msg.edit_text("⚠️ Սխալ՝ AI վերլուծության ժամանակ։")
            
            data = await res.json()
            candidates = data.get("candidates") or []
            if not candidates:
                return await status_msg.edit_text("⚠️ AI-ն չկարողացավ վերլուծել ձայնը։")
            
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not text:
                return await status_msg.edit_text("⚠️ Պատասխան չստացվեց։")

            # Try to extract score (look for numbers like 85/100 or just 85)
            # regex looks for patterns like 85/100 or 85 in the first 200 chars
            score_match = re.search(r"(\d{1,3})\s*/\s*100", text) or re.search(r"(\d{1,3})", text[:200])
            score = 0
            if score_match:
                try:
                    score = int(score_match.group(1))
                    if score > 100: score = 100
                except ValueError:
                    score = 0

            kb = get_pronunciation_feedback_keyboard(target_word, score)
            try:
                await status_msg.edit_text(
                    f"🎙️ **Արտասանության վերլուծություն՝ {target_word}**\n\n{text}", 
                    parse_mode="Markdown",
                    reply_markup=kb
                )
            except Exception as e:
                logging.warning(f"Markdown parsing failed, falling back to plain text: {e}")
                # Fallback to plain text without Markdown
                await status_msg.edit_text(
                    f"🎙️ Արտասանության վերլուծություն՝ {target_word}\n\n{text}", 
                    reply_markup=kb
                )

    except Exception:
        logging.exception("Pronunciation verification failed")
        await status_msg.edit_text("⚠️ Տեխնիկական սխալ՝ արտասանությունը ստուգելիս։")
