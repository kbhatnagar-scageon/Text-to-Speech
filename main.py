import time
import os
import asyncio
import platform
import json
from typing import Optional, Union, Dict, List, Any
from googletrans import Translator


class EdgeTTS:
    def __init__(self):
        self.voice = "hi-IN-MadhurNeural"  # Default voice
        self.rate = "+0%"  # Normal speed
        self.volume = "+0%"  # Normal volume
        self.translator = Translator()

    async def _generate_speech(self, text: str, output_file: str) -> bool:
        """Generate speech using edge-tts"""
        try:
            # Import from the installed package
            import edge_tts

            # Create communicator
            # NOTE: We're using the compatible syntax without 'options' parameter
            communicate = edge_tts.Communicate(text, self.voice)

            # Set rate and volume using the communicate setter methods, if they exist
            # This is the compatible way to handle different edge-tts versions
            if hasattr(communicate, "set_rate"):
                communicate.set_rate(self.rate)
            if hasattr(communicate, "set_volume"):
                communicate.set_volume(self.volume)

            # Generate speech
            await communicate.save(output_file)
            return True
        except Exception as e:
            print(f"Error generating speech: {str(e)}")
            return False

    def set_voice(self, voice: str) -> None:
        """Set the voice to use"""
        self.voice = voice

    def set_rate(self, rate: str) -> None:
        """Set speech rate (e.g., '+10%', '-20%')"""
        self.rate = rate

    def set_volume(self, volume: str) -> None:
        """Set volume (e.g., '+10%', '-20%')"""
        self.volume = volume

    def translate_text(self, text: str, target_language: str = "hi") -> str:
        """Translate text to the target language"""
        try:
            translation = self.translator.translate(text, dest=target_language)
            return translation.text
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text  # Return original text if translation fails

    async def speak_async(
        self,
        text: str,
        output_file: str = "output.mp3",
        translate_to_hindi: bool = False,
    ) -> bool:
        """Async version of speak method with optional translation"""
        try:
            start_time = time.time()

            # Translate if needed
            if translate_to_hindi:
                text = self.translate_text(text, "hi")
                print(f"Translated text: {text}")

            # Generate speech
            success = await self._generate_speech(text, output_file)
            if not success:
                return False

            process_time = time.time() - start_time
            print(f"Text processed in {process_time:.2f} seconds")

            # Play the audio
            print("Playing audio...")
            self.play_audio(output_file)
            return True
        except Exception as e:
            print(f"Error in Edge TTS: {str(e)}")
            return False

    def speak(
        self,
        text: str,
        output_file: str = "output.mp3",
        translate_to_hindi: bool = False,
    ) -> bool:
        """Convert text to speech and play it - wrapper for async version"""
        # Use a different approach that avoids nested event loops
        try:
            # Create a separate event loop
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    self.speak_async(text, output_file, translate_to_hindi)
                )
            finally:
                loop.close()
        except RuntimeError as e:
            if "already running" in str(e):
                # If we're already in an event loop, we need to use a different approach
                print(
                    "Note: Running in existing event loop, some features may be limited"
                )

                # Create a background thread to run the TTS
                import threading

                result = [False]  # To store the result

                def run_in_thread():
                    # Create a new event loop for this thread
                    thread_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(thread_loop)
                    try:
                        result[0] = thread_loop.run_until_complete(
                            self.speak_async(text, output_file, translate_to_hindi)
                        )
                    finally:
                        thread_loop.close()

                # Start thread
                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join()  # Wait for completion

                return result[0]
            else:
                raise

    def play_audio(self, file_path: str) -> bool:
        """Play audio file using the appropriate method for the platform"""
        try:
            # Try using native Windows playback
            if os.name == "nt":  # Windows
                from os import system

                system(f'start "" "{file_path}"')
                return True

            # Try using native macOS playback
            elif os.name == "posix" and platform.system() == "Darwin":  # macOS
                from os import system

                system(f'afplay "{file_path}"')
                return True

            # Try using aplay on Linux
            elif os.name == "posix":  # Linux
                from os import system

                system(f'aplay "{file_path}"')
                return True

            else:
                print("Unsupported platform for audio playback")
                return False

        except Exception as e:
            print(f"Error playing audio: {str(e)}")

            # Fallback method using webbrowser to open the file
            try:
                import webbrowser

                webbrowser.open(file_path)
                return True
            except:
                print("All audio playback methods failed")
                return False


async def list_voices() -> List[Dict[str, Any]]:
    """List all available voices and return them as a list"""
    try:
        # Import from the installed package
        import edge_tts

        voices = await edge_tts.list_voices()
        print("Available voices:")
        result = []

        for voice in voices:
            # The field names have changed in newer versions
            friendly_name = voice.get("FriendlyName", voice.get("Name", "Unknown"))
            gender = voice.get("Gender", "Unknown")
            print(f"- {voice['ShortName']}: {friendly_name} ({gender})")

            result.append(
                {
                    "short_name": voice["ShortName"],
                    "friendly_name": friendly_name,
                    "gender": gender,
                    "locale": voice.get("Locale", ""),
                }
            )

        return result
    except Exception as e:
        import traceback

        print(f"Error listing voices: {str(e)}")
        traceback.print_exc()
        return []


def speak_text(
    text: str,
    voice: str = "hi-IN-MadhurNeural",
    rate: str = "+0%",
    translate_to_hindi: bool = False,
    output_file: str = "output.mp3",
) -> bool:
    """Simple function to speak text with optional translation"""
    tts = EdgeTTS()
    tts.set_voice(voice)
    tts.set_rate(rate)
    return tts.speak(text, output_file, translate_to_hindi)


async def get_voices() -> List[Dict[str, Any]]:
    """Get all available voices as a list of dictionaries"""
    return await list_voices()


def process_json_input(json_file_path: str) -> bool:
    """Process text-to-speech requests from a JSON file"""
    try:
        # Read and parse the JSON file
        with open(json_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Create TTS engine
        tts = EdgeTTS()

        # Process each request in the JSON
        for i, request in enumerate(data.get("requests", [])):
            # Extract parameters with defaults
            text = request.get("text", "")
            voice = request.get("voice", "hi-IN-MadhurNeural")
            rate = request.get("rate", "+0%")
            volume = request.get("volume", "+0%")
            translate_to_hindi = request.get("translate_to_hindi", False)
            output_file = request.get("output_file", f"output_{i+1}.mp3")

            # Skip empty texts
            if not text:
                print(f"Skipping request #{i+1}: Empty text")
                continue

            print(f"Processing request #{i+1}: '{text[:30]}...' with voice {voice}")

            # Configure TTS
            tts.set_voice(voice)
            tts.set_rate(rate)
            tts.set_volume(volume)

            # Speak the text
            tts.speak(text, output_file, translate_to_hindi)

            # Give a pause between requests
            time.sleep(1)

        return True

    except Exception as e:
        print(f"Error processing JSON input: {str(e)}")
        return False


# Run the main function if this file is executed directly
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Use the JSON file provided as an argument
        json_file = sys.argv[1]
        print(f"Processing TTS requests from: {json_file}")
        process_json_input(json_file)
    else:
        print("Usage: python text_to_speech_fixed.py <json_file>")
        print("No JSON file provided. Using example:")

        # Create an example JSON file
        example_json = {
            "requests": [
                {
                    "text": "Hello! This is Microsoft's Edge Text-to-Speech system.",
                    "voice": "en-US-GuyNeural",
                    "translate_to_hindi": False,
                },
                {
                    "text": "This text will be translated to Hindi before speaking.",
                    "voice": "hi-IN-MadhurNeural",
                    "rate": "+0%",
                    "translate_to_hindi": True,
                },
            ]
        }

        # Write example to file
        example_file = "example_tts_input.json"
        with open(example_file, "w", encoding="utf-8") as f:
            json.dump(example_json, f, indent=2)

        print(f"Created example file: {example_file}")
        print("Processing example file...")
        process_json_input(example_file)
