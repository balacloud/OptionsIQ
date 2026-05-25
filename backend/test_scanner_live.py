"""
Live diagnostic: test get_scanner_batch() via IBWorker.
Run from backend/ with IB Gateway connected:
  python3 test_scanner_live.py
"""
import os
import sys
import logging

# load_dotenv must come first — module-level os.getenv() runs at import time
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

from constants import ETF_TICKERS
from ib_worker import IBWorker

TICKERS = sorted(ETF_TICKERS)


def _discover_scan_codes(provider) -> None:
    """Print all available scan codes from IBKR that mention volatility or put/call."""
    provider._ensure_connected()
    xml = provider.ib.reqScannerParameters()
    import re
    print(f"XML length: {len(xml)} chars, first 300: {xml[:300]!r}")
    codes = re.findall(r'<scanCode>(.*?)</scanCode>', xml)
    vol_codes = [c for c in codes if any(k in c.upper() for k in
                  ["VOL", "IV", "HIST", "PUT", "CALL", "OPTION", "OPT"])]
    print(f"\nAvailable vol/options-related scan codes ({len(vol_codes)} of {len(codes)} total):")
    for c in sorted(vol_codes):
        print(f"  {c}")
    print()


def main():
    print(f"\n{'='*60}")
    print(f"Scanner live test — {len(TICKERS)} ETFs")
    print(f"IB Gateway: {os.getenv('IBKR_HOST', '127.0.0.1')}:{os.getenv('IBKR_PORT', '4001')}")
    print(f"{'='*60}\n")

    worker = IBWorker()  # thread starts automatically in __init__

    try:
        # Step 0: discover available scan codes
        print("Fetching available scanner codes from IBKR...")
        worker.submit(_discover_scan_codes, worker.provider, timeout=10.0)

        print("Testing individual scanner passes with raw distance values...\n")

        def _run_scan_raw(provider, scan_code, wait=15.0, max_rows=5000):
            from ib_insync import ScannerSubscription
            provider._ensure_connected()
            sub = ScannerSubscription(numberOfRows=max_rows, instrument="STK",
                                      locationCode="STK.US.MAJOR", scanCode=scan_code)
            scan_list = provider.ib.reqScannerSubscription(sub)
            provider.ib.sleep(wait)
            provider.ib.cancelScannerSubscription(scan_list)
            ticker_set = set(TICKERS)
            all_syms = [item.contractDetails.contract.symbol.upper() for item in scan_list]
            hits = [(item.contractDetails.contract.symbol, item.distance, item.rank)
                    for item in scan_list
                    if item.contractDetails.contract.symbol.upper() in ticker_set]
            print(f"  [total rows received: {len(all_syms)}, sample top-10: {all_syms[:10]}]")
            return hits

        scan_tests = [
            ("HIGH_OPT_IMP_VOLAT_OVER_HIST",     "IV/HV ratio (%)"),
            ("HIGH_OPT_VOLUME_PUT_CALL_RATIO",    "Put/Call volume ratio"),
            ("SCAN_ivRank52w_DESC",               "52-week IV Rank (IVR)"),
        ]

        for code, label in scan_tests:
            print(f"--- {code} ({label}) ---")
            try:
                hits = worker.submit(_run_scan_raw, worker.provider, code, timeout=30.0)
                if hits:
                    for sym, dist, rank in sorted(hits):
                        print(f"  {sym:<8} rank={rank:<4} distance={dist!r}")
                    print(f"  → {len(hits)}/{len(TICKERS)} ETFs found")
                else:
                    print("  → 0 ETFs found in received rows")
            except Exception as exc:
                print(f"  ERROR: {exc}")
            print()

    except Exception as exc:
        print(f"\nERROR: {exc}")
        import traceback; traceback.print_exc()
    finally:
        worker.stop()
        print("\nDone.")


if __name__ == "__main__":
    main()
