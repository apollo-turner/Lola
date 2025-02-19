import os
import json
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
import time  # For performance tracking

class DataIngestion:
    def __init__(self, base_path):
        self.base_path = base_path
        self.target_folders = ["inbox", "archived_threads", "e2ee_cutover", "filtered_threads"]  # Target folders

    def process_all_directories(self):
        all_messages = []
        base_dirs = [os.path.join(self.base_path, d) for d in os.listdir(self.base_path) if os.path.isdir(os.path.join(self.base_path, d))]

        print(f"Found {len(base_dirs)} directories to process.")

        # Dynamic Worker Allocation
        max_workers = multiprocessing.cpu_count() * 2  # Optimized for I/O-bound tasks
        print(f"Using {max_workers} workers for parallel processing.")

        # Parallel processing using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_dir = {executor.submit(self.scan_folders, directory): directory for directory in base_dirs}

            for future in as_completed(future_to_dir):
                directory = future_to_dir[future]
                try:
                    messages = future.result()
                    all_messages.extend(messages)
                except Exception as e:
                    print(f"Error processing {directory}: {e}")

        return pd.DataFrame(all_messages)

    def scan_folders(self, path):
        messages = []
        for root, dirs, files in os.walk(path):
            # Check if the folder is one of the target folders
            if any(folder in root.lower() for folder in self.target_folders) and "message_1.json" in files:
                file_path = os.path.join(root, "message_1.json")
                try:
                    inbox_messages = self.parse_json(file_path)
                    messages.extend(inbox_messages)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
        return messages

    def parse_json(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='ISO-8859-1') as f:
                data = json.load(f)

        return [
            {
                "sender": message.get("sender_name"),
                "timestamp": pd.to_datetime(message.get("timestamp_ms"), unit='ms') if message.get("timestamp_ms") else None,
                "content": self.clean_text(message.get("content", "")),
                "reactions": [reaction.get('reaction') for reaction in message.get('reactions', [])],
                "photos": [photo.get('uri') for photo in message.get('photos', [])] if 'photos' in message else [],
                "videos": [video.get('uri') for video in message.get('videos', [])] if 'videos' in message else [],
                "audio_files": [audio.get('uri') for audio in message.get('audio_files', [])] if 'audio_files' in message else [],
                "gifs": [gif.get('uri') for gif in message.get('gifs', [])] if 'gifs' in message else [],
                "unsent": message.get('is_unsent', False)
            }
            for message in data.get('messages', [])
        ]

    def clean_text(self, text):
        if isinstance(text, str):
            try:
                cleaned_text = text.encode('latin1').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                cleaned_text = text
            return cleaned_text.replace("’", "'")
        return text

# Main Execution Block
if __name__ == "__main__":
    start_time = time.time()  # Start timing

    data_ingestor = DataIngestion(base_path=r"C:\lola\data\raw\facebook")
    df = data_ingestor.process_all_directories()

    if not df.empty:
        # Filename format: YYYY_MM_DD_HHMMSS
        timestamp = datetime.now().strftime('%Y_%m_%d_%H%M%S')
        processed_folder = r"C:\lola\data\processed"
        os.makedirs(processed_folder, exist_ok=True)
        filename = os.path.join(processed_folder, f"{timestamp}_data-ingestion.csv")

        df.to_csv(filename, index=False)
        print(f"Data saved to {filename} with {len(df)} records.")
    else:
        print("No messages found.")

    print(df.head())

    end_time = time.time()  # End timing
    execution_time = end_time - start_time
    print(f"🚀 Execution Time: {execution_time:.2f} seconds")
