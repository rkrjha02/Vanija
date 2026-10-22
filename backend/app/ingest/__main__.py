"""Load the policy files into the database.

Run from backend/:  python -m app.ingest
"""

import asyncio
import sys

from app.config import settings
from app.data.database import async_session, engine
from app.ingest.ingest import ingest_policies


async def main() -> int:
    print(f"Reading policies from {settings.policies_dir}")
    async with async_session() as session:
        report = await ingest_policies(session)
    await engine.dispose()

    for name in report.loaded:
        print(f"  loaded   {name}")
    for name in report.skipped:
        print(f"  skipped  {name} (unchanged)")
    for name in report.removed:
        print(f"  removed  {name} (file no longer in policies/)")
    for name, reason in report.failed.items():
        print(f"  FAILED   {name}: {reason}")
    print(f"Done: {len(report.loaded)} loaded, {len(report.skipped)} skipped, "
          f"{len(report.removed)} removed, {len(report.failed)} failed.")
    return 1 if report.failed else 0


if __name__ == "__main__":
    kwargs = {}
    if sys.platform == "win32":
        kwargs["loop_factory"] = asyncio.SelectorEventLoop
    sys.exit(asyncio.run(main(), **kwargs))
