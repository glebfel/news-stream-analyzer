import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in [
    ROOT / "libs" / "common" / "src",
    ROOT / "services" / "processor" / "src",
    ROOT / "services" / "nlp_worker" / "src",
    ROOT / "services" / "vk_collector" / "src",
    ROOT / "services" / "telegram_collector" / "src",
    ROOT / "services" / "graph_builder" / "src",
    ROOT / "services" / "api_gateway" / "src",
]:
    sys.path.insert(0, str(p))
