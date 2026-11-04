from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    allowed_origins: frozenset[str] = frozenset({"https://localhost"})
    upload_max_bytes: int = 5 * 1024 * 1024
    max_image_pixels: int = 20_000_000
    analyze_per_min: int = 10
    stego_chi2_p: float = .995
    stego_rs_rate: float = .15
    stego_entropy_trigger: float | None = None
    stego_timeout_s: float = 10.0
    @property
    def stego_config(self):
        return {"chi2_p": self.stego_chi2_p, "rs_rate": self.stego_rs_rate, "entropy_trigger": self.stego_entropy_trigger}

def load_settings():
    return Settings(
        allowed_origins=frozenset(filter(None, os.getenv("ALLOWED_ORIGINS", "https://localhost").split(","))),
        upload_max_bytes=int(os.getenv("UPLOAD_MAX_BYTES", 5 * 1024 * 1024)),
        max_image_pixels=int(os.getenv("MAX_IMAGE_PIXELS", 20_000_000)),
        analyze_per_min=int(os.getenv("ANALYZE_PER_MIN", 10)),
        stego_chi2_p=float(os.getenv("STEGO_CHI2_P", .995)), stego_rs_rate=float(os.getenv("STEGO_RS_RATE", .15)),
        stego_timeout_s=float(os.getenv("STEGO_TIMEOUT_S", 10)),
    )
