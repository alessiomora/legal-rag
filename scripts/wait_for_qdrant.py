import os
import time
from urllib.error import URLError
from urllib.request import urlopen


def main() -> None:
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333").rstrip("/")
    timeout_seconds = int(os.getenv("QDRANT_WAIT_TIMEOUT", "60"))
    deadline = time.time() + timeout_seconds
    health_url = f"{qdrant_url}/collections"

    while time.time() < deadline:
        try:
            with urlopen(health_url, timeout=2) as response:
                if response.status < 500:
                    print(f"Qdrant is reachable at {qdrant_url}")
                    return
        except URLError:
            pass
        time.sleep(1)

    raise SystemExit(
        f"Timed out waiting for Qdrant at {qdrant_url} after {timeout_seconds}s"
    )


if __name__ == "__main__":
    main()
