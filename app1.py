# streamlit_app.py
import re
from dataclasses import dataclass
from typing import List

import streamlit as st


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


@dataclass
class ETSegment:
    seg_idx: int
    raw_from: float
    raw_to: float
    pct_delta: float
    T: float
    E: float


def compute_et_segments(raw: List[float], denom: float = 80.0) -> List[ETSegment]:
    segs: List[ETSegment] = []
    if len(raw) < 2:
        return segs

    for i in range(1, len(raw)):
        a = raw[i - 1]
        b = raw[i]

        pct = 0.0 if a == 0 else 100.0 * (b - a) / a
        T = pct / denom
        E = 1.0 - (T * T)

        segs.append(ETSegment(i, a, b, pct, T, E))
    return segs


def format_segments(segs: List[ETSegment]) -> str:
    lines = []
    for s in segs:
        lines.append(
            f"Seg {s.seg_idx:02d}: {s.raw_from:.6g} → {s.raw_to:.6g} | "
            f"%Δ={s.pct_delta:+.3f}% | T={s.T:+.6g} | E={s.E:.6g}"
        )
    return "\n".join(lines)


def render_tab(tab_key: str, label: str, default_text: str):
    col_left, col_right = st.columns(2, gap="large")

    raw_key = f"{tab_key}_raw_text"
    denom_key = f"{tab_key}_denom"
    raw_vals_key = f"{tab_key}_raw_vals"
    segs_key = f"{tab_key}_segs"

    with col_left:
        st.markdown("### Raw series (points)")
        raw_text = st.text_area(
            "Paste values (comma/space/newline separated)",
            value=st.session_state.get(raw_key, default_text),
            height=180,
            key=raw_key,
        )
        raw_vals = parse_series(raw_text)
        st.caption(f"Parsed: {len(raw_vals)} points")

        denom = st.number_input(
            "Denominator for T = (%Δraw)/denom",
            min_value=1.0,
            value=float(st.session_state.get(denom_key, 80.0)),
            step=1.0,
            key=denom_key,
        )

        if st.button("Compute ET (segment-based)", key=f"{tab_key}_compute_btn", use_container_width=True):
            if len(raw_vals) < 2:
                st.error("Please provide at least 2 points.")
            else:
                segs = compute_et_segments(raw_vals, denom=denom)
                st.session_state[raw_vals_key] = raw_vals
                st.session_state[segs_key] = segs
                st.success("ET segments computed.")

        st.markdown("### ET per segment (copyable)")
        segs_show: List[ETSegment] = st.session_state.get(segs_key, [])
        if segs_show:
            st.text_area(
                "Segments",
                value=format_segments(segs_show),
                height=280,
                key=f"{tab_key}_segs_text_out",
            )
        else:
            st.info("Click **Compute ET** to see ET segments here.")

    with col_right:
        st.markdown("### Raw chart (points)")
        raw_vals_show: List[float] = st.session_state.get(raw_vals_key, raw_vals)
        if raw_vals_show:
            # No matplotlib: use Streamlit built-in chart
            st.line_chart({"raw": raw_vals_show})
        else:
            st.info("No raw data to plot yet.")


st.set_page_config(page_title="ET Demo – HRV & VO2", layout="wide")
st.title("ET Demo – HRV & VO₂ (2 Tabs, Segment-based ET)")
st.caption("Each tab: left = raw → compute → ET segments list; right = raw chart only (no ET chart).")

tab_hrv, tab_vo2 = st.tabs(["HRV", "VO₂"])

with tab_hrv:
    st.subheader("HRV")
    render_tab("hrv", "HRV", "20\n18\n16\n15\n14\n13\n14\n15\n16\n18\n20")

with tab_vo2:
    st.subheader("VO₂")
    render_tab("vo2", "VO₂", "12\n15\n18\n22\n28\n35\n40\n38\n30\n22\n16")
