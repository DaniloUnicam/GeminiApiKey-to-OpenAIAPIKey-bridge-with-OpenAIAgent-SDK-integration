# GeminiApiKey <--> OpenAIAPIKey Bridge with OpenAI Agent SDK Integration

A Python bridge that enables using **Google Gemini API** with the **OpenAI Agent SDK** through OpenAI-compatible endpoints.

This project leverages the OpenAI-compatible API endpoint provided by Google:
```
https://generativelanguage.googleapis.com/v1beta/openai/
```

This allows you to use the full power of OpenAI's Agent SDK with Gemini models instead of OpenAI models.

---

## Prerequisites

- **Python 3.10+** (tested on 3.14)
- **pip** (Python package manager)
- **Google Gemini API Key** (get one at [Google AI Studio](https://aistudio.google.com/app/apikey))
- Optional: **OpenAI API Key** (for testing with OpenAI models)

---

## Installation

### 1. Clone or Download the Repository

```bash
cd your-project-directory
```

### 2. Create and Activate a Virtual Environment (Recommended)

**On Windows (PowerShell):**
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```bash
python -m venv .venv
.venv\Scripts\activate.bat
```

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install openai python-dotenv
```

Or install all at once:
```bash
pip install -r requirements.txt
```

**If requirements.txt doesn't exist, create it with:**
```
openai>=2.26.0
python-dotenv>=1.0.0
pydantic>=2.0.0
aiohttp>=3.8.0
```

### 4. Install OpenAI Agent SDK (If Available in Your Environment)

```bash
pip install openai-agents
```

Or if using the local OpenAI_Agent_Repo:
```bash
pip install -e ./OpenAI_Agent_Repo
```

---

## Setup

### 1. Create a `.env` File

Create a file named `.env` in the root directory (same folder as `AgentMain.py`):

```env
GEMINI_API_KEY_env=your-actual-gemini-api-key-here
```

**How to get your Gemini API Key:**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Select or create a Google Cloud project
4. Copy the API key and paste it in the `.env` file

### 2. (Optional) Add OpenAI API Key for Testing

If you want to test with OpenAI models, add to your `.env` file:

```env
OPENAI_API_KEY=your-openai-api-key-here
```

---

## Usage

### Main Script - AgentMain.py

This is the primary script that demonstrates how to use Gemini with the OpenAI Agent SDK:

```bash
python AgentMain.py
```

**Configuration Options in AgentMain.py:**
- `agent_name`: Name of your agent (default: "Assistant")
- `agent_instructions`: System instructions for the agent
- `agent_model`: Gemini model to use (e.g., "gemini-2.5-flash")
- `prompt_for_chatting_with_agent`: The question/prompt to send to the agent

### List Available Models

View all compatible Gemini models:

```bash
python list_models.py
```

This will display a comprehensive list of available models including:
- Chat models (e.g., `gemini-2.5-flash`, `gemini-2.5-pro`)
- Vision models (e.g., `gemini-2.5-flash-image`)
- Embedding models
- Multimodal models

### Test OpenAI (Optional)

If you have an OpenAI API key set up, test with OpenAI models:

```bash
python test_openai.py
```

⚠️ **Note:** This requires `OPENAI_API_KEY` in your `.env` file

---

## Compatible Models

⚠️ **USE `list_models.py` to view the complete list of compatible models** ⚠️

Popular working models: (to switch model, copy for example "gemini-2.5-flash" and switch the variable **agent_model** in **AgentMain.py** configuration)

List of compatible models:
  - models/gemini-2.5-flash
  - models/gemini-2.5-pro
  - models/gemini-2.0-flash
  - models/gemini-2.0-flash-001
  - models/gemini-2.0-flash-lite-001
  - models/gemini-2.0-flash-lite
  - models/gemini-2.5-flash-preview-tts
  - models/gemini-2.5-pro-preview-tts
  - models/gemma-4-26b-a4b-it
  - models/gemma-4-31b-it
  - models/gemini-flash-latest
  - models/gemini-flash-lite-latest
  - models/gemini-pro-latest
  - models/gemini-2.5-flash-lite
  - models/gemini-2.5-flash-image
  - models/gemini-3-pro-preview
  - models/gemini-3-flash-preview
  - models/gemini-3.1-pro-preview
  - models/gemini-3.1-pro-preview-customtools
  - models/gemini-3.1-flash-lite-preview
  - models/gemini-3-pro-image-preview
  - models/nano-banana-pro-preview
  - models/gemini-3.1-flash-image-preview
  - models/lyria-3-clip-preview
  - models/lyria-3-pro-preview
  - models/gemini-3.1-flash-tts-preview
  - models/gemini-robotics-er-1.5-preview
  - models/gemini-robotics-er-1.6-preview
  - models/gemini-2.5-computer-use-preview-10-2025
  - models/deep-research-max-preview-04-2026
  - models/deep-research-preview-04-2026
  - models/deep-research-pro-preview-12-2025
  - models/gemini-embedding-001
  - models/gemini-embedding-2-preview
  - models/gemini-embedding-2
  - models/aqa
  - models/imagen-4.0-generate-001
  - models/imagen-4.0-ultra-generate-001
  - models/imagen-4.0-fast-generate-001
  - models/veo-2.0-generate-001
  - models/veo-3.0-generate-001
  - models/veo-3.0-fast-generate-001
  - models/veo-3.1-generate-preview
  - models/veo-3.1-fast-generate-preview
  - models/veo-3.1-lite-generate-preview
  - models/gemini-2.5-flash-native-audio-latest
  - models/gemini-2.5-flash-native-audio-preview-09-2025
  - models/gemini-2.5-flash-native-audio-preview-12-2025
  - models/gemini-3.1-flash-live-preview

---

## Project Structure

```
GeminiApiKey-to-OpenAIAPIKey-bridge-with-OpenAIAgent-SDK-integration/
├── .venv/                          # Virtual environment (created after setup)
├── .env                            # Environment variables (CREATE THIS)
├── AgentMain.py                    # Main script - run this to use Gemini with OpenAI Agent SDK
├── list_models.py                  # List all available Gemini models
├── test_openai.py                  # Optional: Test with OpenAI models
├── OpenAI_Agent_Repo/              # OpenAI Agent SDK repository (optional)
│   ├── src/
│   ├── examples/
│   ├── tests/
│   ├── pyproject.toml
│   └── ...
├── README.md                       # This file
└── requirements.txt                # Python dependencies (optional)
```

---

## Environment Variables

The `.env` file supports the following variables:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY_env` | ✅ Yes | Your Google Gemini API key | `AIzaSy...` |
| `OPENAI_API_KEY` | ❌ No | Your OpenAI API key (for testing) | `sk-...` |

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'agents'`

**Solution:**
1. Ensure the virtual environment is activated
2. Install the package: `pip install openai-agents`
3. Or install from local repo: `pip install -e ./OpenAI_Agent_Repo`

### Issue: `ValueError: GEMINI_API_KEY_env not set`

**Solution:**
1. Create a `.env` file in the root directory
2. Add your Gemini API key: `GEMINI_API_KEY_env=your-key-here`
3. Save the file and restart the script

### Issue: `401 Unauthorized` or API key errors

**Solution:**
1. Verify your API key is correct in the `.env` file
2. Check that the API key has no extra spaces or quotes
3. Ensure your Google Cloud project has the Generative Language API enabled
4. Get a fresh API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Issue: `ImportError` related to OpenAI or dependencies

**Solution:**
```bash
# Upgrade pip
pip install --upgrade pip

# Reinstall dependencies
pip install --upgrade openai python-dotenv pydantic
```

### Issue: Models not found or API endpoint errors

**Solution:**
1. Verify the model name is correct (use `list_models.py` to check)
2. Ensure you're using the correct model prefix: `models/gemini-2.5-flash` not just `gemini-2.5-flash`
3. Try a different model like `gemini-2.5-flash`

---

## Quick Start Guide

```bash
# 1. Activate virtual environment
.venv\Scripts\Activate.ps1          # Windows PowerShell
# or
source .venv/bin/activate           # macOS/Linux

# 2. Install dependencies
pip install openai python-dotenv

# 3. Create .env file with your Gemini API key
# (Create manually or using your editor)

# 4. Run the main script
python AgentMain.py

# 5. View available models (optional)
python list_models.py
```

---

## Advanced Usage

### Modifying the Agent

Edit `AgentMain.py` to customize:

```python
# Change the agent name
agent_name = "My Custom Agent"

# Modify the system instructions
agent_instructions = "You are an expert Python developer..."

# Switch to a different model
agent_model = "gemini-2.5-pro"

# Ask a different question
domanda_da_porre = "Help me solve this problem..."
```

### Using with OpenAI Agent SDK Features

The bridge maintains full compatibility with OpenAI Agent SDK features including:
- Tool use and function calling
- Multi-step reasoning
- Context management
- Streaming responses

Refer to the [OpenAI Agent SDK documentation](https://github.com/openai/openai-agents-python) for advanced usage patterns.

---

## Requirements

- **Python:** 3.10 or higher
- **Dependencies:**
  - `openai>=2.26.0` - OpenAI Python client
  - `python-dotenv>=1.0.0` - Environment variable management
  - `pydantic>=2.0.0` - Data validation
  - `aiohttp>=3.8.0` - Async HTTP client
  - `openai-agents` - OpenAI Agent SDK (optional but recommended)

Install all at once:
```bash
pip install openai python-dotenv pydantic aiohttp openai-agents
```

---

## How It Works

1. **API Bridge:** Uses Google's OpenAI-compatible endpoint at `https://generativelanguage.googleapis.com/v1beta/openai/`
2. **Authentication:** Passes your Gemini API key to authenticate with Google's services
3. **SDK Compatibility:** The OpenAI Agent SDK communicates with Google's endpoint transparently
4. **Model Support:** All Gemini models are accessible through the standard OpenAI API interface

---

## Support & Resources

- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI Agent SDK Repository](https://github.com/openai/openai-agents-python)
- [Google AI Studio](https://aistudio.google.com/)

---

## License

Please check the LICENSE file in the OpenAI_Agent_Repo directory for licensing information.
