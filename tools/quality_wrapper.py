import json
import re
import subprocess
import sys


def extract_first_json(s):
    """Return the first valid JSON object found in string s, or None."""
    i = s.find("{")
    if i == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    j = i
    while j < len(s):
        c = s[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    frag = s[i : j + 1]
                    try:
                        return json.loads(frag)
                    except Exception:
                        return None
        j += 1
    return None


def _summarize_lint(lint_dict):
    """Return a list of files with errors and counts from a lint dict."""
    files = []
    inner = lint_dict.get("lint", lint_dict) if isinstance(lint_dict, dict) else {}
    if isinstance(inner, dict):
        for fname, res in inner.items():
            errs = res.get("errors") if isinstance(res, dict) else None
            if isinstance(errs, list) and errs:
                files.append({"file": fname, "count": len(errs)})
            elif isinstance(errs, str) and errs.strip():
                files.append({"file": fname, "count": 1})
    return files


def decide_fail(data, out_text, proc_rc):
    """
    Fail if:
      - unittest.returncode != 0 in JSON
      - lint shows errors
      - textual failure signals (returncode in text, 'FAILED', or Traceback)
      - underlying process rc != 0
    """
    if isinstance(data, dict):
        rc = None
        try:
            rc = int(data.get("unittest", {}).get("returncode"))
        except Exception:
            rc = None
        if rc not in (None, 0):
            return True, {"reason": "tests_failed", "unittest_returncode": rc}

        lint_files = _summarize_lint(data.get("lint", {}))
        if lint_files:
            return True, {"reason": "lint_errors", "files": lint_files}

    m = re.search(r'"returncode"\s*:\s*(\d+)', out_text)
    if m:
        try:
            if int(m.group(1)) != 0:
                return True, {"reason": "tests_failed_text"}
        except Exception:
            pass
    if "FAILED" in out_text or "Traceback (most recent call last):" in out_text:
        return True, {"reason": "trace_or_failed_in_text"}

    if proc_rc != 0:
        return True, {"reason": "process_rc_nonzero", "proc_rc": proc_rc}

    return False, None


def main():
    proc = subprocess.run(
        [sys.executable, "-m", "wilbito.interfaces.cli", "quality"],
        capture_output=True,
        text=True,
    )
    out = proc.stdout or ""
    err = proc.stderr or ""

    data = None
    try:
        data = json.loads(out)
    except Exception:
        data = extract_first_json(out)

    if data is None:
        data = {
            "lint": {},
            "unittest": {"returncode": None},
            "meta": {
                "note": "strict mode; non-JSON stdout captured",
                "stdout_head": out[:2000],
                "stderr_head": err[:2000],
                "proc_returncode": proc.returncode,
            },
        }

    fail, meta = decide_fail(data, out, proc.returncode)

    # If failure detected by text, reflect a numeric returncode when possible
    if isinstance(meta, dict) and meta.get("reason") in (
        "tests_failed_text",
        "trace_or_failed_in_text",
    ):
        m = re.search(r'"returncode"\s*:\s*(\d+)', out)
        if m:
            try:
                rc_det = int(m.group(1))
                if isinstance(data, dict):
                    data.setdefault("unittest", {})
                    data["unittest"]["returncode"] = rc_det
            except Exception:
                pass

    if fail:
        # IMPORTANT: no JSON in STDOUT to force executor parse error
        try:
            sys.stdout.write("QUALITY_FAIL\n")
            sys.stderr.write(json.dumps(data, ensure_ascii=False) + "\n")
            if meta:
                sys.stderr.write("REASON: " + json.dumps(meta) + "\n")
        except Exception:
            pass
        sys.exit(1)

    # Success => JSON only to STDOUT
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
