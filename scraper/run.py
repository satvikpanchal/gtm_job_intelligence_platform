#!/usr/bin/env python3
"""
Run Workers - Launch multiple RQ workers in parallel.
macOS-safe with burst mode to avoid fork() issues.
"""

import os
import sys
import signal
import subprocess
import time
import argparse
from typing import List

# macOS fork safety
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["no_proxy"] = "*"

from .config import REDIS_URL, QUEUE_NAME, DEFAULT_WORKERS


class WorkerManager:
    def __init__(self, num_workers: int, queue: str):
        self.num_workers = num_workers
        self.queue = queue
        self.processes: List[subprocess.Popen] = []
        self.running = True
        
        # Handle Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print("\n🛑 Stopping workers...")
        self.running = False
        self.stop_all()
    
    def start_worker(self, worker_id: int) -> subprocess.Popen:
        """Start a single worker process using burst mode."""
        cmd = [
            sys.executable, "-c",
            f"""
import os
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["no_proxy"] = "*"

from redis import Redis
from rq import Worker, Queue

redis_conn = Redis.from_url("{REDIS_URL}")
queue = Queue("{self.queue}", connection=redis_conn)

# Burst mode: process jobs then exit (safer on macOS)
worker = Worker([queue], connection=redis_conn, name="worker-{worker_id}")
worker.work(burst=True)
"""
        ]
        
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
    
    def start_all(self):
        """Start all workers and keep them running until queue is empty."""
        print("=" * 60)
        print(f"🚀 STARTING {self.num_workers} WORKERS")
        print(f"   Queue: {self.queue}")
        print(f"   Redis: {REDIS_URL}")
        print("=" * 60)
        
        # Initial launch
        for i in range(self.num_workers):
            proc = self.start_worker(i)
            self.processes.append(proc)
            print(f"[{i+1}/{self.num_workers}] Started worker (PID: {proc.pid})")
        
        print(f"\n✅ Started {self.num_workers} workers")
        print("⏹️  Press Ctrl+C to stop\n")
        
        # Monitor and restart workers until queue is empty
        from redis import Redis
        redis_conn = Redis.from_url(REDIS_URL)
        
        while self.running:
            # Check queue length
            queue_len = redis_conn.llen(f"rq:queue:{self.queue}")
            active_workers = sum(1 for p in self.processes if p.poll() is None)
            
            if queue_len == 0 and active_workers == 0:
                print("\n✅ Queue empty, all jobs complete!")
                break
            
            # Restart any finished workers if queue not empty
            if queue_len > 0:
                for i, proc in enumerate(self.processes):
                    if proc.poll() is not None:  # Worker finished
                        self.processes[i] = self.start_worker(i)
            
            # Status update
            print(f"\r📊 Queue: {queue_len} | Active workers: {active_workers}  ", end="", flush=True)
            time.sleep(1)
        
        self.stop_all()
    
    def stop_all(self):
        """Stop all workers."""
        for i, proc in enumerate(self.processes):
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        
        print("\n✅ All workers stopped")


def main():
    parser = argparse.ArgumentParser(description="Run parallel RQ workers")
    parser.add_argument("workers", type=int, nargs="?", default=DEFAULT_WORKERS,
                        help=f"Number of workers (default: {DEFAULT_WORKERS})")
    parser.add_argument("--queue", "-q", default=QUEUE_NAME,
                        help=f"Queue name (default: {QUEUE_NAME})")
    args = parser.parse_args()
    
    manager = WorkerManager(args.workers, args.queue)
    manager.start_all()


if __name__ == "__main__":
    main()
