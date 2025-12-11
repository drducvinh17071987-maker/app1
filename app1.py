import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# App metadata
# ---------------------------------------------------------
APP_NAME = "App 1 – HRV Raw (3 Profiles)"
APP_VERSION = "1.0.0"

st.set_page_config(
    page_title=APP_NAME,
    layout="wide"
)

st.title(APP_NAME)
st.caption(f"Version: {APP_VERSION}")

st.write(
    "Enter HRV values (in ms) separated by commas. "
    "Each profile represents one person (A: high HRV, B: medium, C: low)."
)

# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def parse_hrv_input(text: str):
    """
    Parse an HRV string like '80, 75, 70,...' into a list[float].
    - Strips whitespace
    - Ignores empty items
    - Raises ValueError if a value is not numeric
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
    Bundle 3 HRV lists into a dict for DataFrame.
    Only include series that have data.
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

# ---------------------------------------------------------
# LEFT COLUMN: input + button
# ---------------------------------------------------------

with col_input:
    st.subheader("Input HRV data")

    default_a = "80, 78, 76, 75, 77, 79, 80, 78, 76, 77"
    default_b = "60, 58, 56, 55, 57, 59, 60, 58, 56, 57"
    default_c = "40, 38, 36, 35, 37, 39, 40, 38, 36, 37"

    hrv_a_text = st.text_area(
        "Profile A – high HRV (e.g. athlete / very healthy person):",
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
        "Profile C – low HRV (e.g. stress, chronic condition):",
        value=default_c,
        height=80,
        help="Example: 40, 38, 36, 35, 37, 39..."
    )

    st.caption("Note: values must be separated by **commas**, no need to break lines.")

    calc_button = st.button("Compute & Plot HRV Raw")

# ---------------------------------------------------------
# RIGHT COLUMN: table + chart
# ---------------------------------------------------------

with col_plot:
    st.subheader("HRV Raw plot (3 profiles overlaid)")

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

                st.write("### HRV raw table (ms)")
                st.dataframe(df)

                st.write("### HRV raw line chart (ms)")
                st.line_chart(df)

                st.markdown(
                    """
                    **Quick interpretation:**
                    - Profile A (high HRV) typically stays in the upper zone.
                    - Profile B (medium HRV) stays in the mid zone.
                    - Profile C (low HRV) stays in the lower zone.
                    - Even if the *pattern* of change is similar, different baselines make the three curves separate widely.  
                      → It is very hard to compare physiological state between A/B/C using raw HRV only.
                    """
                )

        except ValueError as e:
            st.error(str(e))
    else:
        st.info(
            "Enter HRV values for 1–3 profiles in the left column, "
            "then click **“Compute & Plot HRV Raw”** to see the result."
        )
