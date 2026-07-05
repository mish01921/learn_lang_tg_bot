import asyncio
import base64
import logging
import os
import re
import tempfile
from io import BytesIO

import httpx
from aiogram import Bot
from aiogram.types import FSInputFile, Message
from gtts import gTTS

from src.bot.ui import get_pronunciation_feedback_keyboard
from src.core.config import GEMINI_API_KEY
from src.data.api_words import GeminiClient
from src.data.level_words import chunk_text as _chunk_text
from src.database.models import get_voice_file_id, save_voice_file_id
from src.core.app_state import record_temp_message, record_word_action
from src.core.i18n import get_lang, t


def _safe_accent(accent: str) -> str:
    a = (accent or "").strip().lower()
    return a if a in {"us", "uk"} else "us"


def _guess_audio_mime_type(file_path: str | None) -> str:
    if not file_path:
        return "audio/ogg"
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".mp3":
        return "audio/mp3"
    if ext == ".wav":
        return "audio/wav"
    if ext in {".m4a", ".mp4", ".aac"}:
        return "audio/mp4"
    return "audio/ogg"


def _escape_markdown_v2(text: str) -> str:
    if not text:
        return ""
    chars = r"\_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(chars)}])", r"\\\1", text)


async def _fetch_word_phonetic(word: str) -> str:
    if not word:
        return "—"
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(url)
            if res.status_code != 200:
                return "—"
            data = res.json()
            if not isinstance(data, list) or not data:
                return "—"
            entry = data[0]
            if entry.get("phonetic"):
                return str(entry["phonetic"])
            for p in entry.get("phonetics", []):
                ph = (p.get("text") or "").strip()
                if ph:
                    return ph
    except Exception:
        return "—"
    return "—"


async def send_word_pronunciation(bot: Bot, chat_id: int, word: str, accent: str = "us"):
    """Sends word pronunciation as a voice message, with caching and TTS fallback. Supports 'us' and 'uk' accents."""
    word = (word or "").strip().lower()
    accent = _safe_accent(accent)
    cache_key = f"{word}_{accent}"

    # 1. Check cache
    file_id = await get_voice_file_id(cache_key)
    if file_id:
        try:
            msg = await bot.send_voice(chat_id, file_id)
            record_temp_message(chat_id, msg.message_id)
            record_word_action(chat_id, {"type": "audio", "file_id": file_id})
            return msg
        except Exception:
            logging.warning(f"Cached file_id {file_id} for word '{cache_key}' is invalid or expired.")

    # 2. Use gTTS with specific accent
    # US: tld='com', UK: tld='co.uk'
    tld = "co.uk" if accent == "uk" else "com"
    tmp = tempfile.NamedTemporaryFile(prefix=f"temp_pron_{accent}_", suffix=".mp3", delete=False)
    temp_filename = tmp.name
    tmp.close()

    try:
        tts = gTTS(text=word, lang='en', tld=tld)
        await asyncio.to_thread(tts.save, temp_filename)

        voice_file = FSInputFile(temp_filename)
        msg = await bot.send_voice(chat_id, voice_file)
        record_temp_message(chat_id, msg.message_id)
        if msg.voice:
            record_word_action(chat_id, {"type": "audio", "file_id": msg.voice.file_id})
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

    target_word = (target_word or "").strip().lower()
    record_temp_message(message.chat.id, message.message_id)

    file_id: str | None = None
    if message.voice:
        file_id = message.voice.file_id
    elif message.audio:
        file_id = message.audio.file_id
    elif message.document and (message.document.mime_type or "").startswith("audio/"):
        file_id = message.document.file_id

    if not file_id:
        return await message.answer("⚠️ Ձայնային հաղորդագրություն չի գտնվել։ Ուղարկիր հենց Voice կամ Audio ֆայլ։")

    lang = get_lang(message.chat.id)
    lang_names = {"hy": "Armenian", "ru": "Russian", "en": "English"}
    target_lang = lang_names.get(lang, "Armenian")

    status_msg = await message.answer(t("pronunciation_analyzing", lang))
    record_temp_message(message.chat.id, status_msg.message_id)

    try:
        file_info = await bot.get_file(file_id)
        audio_mime_type = _guess_audio_mime_type(getattr(file_info, "file_path", None))

        buf = BytesIO()
        dl = await bot.download_file(file_info.file_path, destination=buf)

        # aiogram may return destination, bytes, or a file-like object depending on version.
        audio_data = b""
        if hasattr(dl, "read"):
            audio_data = dl.read()
        elif isinstance(dl, (bytes, bytearray)):
            audio_data = bytes(dl)
        else:
            audio_data = buf.getvalue()

        if not audio_data:
            return await status_msg.edit_text("⚠️ Failed to download voice message.")

        audio_b64 = base64.b64encode(audio_data).decode("utf-8")
        phonetic = await _fetch_word_phonetic(target_word)

        prompt = (
            f"Target word: '{target_word}'\n"
            f"Standard IPA transcription: [{phonetic}]\n\n"
            f"Analyze the audio and provide structured ELSA Speak style pronunciation feedback in {target_lang}.\n"
            "Respond ONLY with clean Markdown (no conversational intros):\n"
            f"1. **🎯 Score:** Give an overall score X/100 (e.g. 85/100).\n"
            f"2. **🗣️ What I heard:** Write how the user actually pronounced it in IPA or phonetic approximation.\n"
            f"3. **✅ Correct pronunciation:** Show the standard IPA and explain syllable stress.\n"
            f"4. **💡 How to improve:** Detail specific errors and give concrete advice on tongue/lip placement in {target_lang}.\n\n"
            "Keep the feedback warm, encouraging, pedagogical, and structured!"
        )

        text = await GeminiClient.generate(
            prompt=prompt,
            temp=0.2,
            maxt=2048,
            audio_b64=audio_b64,
            audio_mime_type=audio_mime_type,
            timeout=25.0
        )

        if not text:
            return await status_msg.edit_text("⚠️ No response from AI audio analysis.")

        # Try to extract score
        score_match = re.search(r"(\d{1,3})\s*/\s*100", text) or re.search(r"(\d{1,3})", text[:200])
        score = int(score_match.group(1)) if score_match else 0
        if score > 100: score = 100

        kb = get_pronunciation_feedback_keyboard(target_word, score)
        header_text = t("pronunciation_header", lang, word=target_word)
        try:
            header = _escape_markdown_v2(header_text)
            body = _escape_markdown_v2(text)
            full_text = f"*{header}*\n\n{body}"
            chunks = list(_chunk_text(full_text))
            if not chunks:
                return

            await status_msg.edit_text(
                chunks[0],
                parse_mode="MarkdownV2",
                reply_markup=kb if len(chunks) == 1 else None,
            )
            record_word_action(message.chat.id, {"type": "text", "text": chunks[0], "parse_mode": "MarkdownV2"})
            for i in range(1, len(chunks)):
                sent = await message.answer(
                    chunks[i],
                    parse_mode="MarkdownV2",
                    reply_markup=kb if i == len(chunks) - 1 else None,
                )
                record_temp_message(message.chat.id, sent.message_id)
                record_word_action(message.chat.id, {"type": "text", "text": chunks[i], "parse_mode": "MarkdownV2"})
        except Exception:
            # Fallback without markdown v2 if parsing fails
            await status_msg.edit_text(
                f"{header_text}\n\n{text}",
                reply_markup=kb,
            )
            record_word_action(message.chat.id, {"type": "text", "text": f"{header_text}\n\n{text}"})
    except Exception as e:
        logging.exception(f"Pronunciation verification failed for word '{target_word}': {e}")
        await status_msg.edit_text("⚠️ Տեղի ունեցավ սխալ ձայնը մշակելիս։ Փորձիր կրկին։")
