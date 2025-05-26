import sounddevice as sd
import numpy as np
import wave
import queue
import threading # To run recording in a separate thread

# Global queue to hold audio data from callback
audio_q = queue.Queue()
# Global recording stream object
recording_stream = None
# Global flag to indicate recording state
is_recording_active = False
# Thread for the recording loop
recording_thread = None

def list_input_devices():
    devices = sd.query_devices()
    input_devices = []
    for i, device in enumerate(devices):
        # Check for input channels; device name might be empty
        if device.get('max_input_channels', 0) > 0:
            device_name = device.get('name', f"Device {i}")
            input_devices.append({"id": i, "name": device_name, "channels": device.get('max_input_channels'), "samplerate": device.get('default_samplerate')})
    return input_devices

def audio_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, flush=True) # Print any errors/warnings
    audio_q.put(indata.copy()) # Add incoming audio data (NumPy array) to the queue

def start_recording(device_id=None, samplerate=44100, channels=1, output_filename="temp_audio.wav"):
    global recording_stream, is_recording_active, audio_q, recording_thread

    if is_recording_active:
        print("Recording is already active.")
        return False

    audio_q = queue.Queue() # Clear queue on new recording start

    try:
        # Determine device_id: use default if None, else try to use provided
        selected_device_id = device_id
        if selected_device_id is None:
            try:
                selected_device_id = sd.default.device[0] # Default input device
                # Check if default input device is valid
                if sd.query_devices(selected_device_id)['max_input_channels'] == 0:
                   raise IndexError("Default input device has no input channels.")
            except IndexError: # If default device is not suitable (e.g. no input channels)
                print("Default input device not suitable or not found. Trying first available input device.")
                available_devices = list_input_devices()
                if not available_devices:
                    print("No input devices found.")
                    return False
                selected_device_id = available_devices[0]['id']
                print(f"Using first available input device: {sd.query_devices(selected_device_id)['name']}")


        device_info = sd.query_devices(selected_device_id)
        actual_samplerate = samplerate if samplerate else device_info['default_samplerate']
        
        recording_stream = sd.InputStream(
            samplerate=actual_samplerate,
            device=selected_device_id,
            channels=channels,
            callback=audio_callback,
            dtype='float32' # Or 'int16' - float32 is often easier to work with before saving
        )
        recording_stream.start()
        is_recording_active = True
        
        # Start the thread that will write data from queue to file
        recording_thread = threading.Thread(target=record_to_file_thread, args=(output_filename, channels, actual_samplerate))
        recording_thread.start()
        
        print(f"Recording started on device {selected_device_id} ({device_info['name']})...")
        return True
    except Exception as e:
        print(f"Error starting recording: {e}")
        if recording_stream:
            recording_stream.close()
        recording_stream = None
        is_recording_active = False
        return False

def record_to_file_thread(output_filename, channels, samplerate):
    global is_recording_active, audio_q
    
    # Using 'int16' for WAV file as it's widely compatible
    # Max value for int16
    max_int16 = np.iinfo(np.int16).max

    try:
        with wave.open(output_filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 2 bytes for 'int16'
            wf.setframerate(int(samplerate)) # Ensure samplerate is int for wave module

            while is_recording_active:
                try:
                    data = audio_q.get(timeout=0.1) # Timeout to allow checking is_recording_active
                    # Convert float32 data to int16
                    data_int16 = (data * max_int16).astype(np.int16)
                    wf.writeframes(data_int16.tobytes())
                except queue.Empty:
                    pass # No data, continue loop
    except Exception as e:
        print(f"Error in recording thread: {e}")
    finally:
        print(f"Recording thread finished. Audio saved to {output_filename if is_recording_active else '(not saved due to early stop/error)'}")
        # Note: is_recording_active might be false here if stop_recording was called.
        # The actual stop logic for the stream is in stop_recording.

def stop_recording():
    global recording_stream, is_recording_active, recording_thread
    if not is_recording_active:
        print("Recording is not active.")
        return

    print("Stopping recording...")
    is_recording_active = False # Signal the recording thread to stop

    if recording_stream:
        recording_stream.stop()
        recording_stream.close()
        recording_stream = None
    
    if recording_thread and recording_thread.is_alive():
        recording_thread.join(timeout=1.0) # Wait for the thread to finish writing
    
    print("Recording stopped.")

if __name__ == '__main__':
    print("Available input devices:")
    devices = list_input_devices()
    if devices:
        for dev in devices:
            print(f"  ID: {dev['id']}, Name: {dev['name']}, Channels: {dev['channels']}, Rate: {dev['samplerate']}")
    else:
        print("  No input devices found.")
        exit()

    selected_dev_id = devices[0]['id'] # Example: use the first available device
    # Check if default device is actually an input device
    try:
        default_input_device_id = sd.default.device[0]
        if sd.query_devices(default_input_device_id)['max_input_channels'] > 0:
            selected_dev_id = default_input_device_id
            print(f"\nUsing default input device ID: {selected_dev_id}")
        else:
            print(f"\nDefault input device is not suitable. Using first available: ID {selected_dev_id}")
    except IndexError:
         print(f"\nNo default input device found. Using first available: ID {selected_dev_id}")


    print(f"\nAttempting to record from device ID {selected_dev_id} for 5 seconds...")
    
    output_file = "test_audio.wav"
    if start_recording(device_id=selected_dev_id, output_filename=output_file):
        try:
            # Keep the main thread alive for recording duration
            for i in range(50): # 5 seconds with 0.1s sleep
                if not is_recording_active:
                    break
                sd.sleep(100) # sounddevice.sleep takes milliseconds
            
        except KeyboardInterrupt:
            print("Recording interrupted by user.")
        finally:
            stop_recording()
            # Check if file was created and is not empty
            import os
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"Test audio successfully saved to {output_file}")
            else:
                print(f"Test audio file {output_file} was not created or is empty.")
    else:
        print("Failed to start recording.")
