"""Checkpoint manager for saving/restoring component state."""
import json
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from autocoder_cc.observability import get_logger

class CheckpointManager:
    """Manages checkpoints for components."""
    
    def __init__(self, checkpoint_dir: Path = Path("checkpoints")):
        self.logger = get_logger("CheckpointManager")
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
    def save_checkpoint(self, component_name: str, state: Dict[str, Any], 
                       metadata: Optional[Dict] = None) -> Path:
        """Save component state to checkpoint."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # Add microseconds for uniqueness
        checkpoint_file = self.checkpoint_dir / f"{component_name}_{timestamp}.checkpoint"
        
        checkpoint = {
            'component_name': component_name,
            'timestamp': timestamp,
            'state': state,
            'metadata': metadata or {}
        }
        
        with open(checkpoint_file, 'wb') as f:
            pickle.dump(checkpoint, f)
        
        self.logger.info(f"Saved checkpoint: {checkpoint_file}")
        return checkpoint_file
    
    def load_checkpoint(self, checkpoint_file: Path) -> Dict[str, Any]:
        """Load checkpoint from file."""
        with open(checkpoint_file, 'rb') as f:
            checkpoint = pickle.load(f)
        
        self.logger.info(f"Loaded checkpoint: {checkpoint_file}")
        return checkpoint
    
    def get_latest_checkpoint(self, component_name: str) -> Optional[Path]:
        """Get latest checkpoint for component."""
        pattern = f"{component_name}_*.checkpoint"
        checkpoints = list(self.checkpoint_dir.glob(pattern))
        
        if checkpoints:
            return max(checkpoints, key=lambda p: p.stat().st_mtime)
        return None
    
    def list_checkpoints(self, component_name: Optional[str] = None) -> List[Path]:
        """List all checkpoints."""
        if component_name:
            pattern = f"{component_name}_*.checkpoint"
        else:
            pattern = "*.checkpoint"
        
        return sorted(self.checkpoint_dir.glob(pattern))
    
    def cleanup_old_checkpoints(self, component_name: str, keep: int = 5):
        """Remove old checkpoints, keeping only the latest N."""
        checkpoints = self.list_checkpoints(component_name)
        
        if len(checkpoints) > keep:
            for checkpoint in checkpoints[:-keep]:
                checkpoint.unlink()
                self.logger.info(f"Removed old checkpoint: {checkpoint}")