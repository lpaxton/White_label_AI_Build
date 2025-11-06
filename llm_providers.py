"""
LLM Provider Module
Supports OpenAI, Anthropic Claude, and Ollama for content selection.
"""
from abc import ABC, abstractmethod
from typing import Optional
import os


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """Generate a response from the LLM."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided).
            model: Model to use (default: gpt-3.5-turbo).
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that selects relevant content based on user personas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        """
        Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided).
            model: Model to use (default: claude-3-sonnet-20240229).
        """
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided")
        
        self.model = model
        self.client = Anthropic(api_key=self.api_key)
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using Anthropic Claude."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self, model: str = "llama2", host: str = "http://localhost:11434"):
        """
        Initialize Ollama provider.
        
        Args:
            model: Model to use (default: llama2).
            host: Ollama server host (default: http://localhost:11434).
        """
        try:
            import ollama
        except ImportError:
            raise ImportError("Ollama package not installed. Run: pip install ollama")
        
        self.model = model
        self.host = host
        self.client = ollama.Client(host=host)
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using Ollama."""
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that selects relevant content based on user personas."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            return response['message']['content']
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")


def get_llm_provider(provider_type: str, **kwargs) -> LLMProvider:
    """
    Factory function to get the appropriate LLM provider.
    
    Args:
        provider_type: Type of provider ('openai', 'anthropic', or 'ollama').
        **kwargs: Additional arguments for the provider.
        
    Returns:
        Initialized LLM provider.
    """
    providers = {
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'ollama': OllamaProvider,
    }
    
    provider_type = provider_type.lower()
    if provider_type not in providers:
        raise ValueError(f"Unknown provider type: {provider_type}. Choose from: {', '.join(providers.keys())}")
    
    return providers[provider_type](**kwargs)
