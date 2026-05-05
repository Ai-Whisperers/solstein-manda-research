# CrewAI Setup Guide — Working Configuration

## Credentials (Auto-Discovered)

### LiteLLM Gateway (VPS — 72.61.44.159:4000)

| Key | Value |
|---|---|
| API URL | `http://72.61.44.159:4000/v1` |
| Master Key | `sk-hermes-litellm-sunstein-2026` |
| Working | ✅ Tested |

### Available Models via LiteLLM Proxy

| Model Name | Provider | Use For | Cost |
|---|---|---|---|
| `deepseek-chat` | DeepSeek | Default analyst agents (cheap, fast) | ~$0.5/M tokens |
| `claude-sonnet-4` | Anthropic | Validator agent (best quality) | ~$15/M tokens |
| `gemini-flash` | Google | Alternative cheap option | ~$0.15/M tokens |
| `groq-deepseek` | Groq | Fallback | Free tier |
| `groq-llama` | Groq via API | Fallback | Free tier |

### VPS API Keys (Available via environment)

| Key | Value | Provider |
|---|---|---|
| `GEMINI_API_KEY` | `AIzaSyDl531vscZ12ngzlHXDzPXkNFkI7LJgTOk` | Google Gemini |
| `GROQ_API_KEY` | `gsk_iSi3DiPB4APjjSXodWAwWGdyb3FYhvoI...` | Groq |
| `DEEPSEEK_API_KEY` | `sk-2241bdc0e803456984c8aab229382416` | DeepSeek |
| `OPENROUTER_API_KEY` | `sk-or-v1-7c0cad9f18c947af3ef9e9fa3c0a660a...` | OpenRouter |
| `TOGETHER_API_KEY` | `abd9f137c68409c6221c7620f4d6c9d0cbe4bf5f9...` | Together AI |

## Quick Test

```bash
cd /data/work/deliverables/john-pipeline/scripts

# Test the proxy connection
python3 -c "
from openai import OpenAI
client = OpenAI(
    api_key='sk-hermes-litellm-sunstein-2026',
    base_url='http://72.61.44.159:4000/v1'
)
models = client.models.list()
print('Available models:')
for m in models.data:
    print(f'  {m.id}')
"

# Test a completion
python3 -c "
from openai import OpenAI
client = OpenAI(
    api_key='sk-hermes-litellm-sunstein-2026',
    base_url='http://72.61.44.159:4000/v1'
)
resp = client.chat.completions.create(
    model='deepseek-chat',
    messages=[{'role': 'user', 'content': 'Return number 42'}],
    max_tokens=10
)
print(resp.choices[0].message.content)
"

# Test full CrewAI agent
python3 -c "
from crewai import Agent, Task, Crew, Process
from crewai_config import get_llm

llm = get_llm('cheap')
agent = Agent(role='Test', goal='Test', backstory='Test.', llm=llm)
task = Task(description='Return score 4', expected_output='4', agent=agent)
crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
print(f'CrewAI result: {result}')
"
```

## How Agents Are Configured

| Agent | Model | Rationale |
|---|---|---|
| Ownership Analyst | `deepseek-chat` | Cheap, fast, good at structured analysis |
| Financial Analyst | `deepseek-chat` | Same |
| Tech Analyst | `deepseek-chat` | Same |
| Market Analyst | `deepseek-chat` | Same |
| Validator | `claude-sonnet-4` | Best quality for critical validation |

The config module (`crewai_config.py`) auto-selects models. The research_crew.py uses these configurations.

## Also Available: GitHub Token

```
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
```

Used by `datasources.py` for GitHub API calls (raises limit from 60/hr to 5,000/hr).
