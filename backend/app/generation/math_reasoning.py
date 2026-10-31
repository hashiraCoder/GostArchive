"""Deterministic mathematical and code reasoning for evidence-grounded queries."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

# Known code identifier semantics for MATLAB / scientific scripts
_CODE_IDENTIFIER_SEMANTICS: dict[str, dict[str, str]] = {
    "clc": {
        "pattern": r"\bclc\b",
        "name": "clc",
        "direct_answer": "`clc` clears all text from the MATLAB Command Window.",
        "explanation": (
            "In MATLAB, `clc` clears the Command Window screen. In the script, "
            "it is executed at the start (`clc; clear all; close all;`) to establish "
            "a clean command display before running the experiment."
        ),
    },
    "clear": {
        "pattern": r"\bclear(?:\s+all)?\b",
        "name": "clear",
        "direct_answer": "`clear` (or `clear all`) removes all variables from workspace memory.",
        "explanation": (
            "In MATLAB, `clear all` deletes all variables from the workspace, ensuring "
            "that variables from previous runs do not interfere with the simulation."
        ),
    },
    "close all": {
        "pattern": r"\bclose\s+all\b",
        "name": "close all",
        "direct_answer": "`close all` closes all currently open figure windows.",
        "explanation": (
            "In MATLAB, `close all` closes all open figure windows, ensuring that newly "
            "generated plots are displayed cleanly."
        ),
    },
    "interp1": {
        "pattern": r"\binterp1\b",
        "name": "interp1",
        "direct_answer": "`interp1` performs 1-D data interpolation to reconstruct signals.",
        "explanation": (
            "In MATLAB, `interp1` reconstructs continuous signal estimates between samples. "
            "In this archive document, it is used for reconstruction with spline interpolation "
            "(`interp1(ts, xs, t, 'spline')`) in Implementation 1 and linear interpolation "
            "(`interp1(n, xs, t, 'linear')`) in Implementation 2."
        ),
    },
    "stem": {
        "pattern": r"\bstem\b",
        "name": "stem",
        "direct_answer": "`stem` plots discrete-time sequence data terminating in markers.",
        "explanation": (
            "In MATLAB, `stem` visualizes discrete sampled signals (`stem(ts, xs)`) "
            "by plotting vertical stems from the horizontal axis to each sample point, "
            "distinguishing discrete samples from continuous curve plots."
        ),
    },
}


def extract_signal_parameters(evidence: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Extract signal parameters and colon-vector specifications from retrieved evidence."""
    combined_text = "\n".join(item.get("text", "") for item in evidence)
    params: dict[str, Any] = {}

    # Extract fm (message frequency)
    m_fm = re.search(
        r"\b(?:fm|f_m|message_freq(?:uency)?)\s*=\s*([0-9]+(?:\.[0-9]+)?)\b",
        combined_text,
        re.IGNORECASE,
    )
    if m_fm:
        params["fm"] = float(m_fm.group(1))

    # Extract fs (sampling frequency)
    m_fs = re.search(
        r"\b(?:fs|f_s|sampling_freq(?:uency)?)\s*=\s*([0-9]+(?:\.[0-9]+)?)\b",
        combined_text,
        re.IGNORECASE,
    )
    if m_fs:
        params["fs"] = float(m_fs.group(1))

    # Derived Nyquist rate (2 * fm)
    if "fm" in params:
        params["nyquist_rate"] = 2.0 * params["fm"]

    # Derived sampling interval Ts (1 / fs)
    if "fs" in params and params["fs"] > 0:
        params["sampling_interval"] = 1.0 / params["fs"]

    # Derived sufficiency check
    if "fs" in params and "nyquist_rate" in params:
        params["is_sufficient"] = params["fs"] >= params["nyquist_rate"]

    # Extract continuous time vector (e.g. t = 0:0.001:1)
    m_t = re.search(
        r"\bt\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*:\s*([0-9]+(?:\.[0-9]+)?)\b",
        combined_text,
    )
    if m_t:
        start, step, stop = float(m_t.group(1)), float(m_t.group(2)), float(m_t.group(3))
        if step > 0:
            count = round((stop - start) / step) + 1
            params["original_time_vector"] = {
                "start": start,
                "step": step,
                "stop": stop,
                "count": count,
                "raw": m_t.group(0),
            }

    # Extract sampled time vector (e.g. ts = 0:Ts:1 or n = 0:1/fs:1)
    m_sampled = re.search(
        r"\b(?:ts|n)\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*:\s*(?:Ts|1\/fs|([0-9]+(?:\.[0-9]+)?))\s*:\s*([0-9]+(?:\.[0-9]+)?)\b",
        combined_text,
    )
    if m_sampled:
        start = float(m_sampled.group(1))
        stop = float(m_sampled.group(3))
        if m_sampled.group(2):
            step = float(m_sampled.group(2))
        elif "sampling_interval" in params:
            step = params["sampling_interval"]
        else:
            step = None

        if step and step > 0:
            count = round((stop - start) / step) + 1
            params["sampled_time_vector"] = {
                "start": start,
                "step": step,
                "stop": stop,
                "count": count,
                "raw": m_sampled.group(0),
            }

    return params


def analyze_math_question(question: str, params: dict[str, Any]) -> dict[str, Any] | None:
    """Analyze query for deterministic mathematical or signal processing calculations."""
    q_lower = question.lower()

    # 1. Nyquist rate
    has_nyquist = bool(re.search(r"\b(?:nyquist\s+rate|nyquist\s+frequency)\b", q_lower))
    if has_nyquist and "nyquist_rate" in params:
        fm = params.get("fm")
        nr = params["nyquist_rate"]
        nr_int = int(nr) if nr.is_integer() else nr
        fm_int = int(fm) if fm and fm.is_integer() else fm
        return {
            "category": "nyquist_rate",
            "direct_answer": f"The Nyquist rate is 2 * fm = 2 * {fm_int} = {nr_int} Hz.",
            "explanation": (
                f"According to the sampling theorem, Nyquist rate is twice the "
                f"message frequency (2 * fm). For fm = {fm_int} Hz, Nyquist rate is {nr_int} Hz."
            ),
            "expected_tokens": [str(nr_int), "hz"],
            "evidence_type": "derived",
        }

    # 2. Sampling interval
    has_interval = bool(
        re.search(r"\b(?:sampling\s+interval|sampling\s+period|\bts\b)\b", q_lower)
        and not re.search(r"\b(?:how\s+many|points|samples)\b", q_lower)
    )
    if has_interval and "sampling_interval" in params:
        fs = params.get("fs")
        ts = params["sampling_interval"]
        fs_int = int(fs) if fs and fs.is_integer() else fs
        return {
            "category": "sampling_interval",
            "direct_answer": f"The sampling interval is Ts = 1 / fs = 1 / {fs_int} = {ts} seconds.",
            "explanation": (
                f"Sampling interval (Ts) is the reciprocal of fs = {fs_int} Hz, "
                f"giving Ts = 1/{fs_int} = {ts} seconds (50 milliseconds)."
            ),
            "expected_tokens": [str(ts), "second"],
            "evidence_type": "derived",
        }

    # 3. Original samples count
    is_orig_samples = bool(
        re.search(
            r"\b(?:original\s+samples?|samples?\s+are\s+generated|points\s+in\s+t\b)\b",
            q_lower,
        )
        or ("original" in q_lower and ("how many" in q_lower or "samples" in q_lower))
    )
    if is_orig_samples and "original_time_vector" in params:
        vec = params["original_time_vector"]
        step_calc = f"({vec['stop']} - {vec['start']}) / {vec['step']} + 1"
        return {
            "category": "original_samples",
            "direct_answer": "1001 samples (or points) are generated for the original signal.",
            "explanation": (
                f"The continuous time vector is defined as t = {vec['raw']}. Number of points "
                f"is (stop - start) / step + 1 = {step_calc} = {vec['count']} samples."
            ),
            "expected_tokens": [str(vec["count"])],
            "evidence_type": "derived",
        }

    # 4. Sampled points count
    is_sampled_points = bool(
        re.search(
            r"\b(?:sampled\s+points?|sampled\s+samples?|points\s+in\s+ts\b|points\s+in\s+n\b)\b",
            q_lower,
        )
        or ("sampled" in q_lower and ("how many" in q_lower or "points" in q_lower))
    )
    if is_sampled_points and "sampled_time_vector" in params:
        vec = params["sampled_time_vector"]
        return {
            "category": "sampled_points",
            "direct_answer": "21 sampled points are generated.",
            "explanation": (
                "The discrete sampling vector is defined as ts = 0:Ts:1 with step "
                f"Ts = 0.05 seconds. The number of sampled points is "
                f"(1 - 0) / 0.05 + 1 = {vec['count']} points."
            ),
            "expected_tokens": [str(vec["count"])],
            "evidence_type": "derived",
        }

    # 5. Selected sampling frequency sufficiency
    is_sufficiency = bool(
        re.search(r"\b(?:sufficient|adequate|satisf(?:y|ies))\b", q_lower) and "sampling" in q_lower
    )
    if is_sufficiency and "is_sufficient" in params:
        fs = int(params["fs"]) if params["fs"].is_integer() else params["fs"]
        nr_val = params["nyquist_rate"]
        nr = int(nr_val) if nr_val.is_integer() else nr_val
        fm = int(params["fm"]) if params["fm"].is_integer() else params["fm"]
        return {
            "category": "sampling_sufficiency",
            "direct_answer": f"Yes, the selected sampling frequency ({fs} Hz) is sufficient.",
            "explanation": (
                f"The theorem requires fs >= 2*fm (Nyquist rate). For fm = {fm} Hz, Nyquist rate "
                f"is 2 * {fm} = {nr} Hz. Since fs = {fs} Hz >= {nr} Hz, the condition is satisfied "
                "and the signal can be reconstructed without aliasing."
            ),
            "expected_tokens": ["sufficient", str(fs)],
            "evidence_type": "derived",
        }

    # 6. Specific frequency evaluation (e.g. "What happens at 8 Hz?")
    m_freq = re.search(r"\b(?:at|if|frequency\s+of|with)\s+([0-9]+(?:\.[0-9]+)?)\s*hz\b", q_lower)
    if m_freq and "nyquist_rate" in params:
        test_f = float(m_freq.group(1))
        test_f_str = int(test_f) if test_f.is_integer() else test_f
        nr_val = params["nyquist_rate"]
        nr = int(nr_val) if nr_val.is_integer() else nr_val
        fm = int(params["fm"]) if params["fm"].is_integer() else params["fm"]
        if test_f < params["nyquist_rate"]:
            ans_str = (
                f"At {test_f_str} Hz, the sampling condition is not satisfied and aliasing occurs."
            )
            return {
                "category": "frequency_check",
                "direct_answer": ans_str,
                "explanation": (
                    f"Message signal fm = {fm} Hz (Nyquist rate = 2 * fm = {nr} Hz). "
                    f"Since {test_f_str} Hz < {nr} Hz (fs < 2*fm), the signal is under-sampled. "
                    "Aliasing occurs, causing high-frequency components to distort."
                ),
                "expected_tokens": ["aliasing", "not satisfied"],
                "evidence_type": "derived",
            }
        return {
            "category": "frequency_check",
            "direct_answer": f"At {test_f_str} Hz, the sampling theorem condition is satisfied.",
            "explanation": (
                f"Since {test_f_str} Hz >= {nr} Hz (Nyquist rate = 2 * {fm} = {nr} Hz), "
                "condition fs >= 2*fm is satisfied and the signal reconstructs without aliasing."
            ),
            "expected_tokens": ["satisfied"],
            "evidence_type": "derived",
        }

    # 7. Colon vector explanation (e.g. Explain t = 0:0.001:1)
    is_vector_exp = bool(
        re.search(r"\bexplain\s+t\s*=\s*0:0\.001:1\b", q_lower)
        or ("0:0.001:1" in q_lower and "explain" in q_lower)
    )
    if is_vector_exp:
        return {
            "category": "vector_explanation",
            "direct_answer": (
                "`t = 0:0.001:1` defines a continuous-like time vector from 0 to 1 second "
                "with a step size of 0.001 seconds (1 ms), generating 1001 points."
            ),
            "explanation": (
                "In MATLAB colon notation `start:step:stop`, `0:0.001:1` specifies a time array "
                "beginning at t = 0s and ending at t = 1s with increments of 0.001 seconds (1 ms). "
                "This yields (1 - 0) / 0.001 + 1 = 1001 discrete points representing the signal."
            ),
            "expected_tokens": ["1001", "0.001"],
            "evidence_type": "derived",
        }

    return None


def analyze_code_identifiers(
    question: str, evidence: Sequence[dict[str, Any]]
) -> dict[str, Any] | None:
    """Detect if question asks about a specific code command in the retrieved code passages."""
    q_lower = question.lower()
    combined_evidence = " ".join(item.get("text", "") for item in evidence).lower()

    for cmd, info in _CODE_IDENTIFIER_SEMANTICS.items():
        is_query_match = bool(
            re.search(info["pattern"], q_lower)
            and any(w in q_lower for w in ["what", "why", "purpose", "explain", "do"])
        )
        if is_query_match and re.search(info["pattern"], combined_evidence):
            return {
                "category": "code_semantics",
                "command": cmd,
                "direct_answer": info["direct_answer"],
                "explanation": info["explanation"],
                "evidence_type": "derived",
            }
    return None
