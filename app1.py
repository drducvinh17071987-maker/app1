# streamlit_app.py
import re
from dataclasses import dataclass
from typing import List

import streamlit as st


# -----------------------------
# Parsing
# -----------------------------
def parse_series(text: str) -> List[float]:
    if not text or not text.strip():
        return []
    tokens = re.split(r"[,\s;]+", text.strip())
    vals: List[float] = []
    for t in tokens:
        if not t:
            continue
        try:
            vals.append(float(t))
        except ValueError:
            pass
    return vals


def fmt_one_line(vals: List[float]) -> str:
    return ", ".join(f"{v:g}" for v in vals)


# -----------------------------
# Segment metrics: %Δ and T
# -----------------------------
@dataclass
class SegmentMetrics:
    seg_idx: int
    pct_delta: float  # % change
    T: float


def compute_segments_pct_T(raw: List[float], denom: float = 80.0) -> List[SegmentMetrics]:
    """
    For each segment (i-1 -> i):
      pct_delta = 100*(raw[i]-raw[i-1]) / raw[i-1]
      T = pct_delta / denom
    """
    out: List[SegmentMetrics] = []
    if len(raw) < 2:
        return out

    for i in range(1, len(raw)):
        a = raw[i - 1]
        b = raw[i]
        pct = 0.0 if a == 0 else 100.0 * (b - a) / a
        T = pct / denom
        out.append(SegmentMetrics(seg_idx=i, pct_delta=pct, T=T))
    return out


def format_segments(out: List[SegmentMetrics]) -> str:
    lines = []
    for s in out:
        lines.append(f"Seg {s.seg_idx:02d}: %Δ={s.pct_delta:+.3f}% | T={s.T:+.6g}")
    return "\n".join(lines)


# -----------------------------
# Tab renderer
# -----------------------------
def render_tab(tab_key: str, default_vals: List[float]):
    col_left, col_right = st.columns(2, gap="large")

    raw_key = f"{tab_key}_raw_text"
    denom_key = f"{tab_key}_denom"
    segs_key = f"{tab_key}_segs"
    raw_vals_key = f"{tab_key}_raw_vals"

    default_text = fmt_one_line(default_vals)

    with col_left:
        st.markdown("### Input raw series (max 10 points)")
        raw_text = st.text_area(
            "Paste values (comma separated)",
            value=st.session_state.get(raw_key, default_text),
            height=110,
            key=raw_key,
        )

        raw_vals = parse_series(raw_text)
        if len(raw_vals) > 10:
            raw_vals = raw_vals[:10]
            st.warning("Only the first 10 values are used.")

        st.caption(f"Parsed: {len(raw_vals)} points")
        if raw_vals:
            st.code(fmt_one_line(raw_vals), language="text")

        denom = st.number_input(
            "Denominator for T = (%Δ)/denom",
            min_value=1.0,
            value=float(st.session_state.get(denom_key, 80.0)),
            step=1.0,
            key=denom_key,
        )

        if st.button("Compute %Δ and T (segment-based)", key=f"{tab_key}_compute_btn", use_container_width=True):
            if len(raw_vals) < 2:
                st.error("Please provide at least 2 points.")
            else:
                segs = compute_segments_pct_T(raw_vals, denom=denom)
                st.session_state[segs_key] = segs
                st.session_state[raw_vals_key] = raw_vals
                st.success("Computed %Δ and T.")

        st.markdown("### Segment outputs (copyable)")
        segs_show: List[SegmentMetrics] = st.session_state.get(segs_key, [])
        if segs_show:
            st.text_area(
                "Segments",
                value=format_segments(segs_show),
                height=240,
                key=f"{tab_key}_segments_text",
            )
        else:
            st.info("Click **Compute** to see %Δ and T outputs.")

    with col_right:
        st.markdown("### %Δ chart (segments)")
        segs_show: List[SegmentMetrics] = st.session_state.get(segs_key, [])
        if segs_show:
            pct = [s.pct_delta for s in segs_show]
            st.line_chart({"pct_delta(%)": pct})
        else:
            st.info("Compute first to show %Δ chart.")

        st.markdown("### T chart (segments)")
        if segs_show:
            Ts = [s.T for s in segs_show]
            st.line_chart({"T": Ts})
        else:
            st.info("Compute first to show T chart.")


# -----------------------------
# App
# -----------------------------
st.set_page_config(page_title="T vs %Δ – HRV & VO2", layout="wide")

st.title("T vs %Δ (Segment-based) – HRV & VO₂")
st.caption("This demo compares only %Δ and T (no raw charts). Each tab shows %Δ chart and T chart over segments.")

tab_hrv, tab_vo2 = st.tabs(["HRV", "VO₂"])

with tab_hrv:
    render_tab("hrv", default_vals=[25, 30, 35, 40, 45, 50])

with tab_vo2:
    render_tab("vo2", default_vals=[12, 15, 18, 22, 28, 35, 40, 38, 30, 22])
