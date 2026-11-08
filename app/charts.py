"""Grafik batang horizontal untuk kategori berlabel panjang.

`st.bar_chart` memotong label sumbu yang panjang. Altair sudah terpasang sebagai dependensi Streamlit,
jadi grafik ini tidak menambah pustaka. Tema dan warnanya tetap mengikuti Streamlit.
"""

import altair as alt

RISK_COLORS = {"menaikkan skor": "#ff2b2b", "menurunkan skor": "#0068c9", "tidak mengubah skor": "#a3a8b8"}
STATUS_COLORS = {"Dropout": "#ff2b2b", "Enrolled": "#83c9ff", "Graduate": "#0068c9"}
STAGE_COLORS = {"T1": "#0068c9", "T2": "#83c9ff", "T3": "#ff2b2b"}


def bars(frame, label, value, color=None, grouped=False, colors=None):
    """Urutan baris dipertahankan. `grouped` menaruh tiap nilai `color` sebagai batang terpisah per label."""
    encoding = {
        "y": alt.Y(field=label, type="nominal", sort=None, title=None, axis=alt.Axis(labelLimit=0)),
        "x": alt.X(field=value, type="quantitative", title=value),
        "tooltip": [alt.Tooltip(field=label), alt.Tooltip(field=value, format=".3f")],
    }
    if color:
        present = {key: value for key, value in (colors or {}).items() if key in set(frame[color])}
        scale = alt.Scale(domain=list(present), range=list(present.values())) if colors else alt.Undefined
        encoding["color"] = alt.Color(
            field=color, type="nominal", sort=None, scale=scale, legend=alt.Legend(orient="bottom", title=None)
        )
        encoding["tooltip"].append(alt.Tooltip(field=color))
        if grouped:
            encoding["yOffset"] = alt.YOffset(field=color, type="nominal", sort=None)
    bands = frame[label].nunique() * (frame[color].nunique() if grouped else 1)
    # Tinggi Streamlit mencakup sumbu dan legenda, bukan hanya area batang.
    return alt.Chart(frame).mark_bar().encode(**encoding).properties(height=26 * bands + 70 + (50 if color else 0))
