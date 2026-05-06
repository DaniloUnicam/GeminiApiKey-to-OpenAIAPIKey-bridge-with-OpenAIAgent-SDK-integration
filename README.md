# GeminiApiKey <--> OpenAIAPIKey bridge with OpenAI Agent SDK integration
A Python script used as a bridge for your Gemini API Key in compatibility with OpenAI API, using the following url:
"https://generativelanguage.googleapis.com/v1beta/openai/"

This enables the use of OpenAI's Agent SDK, but using Gemini instead of OpenAI.

1) Insert your GeminiAPI Key inside a .env file inside this folder.


<img width="421" height="58" alt="image" src="https://github.com/user-attachments/assets/e74c6f1e-9609-448f-977d-9fbb8e77dd12" />



2) The main configuration comes from AgentMain.py:



<img width="517" height="270" alt="image" src="https://github.com/user-attachments/assets/25cb98ed-0a24-459e-a179-a343e066b9d7" />




ONLY IF USING OpenAI-API key: test_openai.py does the job.

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
