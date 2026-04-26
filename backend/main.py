import argparse
import time

import uvicorn

from crew_setup import crew

MAX_OUTPUT_CHARS = 2200


def _format_concise_output(text: str, max_chars: int = MAX_OUTPUT_CHARS) -> str:
    cleaned = text.strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return (
        cleaned[:max_chars].rstrip()
        + "\n\n[Output truncated for readability. Run again with a more specific city/topic for tighter results.]"
    )


def run_cli():

    print("\n=== Healthcare Planning Assistant ===\n")

    topic = input("Enter disease or symptoms: ").strip()
    location = input("Enter your city: ").strip()

    try:
        result = None
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                result = crew.kickoff(
                    inputs={
                        "topic": topic,
                        "location": location
                    }
                )
                break
            except Exception as e:
                error_text = str(e)
                is_rate_limit = "rate_limit_exceeded" in error_text or "Rate limit reached" in error_text
                if is_rate_limit and attempt < max_attempts:
                    wait_seconds = 6 * attempt
                    print(f"\nRate limit hit. Retrying in {wait_seconds} seconds... ({attempt}/{max_attempts})")
                    time.sleep(wait_seconds)
                    continue
                raise

        print("\n" + "=" * 60)
        print("FINAL HEALTHCARE PLAN")
        print("=" * 60 + "\n")

        print(_format_concise_output(str(result)))

    except Exception as e:
        print("\nError occurred while running the agents:")
        print(e)


def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    uvicorn.run("api:app", host=host, port=port, reload=reload)


def main():
    parser = argparse.ArgumentParser(description="Healthcare Planning Assistant")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run interactive CLI mode instead of API server mode",
    )
    parser.add_argument("--host", default="0.0.0.0", help="API host")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload in API mode",
    )
    args = parser.parse_args()

    if args.cli:
        run_cli()
        return

    run_api(host=args.host, port=args.port, reload=not args.no_reload)


if __name__ == "__main__":
    main()