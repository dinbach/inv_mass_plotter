import math
import os
import numpy as np
import streamlit as st
import pandas as pd
import altair as alt

try:
    from scipy.optimize import curve_fit
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# ── Constants ─────────────────────────────────────────────────────────────────
data_dir = "uploads"
# 4-lepton event labels: the row itself is KEPT (it carries the 4-lepton
# invariant mass), but the 2 rows that follow it are SKIPPED because they
# hold the individual lepton-pair masses and should not appear in the histogram.
skip_labels = {'4ee', '4me', '4em', '4mm'}

# Raw label → human-readable display name
display_map = {
    'e':    'ee',
    'm':    'μμ',
    'g':    'γγ',
    '4e':   '4e',    # some HYPATIA versions use short form
    '4ee':  '4e',    # others use long form
    '4m':   '4μ',
    '4mm':  '4μ',
    '2e2m': '2e2μ',
    '4me':  '2e2μ',  # 2μ + 2e mixed final state
    '4em':  '2e2μ',  # same topology, different lepton ordering label
}

# Canonical display-name order for the sidebar filter (stable across uploads)
DISPLAY_ORDER = ['ee', 'μμ', 'γγ', '4e', '4μ', '2e2μ']
bin_options = [5, 10, 20, 50, 70, 100, 200, 400, 500]
DELETE_PASSWORD = "hypatia2025"   # change this to your preferred password

# Fixed colours for every possible display-name so the stacked comparison chart
# keeps the same colour per channel regardless of which channels are selected.
CHANNEL_COLORS = {
    'ee':   '#aec7e8',   # light blue
    'μμ':   '#ff9896',   # light red / pink
    'γγ':   '#ff7f0e',   # orange
    '4e':   '#1f77b4',   # blue
    '4μ':   '#d62728',   # red
    '2e2μ': '#2ca02c',   # green
}
# col2: selectbox(~68) + 2×checkbox(~60) + 6-row table(~245) ≈ 373 px
# col1: CHART_HEIGHT + range-inputs(~68) → 300 + 68 ≈ 368 px
CHART_HEIGHT = 300

os.makedirs(data_dir, exist_ok=True)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Invariant Mass Event Plotter", page_icon="⚛️", layout="wide")
st.title("Ιστογράμματα Αναλλοίωτης Μάζας")
st.markdown(
    "Οπτικοποίηση δεδομένων αναλλοίωτης μάζας από το πρόγραμμα **HYPATIA**. "
    "Ανεβάστε αρχεία `.txt` από την πλευρική μπάρα για να ξεκινήσετε."
)

# ── Sidebar: Αρχεία Δεδομένων ─────────────────────────────────────────────────
st.sidebar.header("Αρχεία Δεδομένων")

def save_upload(uploaded_file):
    path = os.path.join(data_dir, uploaded_file.name)
    with open(path, 'wb') as f:
        f.write(uploaded_file.getbuffer())

if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0
if 'delete_pending' not in st.session_state:
    st.session_state.delete_pending = False

uploaded_files = st.sidebar.file_uploader(
    "Ανεβάστε ένα ή περισσότερα αρχεία (.txt)",
    type=['txt'],
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}"
)
if uploaded_files:
    for uf in uploaded_files:
        save_upload(uf)
        st.sidebar.success(f"Αποθηκεύτηκε: {uf.name}")

existing_files = [f for f in os.listdir(data_dir) if f.lower().endswith('.txt')]
if existing_files:
    if not st.session_state.delete_pending:
        # Normal state: show the delete button
        if st.sidebar.button("Διαγραφή όλων των αρχείων", type="secondary"):
            st.session_state.delete_pending = True
            st.rerun()
    else:
        # Password-confirmation dialog
        st.sidebar.warning("⚠️ Θα διαγραφούν όλα τα αρχεία!")
        pwd = st.sidebar.text_input("🔑 Κωδικός:", type="password", key="delete_pwd")
        if st.sidebar.button("✓ Επιβεβαίωση διαγραφής", type="primary", key="confirm_del"):
            if pwd == DELETE_PASSWORD:
                for f in existing_files:
                    os.remove(os.path.join(data_dir, f))
                st.session_state.delete_pending = False
                st.session_state.uploader_key += 1
                # clear the stored password from state
                st.session_state.pop("delete_pwd", None)
                st.rerun()
            else:
                st.sidebar.error("Λάθος κωδικός. Δοκιμάστε ξανά.")
        if st.sidebar.button("✗ Ακύρωση", key="cancel_del"):
            st.session_state.delete_pending = False
            st.session_state.pop("delete_pwd", None)
            st.rerun()

# ── Load datasets ─────────────────────────────────────────────────────────────
def load_datasets():
    datasets = {}
    for fname in sorted(os.listdir(data_dir)):
        if not fname.lower().endswith('.txt'):
            continue
        path = os.path.join(data_dir, fname)
        try:
            df = pd.read_csv(path, sep=r"\s+", header=None, names=['mass', 'event'])
            if df.empty:
                st.sidebar.warning(f"{fname}: κενό αρχείο.")
                continue
            df['mass'] = pd.to_numeric(df['mass'], errors='coerce')
            df = df.dropna(subset=['mass']).reset_index(drop=True)
            mask = pd.Series(False, index=df.index)
            for pos, lbl in enumerate(df['event']):
                if lbl in skip_labels:
                    for offset in [1, 2]:
                        if pos + offset < len(df):
                            mask.iloc[pos + offset] = True
            datasets[fname] = df.loc[~mask].reset_index(drop=True)
        except Exception as e:
            st.sidebar.warning(f"Αδυναμία φόρτωσης {fname}: {e}")
    return datasets

datasets = load_datasets()
if not datasets:
    st.info("Παρακαλώ ανεβάστε ένα ή περισσότερα αρχεία .txt από το πρόγραμμα HYPATIA για οπτικοποίηση της αναλλοίωτης μάζας.")
    st.stop()

# ── Sidebar: Φίλτρα ───────────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.header("Φίλτρα")

n_files = len(datasets)
n_events_total = sum(len(df) for df in datasets.values())
st.sidebar.caption(f"{n_files} αρχεί{'ο' if n_files == 1 else 'α'} · {n_events_total:,} γεγονότα φορτώθηκαν")

# Collect every raw event label that actually appears in the loaded data.
_all_raw = {e for df in datasets.values() for e in df['event'].unique()}

# Translate to display names and deduplicate while preserving canonical order.
# Multiple raw labels can share the same display name (e.g. '4ee' and '4e'
# both show as '4e'); the multiselect operates on display names so the user
# sees a clean, non-redundant list.
_present_displays = {display_map.get(e, e) for e in _all_raw}
display_options   = [d for d in DISPLAY_ORDER if d in _present_displays] + \
                    sorted(_present_displays - set(DISPLAY_ORDER))

selected_displays = st.sidebar.multiselect(
    "Επιλογή τύπου τελικής κατάστασης",
    options=display_options,
    default=display_options,
)

# Map selected display names back to raw labels for all downstream filtering.
selected_events = [raw for raw in _all_raw
                   if display_map.get(raw, raw) in selected_displays]

all_masses = pd.concat(
    [df[df['event'].isin(selected_events)]['mass'] for df in datasets.values()],
    ignore_index=True
)
if all_masses.empty:
    st.warning("Δεν υπάρχουν γεγονότα για τα επιλεγμένα είδη τελικής κατάστασης. Επιλέξτε τουλάχιστον έναν τύπο.")
    st.stop()

min_mass     = int(math.floor(all_masses.min()))
max_mass     = int(math.ceil(all_masses.max()))   # ceil so the max value itself is never excluded
default_xmax = min(max_mass, 2000)

# ── Initialise & clamp per-plot range keys ────────────────────────────────────
# Two-step process, both steps run BEFORE any widget is instantiated so that
# Streamlit's "cannot modify after instantiation" rule is never triggered.
#
# Step 1 – Seed defaults for keys that don't exist yet.
#   Streamlit uses number_input's `value=` arg only when the key is ABSENT from
#   session_state; if the key exists (even from a prior run with a stale value)
#   `value=` is silently ignored.  Writing here guarantees a fresh session always
#   starts at (0, min(max_mass, 2000)) regardless of what was stored before.
_init_defaults = (
    [("xmin_summed", 0), ("xmax_summed", default_xmax),
     ("ov_xmin",     0), ("ov_xmax",     default_xmax)] +
    [(f"xmin_{n}", 0)           for n in datasets] +
    [(f"xmax_{n}", default_xmax) for n in datasets]
)
for _k, _v in _init_defaults:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Step 2 – Delete keys whose stored value now exceeds max_mass.
#   This happens when the user removes event types and max_mass shrinks; the
#   stored value would crash number_input(max_value=max_mass).  Deletion (not
#   re-assignment) is used because the value parameter in the subsequent widget
#   call will then re-seed the key at the correct clamped value.
_range_keys = (
    ["xmin_summed", "xmax_summed", "ov_xmin", "ov_xmax"] +
    [k for name in datasets for k in (f"xmin_{name}", f"xmax_{name}")]
)
for _k in _range_keys:
    if _k in st.session_state:
        try:
            if int(st.session_state[_k]) > max_mass:
                del st.session_state[_k]
        except (ValueError, TypeError):
            del st.session_state[_k]

# ── Helper functions ──────────────────────────────────────────────────────────
def gaussian(x, amplitude, mean, sigma):
    return amplitude * np.exp(-0.5 * ((x - mean) / sigma) ** 2)


def stats_table(series, x_min, x_max, fit_mean=None, fit_sigma=None):
    filtered = series[(series >= x_min) & (series <= x_max)]
    empty = filtered.empty
    rows = [
        ('Εύρος ανάλυσης',    f"{x_min} – {x_max} GeV"),
        ('Αριθμός Γεγονότων', '0' if empty else int(filtered.count())),
        ('Μέσος όρος',        '—' if empty else f"{filtered.mean():.2f} GeV"),
        ('Τυπική απόκλιση',   '—' if empty else f"{filtered.std():.2f} GeV"),
        ('Ελάχιστο',          '—' if empty else f"{filtered.min():.1f} GeV"),
        ('Μέγιστο',           '—' if empty else f"{filtered.max():.1f} GeV"),
    ]
    if fit_mean is not None:
        rows += [
            ('Προσ. μέση τιμή',  f"{fit_mean:.2f} GeV"),
            ('Προσ. σ (πλάτος)', f"{abs(fit_sigma):.2f} GeV"),
        ]
    return pd.DataFrame(rows, columns=['Στατιστικό', 'Τιμή'])


def build_chart(sel, bins_n, color, show_counts, show_fit, x_min, x_max):
    """Histogram using Altair's native bin+count() — guaranteed to render bars.

    Gaussian fit and count labels are overlaid as separate layers using numpy
    bins (same step, so bin centers align with the bars).
    resolve_scale(y='shared') ensures all layers share one Y axis.
    """
    data = sel[(sel >= x_min) & (sel <= x_max)]
    bin_width   = (x_max - x_min) / bins_n
    width_label = str(int(bin_width)) if bin_width == int(bin_width) else f"{bin_width:.1f}"
    # Use same step in Altair and numpy so bin edges are identical
    abin = alt.Bin(step=bin_width, extent=[x_min, x_max])

    # Numpy histogram (needed for labels & fit; bins match Altair's)
    if not data.empty:
        counts, bin_edges = np.histogram(data, bins=bins_n, range=(x_min, x_max))
    else:
        counts    = np.zeros(bins_n, dtype=int)
        bin_edges = np.linspace(x_min, x_max, bins_n + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # ── Bar chart via Altair's count() – this is the approach that reliably renders
    bars = alt.Chart(pd.DataFrame({'mass': data})).mark_bar(
        opacity=0.7, color=color
    ).encode(
        alt.X('mass:Q', bin=abin, title='Αναλλοίωτη Μάζα (GeV)',
              axis=alt.Axis(grid=True, ticks=True)),
        alt.Y('count()', title=f'Γεγονότα/{width_label} GeV',
              axis=alt.Axis(grid=True)),
        tooltip=[
            alt.Tooltip('mass:Q', bin=abin, title='Εύρος Μάζας', format='.1f'),
            alt.Tooltip('count()', title='Γεγονότα'),
        ]
    )

    extra_layers = []   # layers that use count:Q (shared scale with bars)
    fit_mean = fit_sigma = None

    if show_counts and not data.empty:
        # Use 'mass' as the X field so this layer shares the same X scale as
        # the bar layer (which also uses mass:Q). A different field name would
        # force Altair to merge two independent X scales, distorting the axis.
        hist_df = pd.DataFrame({'mass': bin_centers, 'count': counts})
        labels  = alt.Chart(hist_df[hist_df['count'] > 0]).mark_text(
            dy=-7, fontSize=10
        ).encode(
            x=alt.X('mass:Q'),
            y=alt.Y('count:Q'),
            text=alt.Text('count:Q'),
        )
        extra_layers.append(labels)

    if show_fit and SCIPY_AVAILABLE and not data.empty and len(data) >= 5:
        nonzero = counts > 0
        if nonzero.sum() >= 3:
            try:
                p0 = [float(counts.max()), float(data.mean()),
                      max(float(data.std()), 0.1)]
                popt, _ = curve_fit(
                    gaussian, bin_centers[nonzero], counts[nonzero].astype(float),
                    p0=p0, maxfev=5000
                )
                fit_mean  = float(popt[1])
                fit_sigma = float(popt[2])
                x_fit = np.linspace(x_min, x_max, 500)
                y_fit = gaussian(x_fit, *popt)
                fit_color = '#d62728' if color != '#d62728' else '#ff7f0e'
                # Both X and Y field names match the bar layer ('mass', 'count')
                # so all three layers resolve to the same axes without distortion.
                fit_curve = alt.Chart(
                    pd.DataFrame({'mass': x_fit, 'count': y_fit})
                ).mark_line(color=fit_color, strokeWidth=2.5).encode(
                    x=alt.X('mass:Q'),
                    y=alt.Y('count:Q'),
                )
                extra_layers.append(fit_curve)
            except Exception:
                pass

    if extra_layers:
        chart = alt.layer(bars, *extra_layers).resolve_scale(y='shared')
    else:
        chart = bars

    return chart.interactive(), fit_mean, fit_sigma


def _read_range(xmin_key, xmax_key):
    """Read per-plot range from session state (keys were pre-clamped above).
    Pure read — never writes to session_state, so safe to call at any point."""
    xmin = max(0, min(int(st.session_state.get(xmin_key, 0)), max_mass))
    xmax = max(0, min(int(st.session_state.get(xmax_key, default_xmax)), max_mass))
    if xmin >= xmax:
        xmin, xmax = 0, min(default_xmax, max_mass)
    return xmin, xmax


def make_histogram_section(sel, bins_key, count_key, fit_key,
                            xmin_key, xmax_key, color):
    """Render histogram block.  Range inputs live below the chart in col1."""
    plot_xmin, plot_xmax = _read_range(xmin_key, xmax_key)

    col1, col2 = st.columns([3, 1])

    with col2:
        bins_n      = st.selectbox("Αριθμός Bin", options=bin_options,
                                   index=bin_options.index(100), key=bins_key)
        show_counts = st.checkbox("Εμφάνιση counts", key=count_key)
        show_fit    = (st.checkbox("Γκαουσιανή προσαρμογή", key=fit_key)
                       if SCIPY_AVAILABLE else False)
        stats_slot  = st.empty()   # filled after build_chart returns fit results

    with col1:
        if sel[(sel >= plot_xmin) & (sel <= plot_xmax)].empty:
            st.info("Δεν υπάρχουν δεδομένα στο επιλεγμένο εύρος.")
        chart, fit_mean, fit_sigma = build_chart(
            sel, bins_n, color, show_counts, show_fit, plot_xmin, plot_xmax
        )
        st.altair_chart(chart.properties(height=CHART_HEIGHT), use_container_width=True)
        # Range inputs directly below the x-axis
        rc1, rc2 = st.columns(2)
        with rc1:
            st.number_input("X min (GeV)", min_value=0, max_value=max_mass,
                            value=plot_xmin, key=xmin_key)
        with rc2:
            st.number_input("X max (GeV)", min_value=0, max_value=max_mass,
                            value=plot_xmax, key=xmax_key)

    stats_slot.dataframe(
        stats_table(sel, plot_xmin, plot_xmax,
                    fit_mean if show_fit else None,
                    fit_sigma if show_fit else None),
        hide_index=True, use_container_width=True
    )


# ── Individual histograms ─────────────────────────────────────────────────────
for name, df in datasets.items():
    display_name = os.path.splitext(name)[0]
    st.subheader(f"Ιστόγραμμα — {display_name}")
    sel = df[df['event'].isin(selected_events)]['mass']
    make_histogram_section(sel,
                           bins_key=f"bins_{name}",
                           count_key=f"count_{name}",
                           fit_key=f"fit_{name}",
                           xmin_key=f"xmin_{name}",
                           xmax_key=f"xmax_{name}",
                           color='#1f77b4')
    st.divider()

# ── Summed histogram ──────────────────────────────────────────────────────────
st.subheader(f"Συνολικό ιστόγραμμα ({len(datasets)} αρχεία)")
make_histogram_section(all_masses,
                       bins_key="bins_summed",
                       count_key="count_summed",
                       fit_key="fit_summed",
                       xmin_key="xmin_summed",
                       xmax_key="xmax_summed",
                       color='#d62728')

# ════════════════════════════════════════════════════════════════════════════════
# Feature 1 – Signal window analysis
# ════════════════════════════════════════════════════════════════════════════════
st.divider()
with st.expander("Ανάλυση Παραθύρου Σήματος", expanded=False):
    st.markdown(
        "Ορίστε ένα εύρος μάζας (**παράθυρο σήματος**) και μετρήστε τα γεγονότα μέσα σε αυτό. "
        "Χρήσιμο για εκτίμηση της απόδοσης ενός σωματιδίου (π.χ. Z, J/ψ, Higgs) ή "
        "υπολογισμό λόγου σήματος/υποβάθρου."
    )

    sw_xmin, sw_xmax = _read_range("xmin_summed", "xmax_summed")

    sw_col1, sw_col2 = st.columns(2)
    default_lo = round(sw_xmin + (sw_xmax - sw_xmin) * 0.4, 1)
    default_hi = round(sw_xmin + (sw_xmax - sw_xmin) * 0.6, 1)
    with sw_col1:
        sig_min = st.number_input("Κάτω όριο παραθύρου (GeV)",
                                  min_value=float(sw_xmin), max_value=float(sw_xmax),
                                  value=default_lo, step=0.5, key="sig_min")
    with sw_col2:
        sig_max = st.number_input("Άνω όριο παραθύρου (GeV)",
                                  min_value=float(sw_xmin), max_value=float(sw_xmax),
                                  value=default_hi, step=0.5, key="sig_max")

    if sig_min >= sig_max:
        st.warning("Το κάτω όριο πρέπει να είναι μικρότερο από το άνω.")
    else:
        in_range = all_masses[(all_masses >= sw_xmin) & (all_masses <= sw_xmax)]
        n_total  = len(in_range)
        n_sig    = int(((all_masses >= sig_min) & (all_masses <= sig_max)).sum())
        n_out    = n_total - n_sig
        pct      = (n_sig / n_total * 100) if n_total > 0 else 0.0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Σύνολο (εύρος ανάλυσης)", n_total)
        m2.metric("Εντός παραθύρου", n_sig)
        m3.metric("Εκτός παραθύρου", n_out)
        m4.metric("Ποσοστό στο παράθυρο", f"{pct:.1f}%")

        bins_sw = st.selectbox("Αριθμός Bin για εμφάνιση", options=bin_options,
                               index=bin_options.index(100), key="bins_sw")

        if not in_range.empty:
            bw_sw   = (sw_xmax - sw_xmin) / bins_sw
            abin_sw = alt.Bin(step=bw_sw, extent=[sw_xmin, sw_xmax])

            # Tag each mass value as inside or outside the signal window
            sw_df = pd.DataFrame({'mass': in_range})
            sw_df['παράθυρο'] = np.where(
                (sw_df['mass'] >= sig_min) & (sw_df['mass'] <= sig_max),
                'Εντός', 'Εκτός'
            )

            sw_bars = alt.Chart(sw_df).mark_bar(opacity=0.75).encode(
                alt.X('mass:Q', bin=abin_sw, title='Αναλλοίωτη Μάζα (GeV)',
                      axis=alt.Axis(grid=True, ticks=True)),
                alt.Y('count()', stack='zero', title='Γεγονότα',
                      axis=alt.Axis(grid=True)),
                alt.Color('παράθυρο:N',
                          scale=alt.Scale(domain=['Εντός', 'Εκτός'],
                                          range=['#d62728', '#aec7e8']),
                          legend=alt.Legend(title='Παράθυρο')),
                tooltip=[
                    alt.Tooltip('mass:Q', bin=abin_sw, title='Εύρος', format='.1f'),
                    alt.Tooltip('count()', title='Γεγονότα'),
                    alt.Tooltip('παράθυρο:N', title='Κατηγορία'),
                ]
            )
            rule_lo = alt.Chart(pd.DataFrame({'x': [sig_min]})).mark_rule(
                color='red', strokeDash=[5, 3], strokeWidth=2).encode(x='x:Q')
            rule_hi = alt.Chart(pd.DataFrame({'x': [sig_max]})).mark_rule(
                color='red', strokeDash=[5, 3], strokeWidth=2).encode(x='x:Q')

            st.altair_chart(
                (sw_bars + rule_lo + rule_hi).interactive().properties(height=280),
                use_container_width=True
            )

# ════════════════════════════════════════════════════════════════════════════════
# Feature 2 – Channel comparison (stacked bar histogram)
# ════════════════════════════════════════════════════════════════════════════════
st.divider()
with st.expander("Σύγκριση Καναλιών Διάσπασης", expanded=False):
    st.markdown(
        "Στοιβαγμένο ιστόγραμμα για όλα τα κανάλια διάσπασης. "
    )

    ov_col1, ov_col2 = st.columns(2)
    with ov_col1:
        bins_ov = st.selectbox("Αριθμός Bin", options=bin_options,
                               index=bin_options.index(100), key="bins_overlay")

    ov_xmin, ov_xmax = _read_range("ov_xmin", "ov_xmax")

    ov_rc1, ov_rc2 = st.columns(2)
    with ov_rc1:
        st.number_input("X min (GeV)", min_value=0, max_value=max_mass,
                        value=ov_xmin, key="ov_xmin")
    with ov_rc2:
        st.number_input("X max (GeV)", min_value=0, max_value=max_mass,
                        value=ov_xmax, key="ov_xmax")

    # Build combined DataFrame with 'mass' and 'channel' columns
    all_sel_df = pd.concat(
        [df[df['event'].isin(selected_events)][['mass', 'event']]
         for df in datasets.values()],
        ignore_index=True
    )
    all_sel_df['channel'] = all_sel_df['event'].map(lambda x: display_map.get(x, x))
    all_sel_df = all_sel_df[
        (all_sel_df['mass'] >= ov_xmin) & (all_sel_df['mass'] <= ov_xmax)
    ]

    if not all_sel_df.empty:
        bw_ov   = (ov_xmax - ov_xmin) / bins_ov
        abin_ov = alt.Bin(step=bw_ov, extent=[ov_xmin, ov_xmax])

        # Build a scale whose domain contains ONLY the channels present in the
        # current data (so the legend shows only those), but colours are looked
        # up from the fixed CHANNEL_COLORS map so they never shift.
        _present   = [ch for ch in CHANNEL_COLORS
                      if ch in all_sel_df['channel'].unique()]
        _ch_domain = _present
        _ch_range  = [CHANNEL_COLORS[ch] for ch in _present]

        # Altair stacks count() per (bin, channel) automatically with stack='zero'
        stacked_chart = alt.Chart(all_sel_df).mark_bar(opacity=0.8).encode(
            alt.X('mass:Q', bin=abin_ov, title='Αναλλοίωτη Μάζα (GeV)',
                  axis=alt.Axis(grid=True, ticks=True)),
            alt.Y('count()', stack='zero', title='Γεγονότα',
                  axis=alt.Axis(grid=True)),
            alt.Color('channel:N',
                      scale=alt.Scale(domain=_ch_domain, range=_ch_range),
                      legend=alt.Legend(title='Κανάλι')),
            tooltip=[
                alt.Tooltip('channel:N',  title='Κανάλι'),
                alt.Tooltip('mass:Q', bin=abin_ov, title='Εύρος Μάζας', format='.1f'),
                alt.Tooltip('count()',    title='Γεγονότα'),
            ]
        ).interactive()
        st.altair_chart(stacked_chart.properties(height=350), use_container_width=True)

        # ── Per-channel counts table ──────────────────────────────────────────
        ch_counts = (
            all_sel_df.groupby('channel', as_index=False)
            .agg(Γεγονότα=('mass', 'count'))
            .sort_values('Γεγονότα', ascending=False)
            .reset_index(drop=True)
        )
        total_ch = int(ch_counts['Γεγονότα'].sum())
        ch_counts['Ποσοστό (%)'] = (
            ch_counts['Γεγονότα'] / total_ch * 100
        ).round(1)
        ch_counts = ch_counts.rename(columns={'channel': 'Κανάλι'})
        # Totals row
        totals_row = pd.DataFrame([{
            'Κανάλι': 'Σύνολο', 'Γεγονότα': total_ch, 'Ποσοστό (%)': 100.0
        }])
        ch_counts = pd.concat([ch_counts, totals_row], ignore_index=True)

        st.caption(f"Γεγονότα ανά κανάλι στο εύρος **{ov_xmin} – {ov_xmax} GeV**")
        st.dataframe(ch_counts, hide_index=True, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν αρκετά δεδομένα για σύγκριση καναλιών στο επιλεγμένο εύρος.")
