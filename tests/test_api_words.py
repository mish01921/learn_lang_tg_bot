import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import src.data.api_words as api_words


class TestApiWordsHelpers(unittest.TestCase):
    def test_extract_headword(self):
        self.assertEqual(api_words.extract_headword("bank (money) n."), "bank")
        self.assertEqual(api_words.extract_headword(" about prep."), "about")
        self.assertEqual(api_words.extract_headword("Go1 v."), "go")
        self.assertEqual(api_words.extract_headword(""), "")
        self.assertEqual(api_words.extract_headword("# comment"), "")

    def test_normalize_word(self):
        self.assertEqual(api_words._normalize_word(" Test "), "test")
        self.assertEqual(api_words._normalize_word("WORD"), "word")
        self.assertEqual(api_words._normalize_word(None), "")

    def test_parse_examples_text(self):
        text = """1. Example one.
        2) Example two.
        - Example three.
        """
        examples = api_words._parse_examples_text(text)
        self.assertEqual(len(examples), 3)
        self.assertEqual(examples[0], "Example one.")
        self.assertEqual(examples[1], "Example two.")
        self.assertEqual(examples[2], "Example three.")

    def test_fallback_examples(self):
        examples = api_words._fallback_examples("test")
        self.assertTrue(len(examples) >= 1)
        self.assertIn("test", examples[0])


class TestApiWordsCaching(unittest.TestCase):
    def setUp(self):
        # Clear cache before tests
        api_words._word_data_cache.clear()
        api_words._example_cache.clear()

    def test_word_data_caching(self):
        word = "test"
        data = {"word": "test", "translation": "փորձ"}

        # Should be None initially
        self.assertIsNone(api_words._get_cached_word_data(word))

        # Set cache
        api_words._set_cached_word_data(word, data)

        # Retrieve cache
        cached = api_words._get_cached_word_data(word)
        self.assertEqual(cached, data)

        # Test normalization in cache
        cached_upper = api_words._get_cached_word_data("TEST")
        self.assertEqual(cached_upper, data)

    def test_cache_ttl_expiry(self):
        # Manually insert an old record
        old_time = datetime.now() - timedelta(hours=api_words.WORD_CACHE_TTL_HOURS + 1)
        api_words._word_data_cache["old"] = (old_time, {"val": 1})

        self.assertIsNone(api_words._get_cached_word_data("old"))


class TestApiWordsAsync(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        api_words._http_session = None
        api_words._network_blocked_until = None
        # Set dummy keys for testing
        api_words.GEMINI_API_KEY = "dummy_gemini_key"
        api_words.GOOGLE_TRANSLATE_API_KEY = "dummy_gt_key"
        # Clear caches
        api_words._word_data_cache.clear()
        api_words._example_cache.clear()

    async def asyncTearDown(self):
        await api_words.HTTPClient.close()

    @patch("src.data.api_words.HTTPClient.get", new_callable=AsyncMock)
    async def test_get_translation_gemini_success(self, mock_get_client):
        from unittest.mock import AsyncMock, MagicMock
        mock_session = AsyncMock()
        mock_get_client.return_value = mock_session

        # Mock response for Gemini
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "թարգմանություն"}]
                }
            }]
        }
        mock_session.post.return_value = mock_response

        translation = await api_words.get_translation_gemini("word")
        self.assertEqual(translation, "թարգմանություն")

    @patch("src.data.api_words.HTTPClient.get", new_callable=AsyncMock)
    async def test_get_word_data_integration_success(self, mock_get_client):
        mock_session = AsyncMock()
        mock_get_client.return_value = mock_session

        with patch("src.data.api_words._fetch_dictionary_fields", new_callable=AsyncMock) as mock_dict, \
             patch("src.data.api_words.get_translation", new_callable=AsyncMock) as mock_trans:

            mock_dict.return_value = ("trans_dict", "def_dict", "ex_dict", "audio_dict")
            mock_trans.return_value = "թարգմանություն"

            data = await api_words.get_word_data("test")

            self.assertEqual(data["word"], "test")
            self.assertEqual(data["translation"], "թարգմանություն")
            self.assertEqual(data["definition"], "def_dict")
            self.assertEqual(data["transcription"], "trans_dict")
            self.assertEqual(data["audio_url"], "audio_dict")

    @patch("src.data.api_words.HTTPClient.get", new_callable=AsyncMock)
    async def test_get_word_data_fallback(self, mock_get_client):
        mock_session = AsyncMock()
        mock_get_client.return_value = mock_session

        with patch("src.data.api_words._fetch_dictionary_fields", new_callable=AsyncMock) as mock_dict, \
             patch("src.data.api_words.get_translation", new_callable=AsyncMock) as mock_trans:

            mock_dict.return_value = ("trans_def", "dict_def", "dict_ex", "audio_def")
            mock_trans.return_value = "fallback_trans"

            data = await api_words.get_word_data("test")

            self.assertEqual(data["definition"], "dict_def")
            self.assertEqual(data["translation"], "fallback_trans")
            self.assertEqual(data["transcription"], "trans_def")
