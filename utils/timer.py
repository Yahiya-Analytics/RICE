import time
class StageTimer:
    """
    Tracks elapsed time per stage and prints a summary table at the end.
    Usage:
        timer = StageTimer()
        timer.start("ingestion")
        ... do work ...
        timer.stop("ingestion")
        timer.summary()
    """
    STAGE_ORDER = [
        "ingestion",
        "chunking",
        "embeddings",
        "vector_db",
        "retrieval",
        "rag",
        "llm",
    ]

    def __init__(self):
        self._start_times: dict[str, float] = {}
        self._elapsed:     dict[str, float] = {}

    def start(self, stage: str) -> None:
        self._start_times[stage] = time.perf_counter()

    def stop(self, stage: str) -> float:
        if stage not in self._start_times:
            return 0.0
        elapsed = time.perf_counter() - self._start_times[stage]
        self._elapsed[stage] = elapsed
        print(f" {stage} completed in {self._fmt(elapsed)}")
        return elapsed

    def summary(self) -> None:
        if not self._elapsed:
            return

        total = sum(self._elapsed.values())
        max_t = max(self._elapsed.values()) or 1.0

        print()
        print("⏱ Pipeline Timing Summary")
        print("-" * 46)

        # print stages in canonical order, then any extras
        ordered = [s for s in self.STAGE_ORDER if s in self._elapsed]
        extras  = [s for s in self._elapsed if s not in self.STAGE_ORDER]

        for stage in ordered + extras:
            t    = self._elapsed[stage]
            bar  = self._bar(t, max_t)
            name = stage.ljust(12)
            print(f"  {name}  {self._fmt(t).rjust(8)}  {bar}")

        print("─" * 46)
        print(f"  {'TOTAL'.ljust(12)}  {self._fmt(total).rjust(8)}")
        print("-" * 46)
        print()

    @staticmethod
    def _fmt(seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.1f}s"
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}m {s:.0f}s"

    @staticmethod
    def _bar(t: float, max_t: float, width: int = 16) -> str:
        filled = int((t / max_t) * width)
        return "█" * filled + "░" * (width - filled)