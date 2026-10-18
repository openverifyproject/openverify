"""Bounded-process worker for potentially expensive authored stdlib regex patterns."""

import json
import re
import sys


def main() -> None:
    data = json.load(sys.stdin)
    print(
        json.dumps([re.search(pattern, data["text"]) is not None for pattern in data["patterns"]])
    )


if __name__ == "__main__":
    main()
