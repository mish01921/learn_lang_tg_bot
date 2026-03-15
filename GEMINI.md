# Google Gemini AI Integration Guide

This document explains how the English Learning Bot utilizes Google Gemini AI (Multimodal) for advanced language coaching.

## 🎙️ Pronunciation Verification (ELSA Style)
The bot uses **Gemini 1.5 Flash** (or higher) to analyze user-recorded voice messages.

- **Process:**
  1. User records a voice message in Telegram (`.oga` format).
  2. The bot downloads the file and converts it to base64.
  3. The payload is sent to Gemini via `generateContent` API with `audio/ogg` mime type.
  4. The AI evaluates the pronunciation against the target word using General American standards.

- **Feedback Metrics:**
  - **Accuracy Score (0-100):** Extracted via Regex from the AI's response.
  - **Phoneme Analysis:** Detailed breakdown of mispronounced sounds.
  - **Articulation Guide:** Physical instructions for tongue position, mouth shape, and airflow.

- **Conditional Logic:** 
  - If the user achieves a score of **95+**, the "Next Word" button is displayed to encourage progress.
  - Otherwise, only the "Try Again" button is shown.

## 🗣️ Interactive Practice
- **Contextual Correction:** Gemini analyzes sentences written by the user using a specific word.
- **Natural Language:** Provides a more natural, "native-like" version of the student's sentence.
- **Armenian Support:** All feedback is provided in Armenian to ensure clear understanding.

## 🗺️ Learning Path Optimization
- **AI Coach:** Analyzes the user's historical performance (SRS data) to provide personalized motivational messages and study tips.

## 🛠️ Model Configuration
- **Model:** `gemini-3-flash-preview` (discovered as the most stable for the current API key).
- **API Version:** `v1beta`.
- **Safety Settings:** Configured to allow educational analysis while maintaining standard safety boundaries.
