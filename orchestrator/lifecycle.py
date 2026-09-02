# orchestrator/lifecycle.py
import subprocess
import requests
import psutil
import time
import os
import json
from registry.registry import (
    IMAGE_REGISTRY, PORT_REGISTRY,
    HEALTH_REGISTRY, VOLUME_REGISTRY,
    RAM_REQUIREMENTS, NEEDS_CONTAINER
)

class Lifecycle:

    # ── Preflight ─────────────────────────
    def preflight(self, stages: list):
        print("\n Preflight checks...")
        for stage in stages:
            if NEEDS_CONTAINER.get(stage):
                image = IMAGE_REGISTRY.get(stage)
                if image:
                    print(f"   pulling {image}...")
                    subprocess.run(
                        ["podman", "pull", image],
                        check=True
                    )
        print(" Preflight complete\n")

    # ── RAM check ─────────────────────────
    def check_ram(self, stage: str, budget_gb: float):
        available = psutil.virtual_memory().available / (1024**3)
        required  = RAM_REQUIREMENTS.get(stage, 1.0)
        print(f" RAM — available: {available:.1f}GB "
              f"required: {required}GB")
        if available < required:
            raise RuntimeError(
                f" Not enough RAM for {stage}. "
                f"Need {required}GB have {available:.1f}GB"
            )

    # ── Start container ───────────────────
    def start(self, stage: str):
        if not NEEDS_CONTAINER.get(stage):
            print(f" {stage}=pure Python, no container")
            return
        container_name = f"rice_{stage}"

        subprocess.run(["podman", "rm", "-f", container_name],capture_output=True)   # suppress output if not found 
        import time
        time.sleep(1)
        image   = IMAGE_REGISTRY[stage]
        ports   = PORT_REGISTRY.get(stage, ())
        volumes = VOLUME_REGISTRY.get(stage, [])

        cmd = ["podman", "run", "-d",
               "--name", f"rice_{stage}",
               "--rm",]                       # auto remove on stop

        if ports:
            cmd += ["-p", f"{ports[0]}:{ports[1]}"]

        for vol in volumes:
            cmd += ["-v", vol]

        cmd.append(image)

        print(f" Starting {stage}...")
        print(f"   cmd: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f" Failed to start {stage}: \n {result.stderr}")
        print(f"   container id: {result.stdout.strip()[:12]}")
    # ── Health check ──────────────────────
    def health_check(self, stage: str, retries: int = 15):
        if not NEEDS_CONTAINER.get(stage):
            return

        url = HEALTH_REGISTRY[stage]
        print(f" Waiting for {stage} at {url}")
        for attempt in range(retries):
            try:
                r = requests.get(url, timeout=2)
                if r.status_code == 200:
                    print(f" {stage} is ready")
                    return
            except Exception as e:
                print(f" Attempt {attempt+1}/{retries}: {e}")
            time.sleep(3)
        print(f"\n📋 Container logs for {stage}:")
        subprocess.run(["podman", "logs", f"rice_{stage}"])
        raise RuntimeError(f" {stage} failed to start after {retries} retries")

    # ── Stop container ────────────────────
    def stop(self, stage: str):
        if not NEEDS_CONTAINER.get(stage):
            return

        print(f" Stopping {stage}...")
        subprocess.run(
            ["podman", "stop", f"rice_{stage}"],
            check=True
        )
        self._log_ram(stage)

    # ── Cache helpers ─────────────────────
    def save_cache(self, stage: str, data, cache_dir: str):
        os.makedirs(cache_dir, exist_ok=True)
        path = os.path.join(cache_dir, "output.json")
        with open(path, "w") as f:
            json.dump(data, f)
        print(f" {stage} output saved → {path}")

    def load_cache(self, stage: str, cache_dir: str):
        path = os.path.join(cache_dir, "output.json")
        if not os.path.exists(path):
            raise RuntimeError(
                f" Cache not found for {stage} at {path}. "
                f"Did previous stage complete?"
            )
        with open(path, "r") as f:
            data = json.load(f)
        print(f" Loaded {stage} cache from {path}")
        return data

    # ── RAM logger ────────────────────────
    def _log_ram(self, after_stage: str):
        ram  = psutil.virtual_memory()
        used = ram.used / (1024**3)
        free = ram.available / (1024**3)
        print(f" RAM after {after_stage}: "
              f"{used:.1f}GB used | {free:.1f}GB free")