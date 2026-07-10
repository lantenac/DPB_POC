#!/usr/bin/env python3
"""Register all sample Battery Pass AAS + submodels into the BaSyx AAS Environment.

Reads every *.json file in seed/ and POSTs each shell and submodel to the
BaSyx v2 AAS Environment REST API (AAS Part 2 HTTP/REST). Idempotent: if an
element already exists (HTTP 409) it is updated via PUT instead.
"""
import base64
import glob
import json
import os
import sys
import time
import urllib.error
import urllib.request

ENV_BASE = os.environ.get("AAS_ENV_BASE", "http://localhost:8081")
SEED_DIR = os.environ.get("SEED_DIR", os.path.join(os.path.dirname(__file__), "seed"))


def b64(identifier: str) -> str:
    """Base64URL-encode an identifier as required by the BaSyx v2 path syntax."""
    return base64.urlsafe_b64encode(identifier.encode()).decode()


def request(method: str, url: str, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def wait_for_env(retries: int = 60, delay: float = 5.0):
    for i in range(retries):
        try:
            status, _ = request("GET", f"{ENV_BASE}/shells")
            if status == 200:
                print(f"[ok] AAS Environment reachable at {ENV_BASE}")
                return
        except Exception:
            pass
        print(f"[..] waiting for AAS Environment ({i + 1}/{retries})")
        time.sleep(delay)
    print(f"[!!] AAS Environment not reachable at {ENV_BASE}", file=sys.stderr)
    sys.exit(1)


def upsert(collection: str, obj: dict):
    """POST to the repo; on conflict, PUT to the element-specific endpoint."""
    identifier = obj["id"]
    status, body = request("POST", f"{ENV_BASE}/{collection}", obj)
    if status in (200, 201):
        print(f"[ok] created {collection[:-1]}: {identifier}")
    elif status == 409:
        status, body = request("PUT", f"{ENV_BASE}/{collection}/{b64(identifier)}", obj)
        if status in (200, 204):
            print(f"[ok] updated {collection[:-1]}: {identifier}")
        else:
            print(f"[!!] update failed ({status}) for {identifier}: {body}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"[!!] create failed ({status}) for {identifier}: {body}", file=sys.stderr)
        sys.exit(1)


def load_seed_files():
    paths = sorted(glob.glob(os.path.join(SEED_DIR, "*.json")))
    if not paths:
        print(f"[!!] no *.json files found in {SEED_DIR}", file=sys.stderr)
        sys.exit(1)

    submodels, shells = [], []
    for path in paths:
        print(f"[..] loading {os.path.basename(path)}")
        with open(path) as f:
            env = json.load(f)
        submodels.extend(env.get("submodels", []))
        shells.extend(env.get("assetAdministrationShells", []))
    return submodels, shells


def main():
    submodels, shells = load_seed_files()

    wait_for_env()

    for sm in submodels:
        upsert("submodels", sm)
    for shell in shells:
        upsert("shells", shell)

    print("\n[done] Seed data registered. Sample identifiers:")
    for shell in shells:
        print(f"   AAS id : {shell['id']}")
        for said in shell.get("assetInformation", {}).get("specificAssetIds", []):
            if said["name"] == "SerialNumber":
                print(f"   Serial : {said['value']}")


if __name__ == "__main__":
    main()
