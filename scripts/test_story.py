import asyncio
import os
import sys

sys.path.append(os.getcwd())

from src.data.api_words import HTTPClient, generate_contextual_story


async def test_story_generation():
    print("Testing Story Generation with Gemini...")
    words = ["apple", "banana", "sun"]
    genre = "fantasy"
    level = "A2"

    try:
        story = await generate_contextual_story(words, genre, level)
        print("\n--- GENERATED STORY ---")
        print(story)
        print("------------------------")

        if "fallback" in story.lower() or "📖" in story:
            print("\n⚠️ WARNING: The bot returned a FALLBACK story, not an AI-generated one.")
        else:
            print("\n✅ SUCCESS: AI Story generated!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    finally:
        await HTTPClient.close()

if __name__ == "__main__":
    asyncio.run(test_story_generation())
