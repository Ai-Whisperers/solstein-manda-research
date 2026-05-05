#!/usr/bin/env python3
"""
CrewAI Configuration — sets up model providers for research agents.
Uses available API keys: OpenAI, OpenRouter, GitHub.

Usage:
    from crewai_config import get_llm, get_github_token
    llm = get_llm('openai')       # OpenAI GPT-4o-mini
    llm = get_llm('openrouter')   # Claude Haiku via OpenRouter
    llm = get_llm('cheap')        # Cheapest option (OpenRouter Haiku)
    
    token = get_github_token()    # GitHub PAT for API access
"""

import os

def get_github_token():
    """Get GitHub token from environment or gh CLI."""
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if token:
        return token
    try:
        import subprocess
        result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_openai_key():
    """Get OpenAI API key."""
    return os.environ.get('OPENAI_API_KEY')


def get_openrouter_key():
    """Get OpenRouter API key."""
    return os.environ.get('OPENROUTER_API_KEY')


def get_llm(provider='openai', temperature=0.1):
    """
    Get a CrewAI-compatible LLM configuration.
    
    Providers:
      'openai'     — GPT-4o-mini (cheap, fast, good for structured tasks)
      'openai_best' — GPT-4o (best quality, more expensive)
      'openrouter' — Claude Haiku via OpenRouter (if OpenAI quota hit)
      'cheap'      — Auto: prefer OpenRouter Haiku, fallback GPT-4o-mini
    
    Returns a dict suitable for CrewAI Agent(llm_config=...) or Agent(llm=...)
    """
    from crewai import LLM

    LITELLM_BASE = 'http://72.61.44.159:4000/v1'
    LITELLM_KEY = 'sk-hermes-litellm-sunstein-2026'

    def _litellm(model):
        return LLM(
            model=model,
            api_key=LITELLM_KEY,
            base_url=LITELLM_BASE,
            temperature=temperature,
        )

    if provider == 'cheap':
        return _litellm('deepseek-chat')

    if provider == 'openai':
        return _litellm('groq-deepseek')

    if provider == 'openai_best':
        return _litellm('claude-sonnet-4')

    if provider == 'openrouter':
        return _litellm('gemini-flash')

    # Fallback — cheapest working option
    return _litellm('deepseek-chat')


# Provider configurations for CrewAI
LLM_CONFIGS = {
    'ownership_analyst': {
        'provider': 'openai',
        'model': 'gpt-4o-mini',
        'temperature': 0.1,
    },
    'financial_analyst': {
        'provider': 'openai',
        'model': 'gpt-4o-mini', 
        'temperature': 0.1,
    },
    'tech_analyst': {
        'provider': 'openai',
        'model': 'gpt-4o-mini',
        'temperature': 0.1,
    },
    'market_analyst': {
        'provider': 'openai',
        'model': 'gpt-4o-mini',
        'temperature': 0.1,
    },
    'validator': {
        'provider': 'openai_best',
        'model': 'gpt-4o',
        'temperature': 0.0,  # Zero temperature for validation — deterministic
    },
}


if __name__ == '__main__':
    print("=== CrewAI Configuration Check ===")
    print(f"OpenAI key:    {'✓ Found' if get_openai_key() else '✗ Missing'}")
    print(f"OpenRouter key: {'✓ Found' if get_openrouter_key() else '✗ Missing'}")
    print(f"GitHub token:  {'✓ Found' if get_github_token() else '✗ Missing'}")
    
    if get_openai_key():
        print(f"OpenAI key prefix: {get_openai_key()[:15]}...")
    print(f"\nLLM configs available for all 5 specialist agents + validator")
