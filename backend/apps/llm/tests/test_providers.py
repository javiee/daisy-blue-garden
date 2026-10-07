import os
import tempfile
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings


class OpenAIProviderTest(TestCase):
    @override_settings(LLM_API_KEY='test-key', LLM_MODEL='gpt-4o')
    @patch('openai.OpenAI')
    def test_generate(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='response text'))]
        )
        from apps.llm.providers import OpenAIProvider
        provider = OpenAIProvider()
        result = provider.generate('test prompt', system='system')
        self.assertEqual(result, 'response text')


class AnthropicProviderTest(TestCase):
    @override_settings(LLM_API_KEY='test-key', LLM_MODEL='claude-sonnet-4-6')
    @patch('anthropic.Anthropic')
    def test_generate(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text='response text')]
        )
        from apps.llm.providers import AnthropicProvider
        provider = AnthropicProvider()
        result = provider.generate('test prompt')
        self.assertEqual(result, 'response text')


class OllamaProviderTest(TestCase):
    @override_settings(OLLAMA_BASE_URL='http://localhost:11434', LLM_MODEL='llama3.2')
    @patch('apps.llm.providers.requests.post')
    def test_generate(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {'response': 'ollama response'}
        )
        mock_post.return_value.raise_for_status = MagicMock()
        from apps.llm.providers import OllamaProvider
        provider = OllamaProvider()
        result = provider.generate('test prompt')
        self.assertEqual(result, 'ollama response')


class OpenAIProviderVisionTest(TestCase):
    @override_settings(LLM_API_KEY='test-key', LLM_MODEL='gpt-4o')
    @patch('openai.OpenAI')
    def test_generate_with_image_sends_text_and_image_parts(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='A rose'))]
        )
        from apps.llm.providers import OpenAIProvider
        provider = OpenAIProvider()
        fd, image_path = tempfile.mkstemp(suffix='.png')
        with os.fdopen(fd, 'wb') as f:
            f.write(b'\x89PNG-fake-bytes')
        try:
            result = provider.generate('What plant is this?', system='sys', image_path=image_path)
        finally:
            os.unlink(image_path)
        self.assertEqual(result, 'A rose')
        kwargs = mock_client.chat.completions.create.call_args.kwargs
        content = kwargs['messages'][-1]['content']
        self.assertEqual([part['type'] for part in content], ['text', 'image_url'])
        self.assertEqual(content[0]['text'], 'What plant is this?')
        self.assertTrue(
            content[1]['image_url']['url'].startswith('data:image/png;base64,'),
            content[1]['image_url']['url'][:50],
        )

    @override_settings(LLM_API_KEY='test-key', LLM_MODEL='gpt-4o')
    @patch('openai.OpenAI')
    def test_generate_without_image_keeps_plain_string(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='ok'))]
        )
        from apps.llm.providers import OpenAIProvider
        provider = OpenAIProvider()
        provider.generate('plain prompt', system='sys')
        kwargs = mock_client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs['messages'][-1]['content'], 'plain prompt')


class UnsupportedVisionTest(TestCase):
    @override_settings(LLM_API_KEY='test-key', LLM_MODEL='claude')
    def test_anthropic_raises_for_image(self):
        from apps.llm.providers import AnthropicProvider, VisionNotSupportedError
        provider = AnthropicProvider()
        with self.assertRaises(VisionNotSupportedError):
            provider.generate('p', image_path='/tmp/whatever.png')

    @override_settings(OLLAMA_BASE_URL='http://localhost:11434', LLM_MODEL='llama3.2')
    def test_ollama_raises_for_image(self):
        from apps.llm.providers import OllamaProvider, VisionNotSupportedError
        provider = OllamaProvider()
        with self.assertRaises(VisionNotSupportedError):
            provider.generate('p', image_path='/tmp/whatever.png')


class GetLLMProviderTest(TestCase):
    @override_settings(LLM_PROVIDER='openai')
    def test_returns_openai(self):
        from apps.llm.providers import get_llm_provider, OpenAIProvider
        self.assertIsInstance(get_llm_provider(), OpenAIProvider)

    @override_settings(LLM_PROVIDER='anthropic')
    def test_returns_anthropic(self):
        from apps.llm.providers import get_llm_provider, AnthropicProvider
        self.assertIsInstance(get_llm_provider(), AnthropicProvider)

    @override_settings(LLM_PROVIDER='ollama')
    def test_returns_ollama(self):
        from apps.llm.providers import get_llm_provider, OllamaProvider
        self.assertIsInstance(get_llm_provider(), OllamaProvider)
