import asyncio
import os
import sys

import aiohttp

sys.path.append(os.getcwd())
from src.core.config import GEMINI_API_KEY


async def list_models():
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not found.")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print("✅ Available models for your key:")
                    for m in data.get('models', []):
                        if 'generateContent' in m.get('supportedGenerationMethods', []):
                            print(f" - {m['name']}")
                else:
                    print(f"❌ Failed to list models: {resp.status}")
                    print(await resp.text())
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
