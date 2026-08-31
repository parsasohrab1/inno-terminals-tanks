"""Stream synthetic sensor readings into the backend ingest endpoint.

    python live_stream.py --api http://127.0.0.1:8010 --interval 2
    python live_stream.py --leak TK-105          # inject a leak on one tank
    python live_stream.py --leak-random 0.02     # 2% chance/tick of a random leak

Requires the backend running and seeded (python -m app.seed).
"""
from __future__ import annotations

import argparse
import random
import sys
import time

import httpx

from sensor_fleet import TankSensor

DEMO_LOGIN = {"username": "admin", "password": "demo1234"}


def get_token(client: httpx.Client, api: str) -> str:
    r = client.post(f"{api}/api/v1/auth/login-json", json=DEMO_LOGIN, timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]


def load_tanks(client: httpx.Client, api: str, token: str) -> list[str]:
    r = client.get(f"{api}/api/v1/tanks", headers={"Authorization": f"Bearer {token}"}, timeout=10)
    r.raise_for_status()
    return [t["code"] for t in r.json()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:8010")
    ap.add_argument("--interval", type=float, default=2.0, help="seconds between batches")
    ap.add_argument("--leak", action="append", default=[], help="tank code to force a leak on")
    ap.add_argument("--leak-random", type=float, default=0.0, help="per-tick random leak probability")
    ap.add_argument("--duration", type=int, default=0, help="stop after N seconds (0 = forever)")
    args = ap.parse_args()

    client = httpx.Client()
    try:
        token = get_token(client, args.api)
        codes = load_tanks(client, args.api, token)
    except Exception as exc:  # noqa: BLE001
        sys.exit(f"cannot reach backend at {args.api}: {exc}")

    if not codes:
        sys.exit("no tanks — run `python -m app.seed` in backend first")

    fleet = {c: TankSensor(tank_code=c, seed=i) for i, c in enumerate(codes)}
    for c in args.leak:
        if c in fleet:
            fleet[c].inject_leak(duration=120)
            print(f"[sim] leak injected on {c}")

    rng = random.Random(0)
    headers = {"Authorization": f"Bearer {token}"}
    started = time.time()
    tick = 0
    print(f"[sim] streaming {len(fleet)} tanks -> {args.api} every {args.interval}s (ctrl-c to stop)")

    while True:
        tick += 1
        if args.leak_random and rng.random() < args.leak_random:
            victim = rng.choice(list(fleet.values()))
            if not victim.leaking:
                victim.inject_leak(duration=rng.randint(60, 150))
                print(f"[sim] random leak on {victim.tank_code}")

        batch = [s.step() for s in fleet.values()]
        try:
            r = client.post(
                f"{args.api}/api/v1/readings/ingest",
                json={"readings": batch, "score": tick % 3 == 0},
                headers=headers, timeout=15,
            )
            r.raise_for_status()
            res = r.json()
            leaking = [c for c, s in fleet.items() if s.leaking]
            print(f"[sim] tick {tick}: stored={res['stored']} alarms={res['alarms_raised']} "
                  f"preds={res['predictions']} leaking={leaking}")
        except Exception as exc:  # noqa: BLE001
            print(f"[sim] ingest error: {exc}")
            if "401" in str(exc):
                token = get_token(client, args.api)
                headers = {"Authorization": f"Bearer {token}"}

        if args.duration and time.time() - started > args.duration:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
