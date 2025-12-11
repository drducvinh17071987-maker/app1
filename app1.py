import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# App metadata
# ---------------------------------------------------------
APP_NAME = "App 1 – HRV Raw Profiles (3 Individuals)"
APP_VERSION = "1.1.0"

st.set_page_config(
    page_title=APP_NAME,
    layout="wide"
)

st.title(APP_NAME)
st.caption(f"Version: {APP_VERSION}")

st.write(
    "This app visualizes raw HRV values (in ms) for up to three individuals "
    "with different baselines (A: high HRV, B: medium HRV, C: low HRV). "
    "Values are entered as comma-separated lists."
)

# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def parse_hrv_input(text: str):
    """
    Parse an HRV string like '80, 75, 70' into a list[float].
    - Strips whitespace
    - Ignores empty items
    - Raises ValueError if something is not numeric
    """
    if not text:
        return []
    items = [x.strip() for x in text.split(",")]
    values = []
    for x in items:
        if x == "":
            continue
        try:
            values.append(float(x))
        except ValueError:
            raise ValueError(f"Invalid value: '{x}' (not a number).")
    return values


def make_series_dict(a, b, c):
    """
    Bundle 3 HRV lists into a dict for plotting.
    Only include series that actually have data.
    """
    data = {}
    if a:
        data["A (high HRV)"] = a
    if b:
        data["B (medium HRV)"] = b
    if c:
        data["C (low HRV)"] = c
    return data


# ---------------------------------------------------------
# Layout: 2 columns
# ---------------------------------------------------------

col_input, col_plot = st.columns([1, 2])

# ---------------- LEFT COLUMN: INPUT + BUTTON ----------------

with col_input:
    st.subheader("Input HRV values")

    default_a = "80, 78, 76, 75, 77, 79, 80, 78, 76, 77"
    default_b = "60, 58, 56, 55, 57, 59, 60, 58, 56, 57"
    default_c = "40, 38, 36, 35, 37, 39, 40, 38, 36, 37"

    hrv_a_text = st.text_area(
        "Profile A – high HRV (e.g. athlete / very healthy):",
        value=default_a,
        height=80,
        help="Example: 80, 78, 76, 75, 77, 79..."
    )

    hrv_b_text = st.text_area(
        "Profile B – medium HRV:",
        value=default_b,
        height=80,
        help="Example: 60, 58, 56, 55, 57, 59..."
    )

    hrv_c_text = st.text_area(
        "Profile C – low HRV (e.g. stress / chronic condition):",
        value=default_c,
        height=80,
        help="Example: 40, 38, 36, 35, 37, 39..."
    )

    st.caption("Note: values must be separated by **commas**. No need to add new lines.")

    calc_button = st.button("Compute & plot raw HRV")


# ---------------- RIGHT COLUMN: LINE CHART ----------------

with col_plot:
    st.subheader("HRV raw line chart (three profiles overlaid)")

    if calc_button:
        try:
            hrv_a = parse_hrv_input(hrv_a_text)
            hrv_b = parse_hrv_input(hrv_b_text)
            hrv_c = parse_hrv_input(hrv_c_text)

            if not (hrv_a or hrv_b or hrv_c):
                st.warning("No HRV data found. Please enter at least one profile.")
            else:
                data_dict = make_series_dict(hrv_a, hrv_b, hrv_c)
                df = pd.DataFrame(data_dict)
                df.index = range(1, len(df) + 1)
                df.index.name = "Measurement step"

                # Only chart – no table
                st.line_chart(df, height=360)

                st.markdown(
                    """
                    **Quick interpretation:**
                    - Profile A (high HRV) stays in the upper zone.
                    - Profile B (medium HRV) stays in the middle zone.
                    - Profile C (low HRV) stays in the lower zone.
                    - Even if all three people follow a similar *pattern* of change, 
                      different baselines make the curves separate widely.  
                      → This illustrates why raw HRV alone cannot be used to fairly 
                      compare physiological state between individuals A, B and C.
                    """
                )

        except ValueError as e:
            st.error(str(e))
    else:
        st.info(
            "Paste comma-separated HRV values for 1–3 profiles in the left column, "
            "then click **“Compute & plot raw HRV”** to see the chart here."
        )
