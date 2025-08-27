# scripts/label_eval.py
import csv, sys, os, requests

API = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
LABELS = sys.argv[2] if len(sys.argv) > 2 else "labels.csv"

def init_labels_from_api(n=30):
    try:
        events = requests.get(f"{API}/events/recent?limit={n}", timeout=5).json()
    except Exception as e:
        print(f"[init] Failed to fetch recent events from {API}: {e}")
        return False
    lines = [
        "# labels.csv format: event_id, keep_or_drop",
        "# use 'keep' for truly actionable events, 'drop' for noise/duplicates",
        "# you can add comments starting with # anywhere",
        "# --- recent events to label below ---",
    ]
    for ev in events:
        rid = ev.get("id")
        red = (ev.get("redacted") or "").replace("\n", " ")[:140]
        lines.append(f"# id={rid} status={ev.get('incident_status')} type={ev.get('event_type')} redacted=\"{red}\"")
        lines.append(f"{rid},drop")
    with open(LABELS, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[init] Wrote template with {len(events)} events to {LABELS}. Edit and re-run.")
    return True

def load_labels(path):
    labels = {}
    with open(path) as f:
        for row in csv.reader(f):
            if not row or row[0].strip().startswith("#"):
                continue
            if len(row) < 2:
                continue
            try:
                eid = int(row[0].strip())
            except ValueError:
                continue
            tag = row[1].strip().lower()
            if tag not in {"keep", "drop"}:
                continue
            labels[eid] = (tag == "keep")
    return labels

def main():
    if not os.path.exists(LABELS):
        if not init_labels_from_api(30):
            print(f"[error] {LABELS} not found and could not initialize from API.")
            sys.exit(2)
        sys.exit(0)

    labels = load_labels(LABELS)
    if not labels:
        print(f"[warn] No labels found in {LABELS}.")
        sys.exit(1)

    misses = 0
    kept = 0
    for eid, should_keep in labels.items():
        ev = requests.get(f"{API}/evidence/{eid}", timeout=5).json()
        if "incident_id" not in ev:
            continue
        inc = requests.get(f"{API}/incidents/{ev['incident_id']}", timeout=5).json()
        if should_keep:
            kept += 1
            if inc.get("status") == "noise":
                misses += 1

    rate = (misses / kept) if kept else 0.0
    print({"kept": kept, "missed": misses, "false_dismissal_rate": round(rate, 3)})

if __name__ == "__main__":
    main()
