from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
import os
import json
import tempfile
import shutil
from typing import Optional
import asyncio

# Import from our TTS module
from main import EdgeTTS

app = FastAPI(
    title="Simple Edge TTS API",
    description="Simple API for Microsoft Edge text-to-speech service with Hindi translation support",
    version="1.0.0",
)

# Create a directory for audio files if it doesn't exist
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tts_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"Output directory created at: {OUTPUT_DIR}")

# Global TTS instance
tts_engine = EdgeTTS()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Simple Edge TTS API is running",
        "instruction": "POST a JSON file to /tts to get text-to-speech output",
    }


async def generate_speech(
    text: str,
    voice: str,
    rate: str,
    volume: str,
    output_file: str,
    translate_to_hindi: bool,
) -> bool:
    """Generate speech file asynchronously"""
    try:
        print(f"Generating speech: '{text[:30]}...'")

        # Configure TTS
        tts_engine.set_voice(voice)
        tts_engine.set_rate(rate)
        tts_engine.set_volume(volume)

        # Generate speech
        success = await tts_engine.speak_async(
            text, output_file=output_file, translate_to_hindi=translate_to_hindi
        )

        if success:
            print(f"Speech generation successful: {output_file}")
        else:
            print(f"Speech generation failed")

        return success
    except Exception as e:
        print(f"Error generating speech: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


@app.post("/tts")
async def process_tts_json(
    file: UploadFile = File(...), return_first_only: Optional[bool] = Form(False)
):
    """Process a JSON file with TTS requests and return the generated speech file(s)"""
    # Create a temporary directory for processing
    temp_dir = tempfile.mkdtemp()
    json_path = os.path.join(temp_dir, "input.json")

    try:
        # Save the uploaded file
        with open(json_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Print file content for debugging
        with open(json_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            print(f"Received JSON content: {file_content}")

        # Parse the JSON
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON format: {str(e)}"}

        # Check if the JSON has the expected structure
        if "requests" not in data or not isinstance(data["requests"], list):
            return {"error": "Invalid JSON format. Expected 'requests' array."}

        if not data["requests"]:
            return {"error": "No requests found in JSON"}

        # Keep track of generated files
        output_files = []

        # Process only the first request if return_first_only is True
        requests_to_process = (
            data["requests"][:1] if return_first_only else data["requests"]
        )

        # Process each request
        for i, req in enumerate(requests_to_process):
            text = req.get("text", "")
            if not text:
                continue

            voice = req.get("voice", "hi-IN-MadhurNeural")
            rate = req.get("rate", "+0%")
            volume = req.get("volume", "+0%")
            translate_to_hindi = req.get("translate_to_hindi", False)

            # Create output filename
            output_filename = req.get("output_file", f"output_{i+1}.mp3")
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            # Generate speech
            success = await generate_speech(
                text, voice, rate, volume, output_path, translate_to_hindi
            )

            if success:
                output_files.append(output_path)

        # Return the appropriate response
        if not output_files:
            return {"error": "No speech files could be generated"}

        if return_first_only and output_files:
            # Return the first generated file
            return FileResponse(
                output_files[0],
                media_type="audio/mpeg",
                filename=os.path.basename(output_files[0]),
            )
        elif len(output_files) == 1:
            # If only one file was generated, return it directly
            return FileResponse(
                output_files[0],
                media_type="audio/mpeg",
                filename=os.path.basename(output_files[0]),
            )
        else:
            # If multiple files were generated, return information about them
            return {
                "message": f"Generated {len(output_files)} audio files",
                "files": [os.path.basename(f) for f in output_files],
                "note": "Use /get-file/FILENAME to download each file",
            }

    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"error": f"Error processing request: {str(e)}"}
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/get-file/{filename}")
async def get_file(filename: str):
    """Get a generated speech file by filename"""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File {filename} not found")

    return FileResponse(file_path, media_type="audio/mpeg", filename=filename)


@app.get("/test")
async def test_tts():
    """Test endpoint to verify TTS functionality"""
    try:
        # Create a test output file
        test_file = os.path.join(OUTPUT_DIR, "test_output.mp3")

        # Generate speech
        success = await generate_speech(
            "This is a test of the Edge TTS API.",
            "en-US-GuyNeural",
            "+0%",
            "+0%",
            test_file,
            False,
        )

        if success and os.path.exists(test_file):
            return {
                "status": "success",
                "message": "TTS test successful",
                "file_size": os.path.getsize(test_file),
                "download_url": "/get-file/test_output.mp3",
            }
        else:
            return {"status": "error", "message": "TTS test failed"}
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"status": "error", "message": f"TTS test error: {str(e)}"}


@app.get("/healthcheck")
async def healthcheck():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
