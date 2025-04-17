# Edge TTS API

A Python API that leverages Microsoft's Edge Text-to-Speech service with additional features like Hindi translation support.

## Features

- Text-to-Speech conversion using Microsoft Edge TTS
- Multiple voice options from Microsoft's neural voice collection
- Hindi translation support using Google Translate
- Customizable speech rate and volume
- JSON-based batch processing
- RESTful API with FastAPI
- Audio file playback support for Windows, macOS, and Linux

## Requirements

- Python 3.7+
- Required packages (see `requirements.txt`):
  ```
  edge-tts>=6.1.7
  asyncio>=3.4.3
  fastapi>=0.100.0
  uvicorn>=0.23.0
  googletrans==4.0.0-rc1
  pydantic>=2.0.0
  python-multipart
  ```

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/edge-tts-api.git
   cd edge-tts-api
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Command Line Text-to-Speech

You can use the script directly from the command line by passing a JSON file:

```
python main.py your_input_file.json
```

If no file is provided, the script will create and process an example file automatically.

### JSON Format

The input JSON file should follow this structure:

```json
{
  "requests": [
    {
      "text": "Hello! This is a test.",
      "voice": "en-US-GuyNeural",
      "rate": "+0%",
      "volume": "+0%",
      "translate_to_hindi": false,
      "output_file": "english_output.mp3"
    },
    {
      "text": "This text will be translated to Hindi.",
      "voice": "hi-IN-MadhurNeural",
      "translate_to_hindi": true,
      "output_file": "hindi_output.mp3"
    }
  ]
}
```

### API Usage

Start the API server:

```
python tts_api.py
```

Or use uvicorn directly:

```
uvicorn tts_api:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

#### API Endpoints

- `GET /`: Root endpoint with API information
- `POST /tts`: Process a JSON file with TTS requests and return the generated speech file(s)
  - Parameters:
    - `file`: The JSON file (required)
    - `return_first_only`: Boolean to return only the first generated file (optional, default: false)
- `GET /get-file/{filename}`: Get a generated speech file by filename
- `GET /test`: Test endpoint to verify TTS functionality
- `GET /healthcheck`: Health check endpoint

#### Example API Request

```bash
curl -X POST http://localhost:8000/tts \
  -F "file=@json_example.json" \
  -F "return_first_only=false"
```

### Python Module Usage

You can also use the EdgeTTS class directly in your Python code:

```python
from main import EdgeTTS, speak_text

# Simple one-line usage
speak_text("Hello, world!", voice="en-US-GuyNeural")

# More customized usage
tts = EdgeTTS()
tts.set_voice("en-US-GuyNeural")
tts.set_rate("+10%")  # Faster speech
tts.speak("This is a test with custom settings.", "output.mp3")

# With translation
tts.speak("This will be translated to Hindi.", "hindi_output.mp3", translate_to_hindi=True)
```

## Available Voices

The Edge TTS service provides numerous voices. You can programmatically list all available voices:

```python
import asyncio
from main import list_voices

# Get all available voices
voices = asyncio.run(list_voices())
```

Common voice options include:
- `en-US-GuyNeural`: Male American English
- `en-US-JennyNeural`: Female American English
- `hi-IN-MadhurNeural`: Male Hindi
- `hi-IN-SwaraNeural`: Female Hindi

## Output Directory

By default, output files are saved to a `tts_output` directory in the same location as the script. This directory is created automatically if it doesn't exist.

## Acknowledgments

- This project uses [Microsoft Edge TTS](https://github.com/rany2/edge-tts) for speech synthesis
- Translation functionality is provided by [Google Translate](https://pypi.org/project/googletrans/)
