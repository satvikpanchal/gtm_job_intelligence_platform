"""Worker launcher for distributed processing."""

import os
import sys
import time
import subprocess
import signal
from redis import Redis
from .config import REDIS_URL, EXTRACT_QUEUE, BURST_MODE

# macOS fork safety
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["no_proxy"] = "*"


class WorkerManager:
    """Manages multiple RQ workers for parallel processing."""
    
    def __init__(self, num_workers: int = 5, queue: str = EXTRACT_QUEUE):
        self.num_workers = num_workers
        self.queue = queue
        self.workers = []
        self.redis = Redis.from_url(REDIS_URL)
        
    def start(self):
        """Start worker processes."""
        print(f"🚀 Starting {self.num_workers} workers for queue '{self.queue}'")
        
        for i in range(self.num_workers):
            # Spawn workers as subprocesses (macOS-safe)
            cmd = [
                sys.executable, "-m", "rq.cli", "worker",
                self.queue,
                "--url", REDIS_URL,
                "--burst" if BURST_MODE else ""
            ]
            cmd = [c for c in cmd if c]  # Remove empty strings
            
            proc = subprocess.Popen(
                cmd,
                env={**os.environ},
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            self.workers.append(proc)
            print(f"  Worker {i+1} started (PID: {proc.pid})")
        
        print(f"✅ {len(self.workers)} workers running")
        
    def wait(self):
        """Wait for all workers to complete."""
        print("\n⏳ Waiting for workers to complete...")
        
        while True:
            # Check queue status
            queue_len = self.redis.llen(f"rq:queue:{self.queue}")
            active = sum(1 for w in self.workers if w.poll() is None)
            
            print(f"📊 Queue: {queue_len} | Active workers: {active}", end="\r")
            
            if queue_len == 0 and active == 0:
                print("\n✅ All tasks complete!")
                break
            
            time.sleep(2)
    
    def stop(self):
        """Stop all workers."""
        for w in self.workers:
            if w.poll() is None:
                w.terminate()
        print("✅ All workers stopped")


def main():
    """Run extraction workers."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run extraction workers")
    parser.add_argument("num_workers", type=int, nargs="?", default=5,
                        help="Number of parallel workers")
    args = parser.parse_args()
    
    manager = WorkerManager(num_workers=args.num_workers)
    
    try:
        manager.start()
        manager.wait()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
    finally:
        manager.stop()


if __name__ == "__main__":
    main()
