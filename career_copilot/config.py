"""Settings loaded from environment variables (see .env.example)."""
from __future__ import annotations
import os
from dataclasses import dataclass, field


def _load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


@dataclass
class Settings:
    apply_threshold: int = 85
    review_threshold: int = 70
    candidate_skills: list[str] = field(default_factory=list)
    preferred_locations: list[str] = field(default_factory=list)
    max_years_experience: int = 2
    scheduler_api_url: str = ""
    scheduler_api_key: str = ""
    output_dir: str = "output"

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        split = lambda v: [s.strip() for s in v.split(",") if s.strip()]
        return cls(
            apply_threshold=int(os.getenv("APPLY_THRESHOLD", 85)),
            review_threshold=int(os.getenv("REVIEW_THRESHOLD", 70)),
            candidate_skills=split(os.getenv("CANDIDATE_SKILLS", "c#,.net,asp.net core,sql,python,git")),
            preferred_locations=split(os.getenv("PREFERRED_LOCATIONS", "remote")),
            max_years_experience=int(os.getenv("MAX_YEARS_EXPERIENCE", 2)),
            scheduler_api_url=os.getenv("SCHEDULER_API_URL", ""),
            scheduler_api_key=os.getenv("SCHEDULER_API_KEY", ""),
            output_dir=os.getenv("OUTPUT_DIR", "output"),
        )
