#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crea/verifica un seed determinÃ­stico en state/seed.json.
Uso:
  python tools/seed_check.py --state state/seed.json --create-if-missing [--force]
"""
import argparse, json, os, random, time, datetime, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="state/seed.json")
    ap.add_argument("--create-if-missing", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    state_path = args.state
    os.makedirs(os.path.dirname(state_path), exist_ok=True)

    if os.path.exists(state_path) and not args.force:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Seed OK -> {data.get('seed')} (created_at={data.get('created_at')})")
        return 0

    seed = int(time.time()) ^ random.randint(1, 1_000_000)
    data = {
        "seed": seed,
        "created_at": datetime.datetime.utcnow().isoformat()+"Z",
        "source": "tools/seed_check.py"
    }
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Seed created -> {seed} -> {state_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())