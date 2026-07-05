import asyncio
import sys
import os

sys.path.append(os.getcwd())

from src.data.api_words import get_tutor_explanation_gemini

async def test_tutor_explanation():
    print("Testing Tutor Explanation (Interactive Task) with Gemini...")
    sentence = "i posted my photo"
    level = "A2"
    
    try:
        explanation = await get_tutor_explanation_gemini(sentence, level=level)
        print("\n--- TUTOR EXPLANATION ---")
        print(explanation)
        print("--------------------------")
        
        if "sorry" in explanation.lower() or "trouble" in explanation.lower():
            print("\n❌ FAILED: The tutor explanation failed with fallback message.")
        else:
            print("\n✅ SUCCESS: Tutor explanation generated!")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_tutor_explanation())
