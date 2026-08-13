import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import create_app


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("用法：python scripts/export_openapi.py <输出文件>")

    output_path = Path(sys.argv[1]).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    application = create_app(
        database_path=Path("data/openapi-only.db"),
        jwt_secret="openapi-export-secret-not-used-at-runtime",
    )
    output_path.write_text(
        json.dumps(application.openapi(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
