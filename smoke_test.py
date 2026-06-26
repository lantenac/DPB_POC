#!/usr/bin/env python3
"""Smoke-test the BaSyx Battery Pass POC.

Queries the seeded Battery Pass submodel via the BaSyx v2 REST API and prints
key regulated properties. Exits non-zero if anything is missing.
"""
import base64
import json
import os
import sys
import urllib.request

ENV_BASE = os.environ.get("AAS_ENV_BASE", "http://localhost:8081")
SM_ID = os.environ.get("SM_ID", "https://schneider-electric.com/ids/sm/battery_pass/9089016745673456")


def b64(identifier: str) -> str:
    return base64.urlsafe_b64encode(identifier.encode()).decode()


def get_json(url: str):
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read())


def walk(elements, prefix=""):
    out = {}
    for el in elements:
        name = f"{prefix}{el.get('idShort')}"
        if el.get("modelType") == "SubmodelElementCollection":
            out.update(walk(el.get("value", []), prefix=f"{name}."))
        elif "value" in el:
            out[name] = el["value"]
    return out


def main():
    url = f"{ENV_BASE}/submodels/{b64(SM_ID)}"
    print(f"[GET] {url}")
    sm = get_json(url)

    print(f"\nSubmodel : {sm.get('idShort')}  (id={sm.get('id')})")
    semantic = sm.get("semanticId", {}).get("keys", [{}])[0].get("value")
    print(f"semanticId: {semantic}")

    flat = walk(sm.get("submodelElements", []))
    expected = [
        "BatteryIdentification.BatteryPassIdentifier",
        "PerformanceAndDurability.BatteryChemistry",
        "PerformanceAndDurability.RatedCapacity",
        "StateOfHealth.StateOfHealth",
        "CarbonFootprint.CarbonFootprintTotal",
        "MaterialComposition.RecycledContentCobalt",
    ]

    print("\nKey properties:")
    missing = []
    for key in expected:
        if key in flat:
            print(f"  {key:<48} = {flat[key]}")
        else:
            missing.append(key)

    if missing:
        print(f"\n[FAIL] missing properties: {missing}", file=sys.stderr)
        sys.exit(1)
    print(f"\n[PASS] {len(expected)} key properties verified, {len(flat)} total properties present.")


if __name__ == "__main__":
    main()
