"""
Fish Speech Voice Training Script
Trains Fish Speech model on custom voice samples (like Sonnet 29)
"""

import os
import sys
import json
import logging
import requests
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import librosa
import soundfile as sf
import numpy as np

# Add ai-lego-bricks to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-lego-bricks'))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FishSpeechTrainer:
    """
    Fish Speech voice training and cloning implementation
    """
    
    def __init__(self, 
                 fish_speech_url: str = "http://100.83.40.11:8080",
                 working_dir: str = "./fish_speech_training"):
        """
        Initialize Fish Speech trainer
        
        Args:
            fish_speech_url: URL of Fish Speech server
            working_dir: Directory for training data and outputs
        """
        self.fish_speech_url = fish_speech_url
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(exist_ok=True)
        
        # Training configuration
        self.config = {
            "sample_rate": 44100,
            "min_duration": 0.5,  # Minimum segment duration in seconds
            "max_duration": 10.0,  # Maximum segment duration in seconds
            "silence_threshold": 0.01,  # Silence detection threshold
            "voice_name": "custom_voice",
            "training_epochs": 100,
            "batch_size": 8,
            "learning_rate": 1e-4
        }
        
        logger.info(f"Initialized Fish Speech trainer with working directory: {self.working_dir}")
    
    def prepare_training_data(self, 
                            audio_file: str, 
                            text_file: str,
                            output_name: str = "sonnet29") -> Dict[str, str]:
        """
        Prepare training data from audio file and corresponding text
        
        Args:
            audio_file: Path to audio file (e.g., sonnet29.mp3)
            text_file: Path to text file with transcript
            output_name: Name for the training dataset
            
        Returns:
            Dictionary with paths to prepared training data
        """
        logger.info(f"Preparing training data from {audio_file} and {text_file}")
        
        # Create dataset directory
        dataset_dir = self.working_dir / output_name
        dataset_dir.mkdir(exist_ok=True)
        
        # Load and preprocess audio
        audio_segments = self._preprocess_audio(audio_file, dataset_dir)
        
        # Load and align text
        with open(text_file, 'r', encoding='utf-8') as f:
            text_content = f.read().strip()
        
        # Create training manifest
        manifest_path = self._create_training_manifest(
            audio_segments, text_content, dataset_dir, output_name
        )
        
        # Prepare configuration files
        config_path = self._create_training_config(dataset_dir, output_name)
        
        return {
            "dataset_dir": str(dataset_dir),
            "manifest_path": str(manifest_path),
            "config_path": str(config_path),
            "audio_segments": len(audio_segments)
        }
    
    def _preprocess_audio(self, audio_file: str, output_dir: Path) -> List[str]:
        """
        Preprocess audio file for training
        
        Args:
            audio_file: Path to input audio file
            output_dir: Directory to save processed audio segments
            
        Returns:
            List of paths to audio segments
        """
        logger.info("Preprocessing audio file...")
        
        # Load audio
        try:
            audio, sr = librosa.load(audio_file, sr=self.config["sample_rate"])
            logger.info(f"Loaded audio: {len(audio)/sr:.2f}s at {sr}Hz")
        except Exception as e:
            logger.error(f"Failed to load audio file: {e}")
            raise
        
        # Normalize audio
        audio = librosa.util.normalize(audio)
        
        # Split into segments based on silence
        segments = self._split_audio_by_silence(audio, sr)
        
        # Save segments
        audio_dir = output_dir / "audio"
        audio_dir.mkdir(exist_ok=True)
        
        segment_paths = []
        for i, segment in enumerate(segments):
            if len(segment) / sr >= self.config["min_duration"]:
                segment_path = audio_dir / f"segment_{i:03d}.wav"
                sf.write(str(segment_path), segment, sr)
                segment_paths.append(str(segment_path))
                logger.info(f"Saved segment {i}: {len(segment)/sr:.2f}s")
        
        logger.info(f"Created {len(segment_paths)} audio segments")
        return segment_paths
    
    def _split_audio_by_silence(self, audio: np.ndarray, sr: int) -> List[np.ndarray]:
        """
        Split audio into segments based on silence detection
        
        Args:
            audio: Audio data
            sr: Sample rate
            
        Returns:
            List of audio segments
        """
        # Simple energy-based silence detection
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.01 * sr)     # 10ms hop
        
        # Calculate RMS energy
        rms = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop_length)[0]
        
        # Find silence frames
        silence_threshold = self.config["silence_threshold"]
        non_silent_frames = rms > silence_threshold
        
        # Convert frame indices to sample indices
        frame_to_sample = lambda f: f * hop_length
        
        # Find continuous non-silent regions
        segments = []
        start_frame = None
        
        for i, is_speech in enumerate(non_silent_frames):
            if is_speech and start_frame is None:
                start_frame = i
            elif not is_speech and start_frame is not None:
                # End of speech segment
                start_sample = frame_to_sample(start_frame)
                end_sample = frame_to_sample(i)
                
                segment = audio[start_sample:end_sample]
                duration = len(segment) / sr
                
                if (duration >= self.config["min_duration"] and 
                    duration <= self.config["max_duration"]):
                    segments.append(segment)
                
                start_frame = None
        
        # Handle case where audio ends with speech
        if start_frame is not None:
            start_sample = frame_to_sample(start_frame)
            segment = audio[start_sample:]
            if len(segment) / sr >= self.config["min_duration"]:
                segments.append(segment)
        
        # If no segments found, use entire audio as one segment
        if not segments and len(audio) / sr >= self.config["min_duration"]:
            segments.append(audio)
        
        return segments
    
    def _create_training_manifest(self, 
                                audio_segments: List[str], 
                                text_content: str, 
                                dataset_dir: Path,
                                dataset_name: str) -> str:
        """
        Create training manifest file
        
        Args:
            audio_segments: List of audio segment paths
            text_content: Full text content
            dataset_dir: Dataset directory
            dataset_name: Name of the dataset
            
        Returns:
            Path to manifest file
        """
        logger.info("Creating training manifest...")
        
        # Split text into segments (roughly match audio segments)
        text_lines = text_content.replace('\n', ' ').split('.')
        text_lines = [line.strip() for line in text_lines if line.strip()]
        
        # Create manifest entries
        manifest_data = []
        
        for i, audio_path in enumerate(audio_segments):
            # Assign text to audio segment (cycle through text if more audio than text)
            text_index = i % len(text_lines)
            text = text_lines[text_index]
            
            # Make audio path relative to dataset directory
            relative_audio_path = os.path.relpath(audio_path, dataset_dir)
            
            manifest_entry = {
                "audio_path": relative_audio_path,
                "text": text,
                "speaker": dataset_name,
                "duration": self._get_audio_duration(audio_path)
            }
            manifest_data.append(manifest_entry)
        
        # Save manifest
        manifest_path = dataset_dir / "manifest.jsonl"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            for entry in manifest_data:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        logger.info(f"Created manifest with {len(manifest_data)} entries")
        return str(manifest_path)
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            audio, sr = librosa.load(audio_path, sr=None)
            return len(audio) / sr
        except Exception:
            return 0.0
    
    def _create_training_config(self, dataset_dir: Path, dataset_name: str) -> str:
        """
        Create training configuration file
        
        Args:
            dataset_dir: Dataset directory
            dataset_name: Name of the dataset
            
        Returns:
            Path to config file
        """
        logger.info("Creating training configuration...")
        
        config = {
            "model": {
                "name": "fish_speech_s1",
                "vocab_size": 1024,
                "hidden_size": 512,
                "num_layers": 12,
                "num_heads": 8
            },
            "training": {
                "epochs": self.config["training_epochs"],
                "batch_size": self.config["batch_size"],
                "learning_rate": self.config["learning_rate"],
                "warmup_steps": 1000,
                "gradient_clip": 1.0,
                "checkpoint_steps": 1000
            },
            "data": {
                "manifest_path": "manifest.jsonl",
                "sample_rate": self.config["sample_rate"],
                "max_duration": self.config["max_duration"],
                "min_duration": self.config["min_duration"]
            },
            "output": {
                "model_dir": "checkpoints",
                "voice_name": self.config["voice_name"]
            }
        }
        
        config_path = dataset_dir / "training_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created training config: {config_path}")
        return str(config_path)
    
    def start_training(self, dataset_config: Dict[str, str]) -> Dict[str, str]:
        """
        Start Fish Speech training process
        
        Args:
            dataset_config: Configuration from prepare_training_data
            
        Returns:
            Training job information
        """
        logger.info("Starting Fish Speech training...")
        
        dataset_dir = Path(dataset_config["dataset_dir"])
        
        # Check if Fish Speech server supports training
        training_status = self._check_training_capability()
        
        if training_status["supported"]:
            # Use server-based training
            return self._start_server_training(dataset_config)
        else:
            # Use local training simulation
            return self._start_local_training(dataset_config)
    
    def _check_training_capability(self) -> Dict[str, bool]:
        """Check if Fish Speech server supports training"""
        try:
            response = requests.get(f"{self.fish_speech_url}/training/status", timeout=5)
            if response.status_code == 200:
                return {"supported": True, "server": True}
        except Exception:
            pass
        
        # Server doesn't support training
        return {"supported": False, "server": False}
    
    def _start_server_training(self, dataset_config: Dict[str, str]) -> Dict[str, str]:
        """Start training on Fish Speech server"""
        logger.info("Starting server-based training...")
        
        try:
            # Upload training data to server
            upload_response = self._upload_training_data(dataset_config)
            
            # Start training job
            training_response = requests.post(
                f"{self.fish_speech_url}/training/start",
                json={
                    "dataset_id": upload_response["dataset_id"],
                    "config_path": dataset_config["config_path"],
                    "voice_name": self.config["voice_name"]
                },
                timeout=30
            )
            
            if training_response.status_code == 200:
                job_info = training_response.json()
                logger.info(f"Training started with job ID: {job_info.get('job_id')}")
                return {
                    "status": "started",
                    "job_id": job_info.get("job_id"),
                    "method": "server"
                }
            else:
                raise Exception(f"Server training failed: {training_response.text}")
                
        except Exception as e:
            logger.error(f"Server training failed: {e}")
            # Fallback to local training
            return self._start_local_training(dataset_config)
    
    def _start_local_training(self, dataset_config: Dict[str, str]) -> Dict[str, str]:
        """Start local training simulation (for demonstration)"""
        logger.info("Starting local training simulation...")
        
        dataset_dir = Path(dataset_config["dataset_dir"])
        
        # Create checkpoints directory
        checkpoints_dir = dataset_dir / "checkpoints"
        checkpoints_dir.mkdir(exist_ok=True)
        
        # Simulate training process
        logger.info("Simulating Fish Speech training process...")
        logger.info(f"Dataset: {dataset_config['audio_segments']} audio segments")
        logger.info(f"Configuration: {dataset_config['config_path']}")
        
        # Create a simple training log
        training_log = {
            "status": "completed_simulation",
            "dataset_dir": str(dataset_dir),
            "audio_segments": dataset_config["audio_segments"],
            "epochs": self.config["training_epochs"],
            "voice_name": self.config["voice_name"],
            "note": "This is a simulation. For actual training, you need Fish Speech training infrastructure."
        }
        
        log_path = dataset_dir / "training_log.json"
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(training_log, f, indent=2)
        
        logger.info(f"Training simulation completed. Log saved to: {log_path}")
        
        return {
            "status": "simulation_completed",
            "log_path": str(log_path),
            "checkpoints_dir": str(checkpoints_dir),
            "method": "local_simulation"
        }
    
    def _upload_training_data(self, dataset_config: Dict[str, str]) -> Dict[str, str]:
        """Upload training data to Fish Speech server"""
        # This would implement actual data upload to the server
        # For now, return a mock response
        return {"dataset_id": "sonnet29_dataset", "uploaded": True}


def main():
    """Main training function"""
    
    # Configuration
    audio_file = "sonnet29.mp3"
    text_file = "sonnet29_text.txt" 
    
    # Check if files exist
    if not os.path.exists(audio_file):
        logger.error(f"Audio file not found: {audio_file}")
        return
    
    if not os.path.exists(text_file):
        logger.error(f"Text file not found: {text_file}")
        return
    
    # Initialize trainer
    trainer = FishSpeechTrainer()
    
    try:
        # Prepare training data
        logger.info("Step 1: Preparing training data...")
        dataset_config = trainer.prepare_training_data(
            audio_file=audio_file,
            text_file=text_file,
            output_name="sonnet29"
        )
        
        logger.info("Training data prepared successfully!")
        logger.info(f"Dataset directory: {dataset_config['dataset_dir']}")
        logger.info(f"Audio segments: {dataset_config['audio_segments']}")
        
        # Start training
        logger.info("\nStep 2: Starting training...")
        training_result = trainer.start_training(dataset_config)
        
        logger.info("Training process initiated!")
        logger.info(f"Status: {training_result['status']}")
        logger.info(f"Method: {training_result['method']}")
        
        if training_result["method"] == "local_simulation":
            logger.info(f"Training log: {training_result['log_path']}")
            logger.info("\nNOTE: This was a simulation. For actual Fish Speech training, you need:")
            logger.info("1. Fish Speech training environment setup")
            logger.info("2. GPU resources for model training")
            logger.info("3. Fish Speech training API endpoints")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()