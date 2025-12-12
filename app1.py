# streamlit_app.py
import re
from dataclasses import dataclass
from typing import List, Tuple

import streamlit as st
import matplotlib.pyplot as plt


# -----------------------------
# Parsing
# -----------------------------
def parse_series(text: str) -> List[float]:
    """
    Parse numbers from a text area.
    Accepts: comma, space, newline, semicolon separated.
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


# -----------------------------
# ET Segment Logic (T, E) - embedded formula
# -----------------------------
@dataclass
class ETSegment:
    seg_idx: int         # 1..n-1
    raw_from: float
    raw_to: float
    pct_delta: float     # % change from raw_from to raw_to
    T: float
    E: float


def compute_et_segments(raw: List[float], denom: float = 80.0) -> List[ETSegment]:
    """
    Segment-based ET:
      pct_delta[i] = 100 * (raw[i] - raw[i-1]) / raw[i-1]
      T = pct_delta / denom
      E = 1 - T^2
    Output length = n-1 segments.
    """
    segs: List[ETSegment] = []
    if len(raw) < 2:
        return segs

    for i in range(1, len(raw)):
        a = raw[i - 1]
        b = raw[i]

        # Guard against divide-by-zero
        if a == 0:
            pct = 0.0
        else:
            pct = 100.0 * (b - a) / a

        T = pct / denom
        E = 1.0 - (T * T)

        segs.append(
            ETSegment(
                seg_idx=i,
                raw_from=a,
                raw_to=b,
                pct_delta=pct,
                T=T,
                E=E,
            )
        )
    return segs


def format_segments(segs: List[ETSegment]) -> str:
    lines = []
    for s in segs:
        lines.append(
            f"Seg {s.seg_idx:02d}: {s.raw_from:.6g} → {s.raw_to:.6g} | "
            f"%Δ={s.pct_delta:+.3f}% | T={s.T:+.6g} | E={s.E:.6g}"
        )
    return "\n".join(lines)


# -----------------------------
# Plotting
# -----------------------------
def plot_points(values: List[float], title: str, y_label: str):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(list(range(1, len(values) + 1)), values, marker="o")
    ax.set_title(title)
    ax.set_xlabel("Point index")
    ax.set_ylabel(y_label)
    ax.grid(True)
    st.pyplot(fig, clear_figure=True)


def plot_segments(segs: List[ETSegment], title: str, y_label: str, which: str = "E"):
    fig = plt.figure()
    ax = fig.add_subplot(111)

    x = [s.seg_idx for s in segs]  # 1..n-1
    if which == "T":
        y = [s.T for s in segs]
    elif which == "pct":
        y = [s.pct_delta for s in segs]
    else:
        y = [s.E for s in segs]

    ax.plot(x, y, marker="o")
    ax.set_title(title)
    ax.set_xlabel("Segment index (i-1 → i)")
    ax.set_ylabel(y_label)
    ax.grid(True)
    st.pyplot(fig, clear_figure=True)


# -----------------------------
# Tab renderer
# -----------------------------
def render_tab(tab_key: str, label: str, default_text: str):
    st.subheader(label)

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
            help="Default 80. You can keep 80 for both tabs unless you intentionally want a different scaling.",
        )

        btn = st.button("Compute ET (segment-based)", key=f"{tab_key}_compute_btn", use_container_width=True)

        if btn:
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
                height=260,
                key=f"{tab_key}_segs_text_out",
            )
        else:
            st.info("Click **Compute ET (segment-based)** to see ET segments here.")

    with col_right:
        st.markdown("### Raw chart (points)")
        raw_vals_show: List[float] = st.session_state.get(raw_vals_key, raw_vals)
        if raw_vals_show:
            plot_points(raw_vals_show, title=f"{label} – Raw (points)", y_label="Raw")
        else:
            st.info("No raw data to plot yet.")

        st.markdown("### ET chart (segments)")
        segs_show: List[ETSegment] = st.session_state.get(segs_key, [])
        if segs_show:
            # Plot E by default. If you want, you can change to T or %Δ
            plot_segments(segs_show, title=f"{label} – ET (E over segments)", y_label="E", which="E")
        else:
            st.info("No ET segments to plot yet.")


# -----------------------------
# App
# -----------------------------
st.set_page_config(page_title="ET Demo – HRV & VO2 (Segment-based)", layout="wide")

st.title("ET Demo – HRV & VO₂ (2 Tabs, Segment-based ET)")
st.caption("Each tab: left = raw → compute → ET segments list; right = raw chart + ET chart (E over segments).")

tab_hrv, tab_vo2 = st.tabs(["HRV", "VO₂"])

with tab_hrv:
    render_tab(
        tab_key="hrv",
        label="HRV",
        default_text="20\n18\n16\n15\n14\n13\n14\n15\n16\n18\n20",
    )

with tab_vo2:
    render_tab(
        tab_key="vo2",
        label="VO₂",
        default_text="12\n15\n18\n22\n28\n35\n40\n38\n30\n22\n16",
    )
