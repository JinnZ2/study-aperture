"""CC0. Offline stdlib primitives for the isolated assessor experiment."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

MISSING = {"$missing": True}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def strict_json(data):
    def reject(value):
        raise ValueError("nonfinite JSON number: " + value)
    return json.loads(data, object_pairs_hook=_pairs, parse_constant=reject)


def strict_load(path):
    return strict_json(Path(path).read_bytes().decode("utf-8"))


def dump_json(path, data):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("path must be a nonempty relative path")
    if ".." in Path(relative).parts:
        raise ValueError("parent traversal is not allowed")
    root = Path(root).resolve()
    result = (root / relative).resolve()
    if not result.is_relative_to(root):
        raise ValueError("path escapes declared root")
    return result


def fresh_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=False)
    return path


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def field_value(obj, dotted_path):
    value = obj
    for part in dotted_path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        else:
            return dict(MISSING)
    return value


def count_outcomes(items):
    counts = {key: 0 for key in ("PASS", "FAIL", "UNSCORABLE", "NOT_ASSESSED")}
    for item in items:
        if item not in counts:
            raise ValueError("unknown outcome " + repr(item))
        counts[item] += 1
    counts["denominator"] = sum(counts.values())
    counts["scorable_denominator"] = counts["PASS"] + counts["FAIL"]
    return counts
