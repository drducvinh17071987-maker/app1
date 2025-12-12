# streamlit_app.py
import re
from dataclasses import dataclass
from typing import List

import streamlit as st


# -----------------------------
# Parsing
# -----------------------------
def parse_series(text: str) -> List[float]:
    """
    Parse numbers from text. Accepts comma/space/newline/semicolon.
    """
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
    """Format raw series as one line: v1, v2, v3"""
    return ", ".join(f"{v:g}" for v in vals)


# -----------------------------
# T Segment Logic (only T)
# -----------------------------
@dataclass
class TSegment:
    seg_idx: int
    raw_from: float
    raw_to: float
    pct_delta: float
    T: float


def compute_T_segments(raw: List[float], denom: float = 80.0) -> List[TSegment]:
    """
    Segment-based T:
      pct_delta = 100 * (raw[i] - raw[i-1]) / raw[i-1]
      T = pct_delta / denom
    Output length = n-1 segments.
    """
    segs: List[TSegment] = []
    if len(raw) < 2:
        return segs

    for i in range(1, len(raw)):
        a = raw[i - 1]
        b = raw[i]
        pct = 0.0 if a == 0 else 100.0 * (b - a) / a
        T = pct / denom
        segs.append(TSegment(i, a, b, pct, T))

    return segs


def format_T_segments(segs: List[TSegment]) -> str:
    lines = []
    for s in segs:
        lines.append(
            f"Seg {s.seg_idx:02d}: {s.raw_from:.6g} → {s.raw_to:.6g} | "
            f"%Δ={s.pct_delta:+.3f}% | T={s.T:+.6g}"
        )
    return "\n".join(lines)


# -----------------------------
# Tab renderer
# -----------------------------
def render_tab(tab_key: str, label: str, default_vals: List[float]):
    col_left, col_right = st.columns(2, gap="large")

    raw_key = f"{tab_key}_raw_text"
    denom_key = f"{tab_key}_denom"
    raw_vals_key = f"{tab_key}_raw_vals"
    segs_key = f"{tab_key}_Tsegs"

    # Default raw in ONE LINE comma-separated
    default_text = fmt_one_line(default_vals)

    with col_left:
        st.markdown("### Raw series (points)")
        raw_text = st.text_area(
            "Paste values (comma separated, one line preferred)",
            value=st.session_state.get(raw_key, default_text),
            height=110,
            key=raw_key,
        )

        raw_vals = parse_series(raw_text)

        # Echo back as one-line comma separated (so it always looks clean)
        if raw_vals:
            st.caption(f"Parsed: {len(raw_vals)} points")
            st.code(fmt_one_line(raw_vals), language="text")
        else:
            st.caption("Parsed: 0 points")

        denom = st.number_input(
            "Denominator for T = (%Δraw)/denom",
            min_value=1.0,
            value=float(st.session_state.get(denom_key, 80.0)),
            step=1.0,
            key=denom_key,
        )

        if st.button("Compute T (segment-based)", key=f"{tab_key}_compute_btn", use_container_width=True):
            if len(raw_vals) < 2:
                st.error("Please provide at least 2 points.")
            else:
                segs = compute_T_segments(raw_vals, denom=denom)
                st.session_state[raw_vals_key] = raw_vals
                st.session_state[segs_key] = segs
                st.success("T segments computed.")

        st.markdown("### T per segment (copyable)")
        segs_show: List[TSegment] = st.session_state.get(segs_key, [])
        if segs_show:
            st.text_area(
                "Segments",
                value=format_T_segments(segs_show),
                height=260,
                key=f"{tab_key}_Tsegs_text_out",
            )
        else:
            st.info("Click **Compute T** to see T segments here.")

    with col_right:
        st.markdown("### Raw chart (points)")
        raw_vals_show: List[float] = st.session_state.get(raw_vals_key, raw_vals)
        if raw_vals_show:
            st.line_chart({"raw": raw_vals_show})
        else:
            st.info("No raw data to plot yet.")

        st.markdown("### T chart (segments)")
        segs_show: List[TSegment] = st.session_state.get(segs_key, [])
        if segs_show:
            Ts = [s.T for s in segs_show]
            st.line_chart({"T": Ts})
        else:
            st.info("Compute T first to show T chart.")


# -----------------------------
# App
# -----------------------------
st.set_page_config(page_title="ET Demo – HRV & VO2 (T-only)", layout="wide")

st.title("ET Demo – HRV & VO₂ (2 Tabs, Segment-based T only)")
st.caption("Each tab: left = raw → compute → T segments list; right = raw chart + T chart (no E).")

tab_hrv, tab_vo2 = st.tabs(["HRV", "VO₂"])

with tab_hrv:
    st.subheader("HRV")
    render_tab("hrv", "HRV", default_vals=[25, 30, 35, 40, 45, 50])

with tab_vo2:
    st.subheader("VO₂")
    render_tab("vo2", "VO₂", default_vals=[12, 15, 18, 22, 28, 35, 40, 38, 30, 22, 16])
