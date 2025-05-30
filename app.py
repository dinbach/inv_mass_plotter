# import os
# import streamlit as st
# import pandas as pd
# import altair as alt

# # Constants
# data_dir = "uploads"
# skip_labels = {'4ee', '4em', '4mm', '4me'}
# display_map = {
#     '4e': '4e',
#     'e': 'ee',
#     'g': 'γγ',
#     '4m': '4μ',
#     'm': 'μμ',
#     '4em': '2e2μ',
#     '4me': '2μ2e'
# }

# # Ensure upload directory exists
# os.makedirs(data_dir, exist_ok=True)

# # Streamlit setup
# st.set_page_config(page_title="Invariant Mass Event Plotter", layout="wide")
# st.title("Ιστογράμματα Αναλλοίωτης Μάζας")

# # Sidebar controls
# bin_options = [5, 10, 20, 50, 70, 100, 200, 400]
# bins = st.sidebar.selectbox("Αριθμός bins", bin_options, index=bin_options.index(50))

# # File uploader
# def save_upload(uploaded_file):
#     with open(os.path.join(data_dir, uploaded_file.name), 'wb') as f:
#         f.write(uploaded_file.getbuffer())

# uploaded_files = st.file_uploader(
#     "Ανεβάστε ένα ή περισσότερα αρχεία (.txt)",
#     type=['txt'], accept_multiple_files=True
# )
# if uploaded_files:
#     for uf in uploaded_files:
#         save_upload(uf)
#         st.success(f"Saved {uf.name}")

# # Load datasets from disk
# def load_datasets():
#     datasets = {}
#     for fname in sorted(os.listdir(data_dir)):
#         if not fname.lower().endswith('.txt'):
#             continue
#         path = os.path.join(data_dir, fname)
#         try:
#             df = pd.read_csv(path, sep=r"\s+", header=None, names=['mass', 'event'])
#             # Skip logic
#             mask = pd.Series(False, index=df.index)
#             for idx, lbl in df['event'].items():
#                 if lbl in skip_labels:
#                     mask.loc[idx+1:idx+2] = True
#             df = df.loc[~mask]
#             datasets[fname] = df
#         except Exception:
#             continue
#     return datasets

# datasets = load_datasets()

# if not datasets:
#     st.info("Παρακαλώ ανεβάστε ένα ή περισσότερα αρχεία .txt από το πρόγραμμα HYPATIA για οπτικοποίηση της αναλλοίωτης μάζας.")
#     st.stop()

# # Event filter and axis bounds
# all_events = sorted({e for df in datasets.values() for e in df['event'].unique()})
# selected_events = st.sidebar.multiselect(
#     "Επιλογή τύπου τελικής κατάστασης", options=all_events, default=all_events,
#     format_func=lambda x: display_map.get(x, x)
# )
# all_masses = pd.concat([df[df['event'].isin(selected_events)]['mass'] for df in datasets.values()])
# if all_masses.empty:
#     st.info("Δεν υπάρχουν γεγονότα για τα επιλεγμένα είδη τελικής κατάστασης.")
#     st.stop()
# min_val, max_val = int(all_masses.min() - 100), int(all_masses.max() +100)
# # min_val, max_val = 0, 2000
# x_min = st.sidebar.number_input("Κατώτερο όριο X-άξονα", min_val, max_val, min_val)
# x_max = st.sidebar.number_input("Ανώτερο όριο X-άξονα", min_val, max_val, max_val)

# # Stats helper, display only 1 decimal place
# def stats_table(series: pd.Series) -> pd.DataFrame:
#     filtered = series[(series >= x_min) & (series <= x_max)]
#     return pd.DataFrame({
#         'Statistic': ['Count', 'Mean', 'Std', 'Min', 'Max'],
#         'Value': [
#             int(filtered.count()),
#             f"{filtered.mean():.1f}",
#             f"{filtered.std():.1f}",
#             f"{filtered.min():.1f}",
#             f"{filtered.max():.1f}"
#         ]
#     })

# # Plot individual histograms
# for name, df in datasets.items():
#     sel = df[df['event'].isin(selected_events)]['mass']
#     st.subheader(f"Ιστόγραμμα από {name}")
#     col1, col2 = st.columns([3, 1])
#     with col1:
#         show_counts = st.checkbox(f"Show bin counts for {name}", key=name)
#         base = alt.Chart(pd.DataFrame({'mass': sel})).encode(
#             alt.X('mass:Q', bin=alt.Bin(maxbins=bins), scale=alt.Scale(domain=[x_min, x_max]), title='Invariant Mass', axis=alt.Axis(grid=True, ticks=True)),
#             alt.Y('count()', title='Αριθμός Γεγονότων', axis=alt.Axis(grid=True))
#         )
#         chart = base.mark_bar(opacity=0.7, color='#1f77b4').interactive()
#         if show_counts:
#             text = base.mark_text(dy=-5, fontSize=10).encode(text='count()')
#             chart = chart + text
#         st.altair_chart(chart.properties(width=500, height=250), use_container_width=True)
#     with col2:
#         st.table(stats_table(sel))

# # Summed histogram
# summed = all_masses
# st.subheader("Συνολικό ιστόγραμμα από όλα τα αρχεία")
# col1, col2 = st.columns([3, 1])
# with col1:
#     show_sum = st.checkbox("Show bin counts for Summed", key="summed")
#     base = alt.Chart(pd.DataFrame({'mass': summed})).encode(
#         alt.X('mass:Q', bin=alt.Bin(maxbins=bins), scale=alt.Scale(domain=[x_min, x_max]), title='Invariant Mass', axis=alt.Axis(grid=True, ticks=True)),
#         alt.Y('count()', title='Αριθμός Γεγονότων', axis=alt.Axis(grid=True))
#     )
#     chart = base.mark_bar(opacity=0.7, color='#d62728').interactive()
#     if show_sum:
#         text = base.mark_text(dy=-5, fontSize=10).encode(text='count()')
#         chart = chart + text
#     st.altair_chart(chart.properties(width=500, height=250), use_container_width=True)
# with col2:
#     st.table(stats_table(summed))
    
#V2
import os
import streamlit as st
import pandas as pd
import altair as alt

# Constants
data_dir = "uploads"
skip_labels = {'4ee', '4em', '4mm'}
display_map = {
    '4e': '4e',
    'e': 'ee',
    'g': 'γγ',
    '4m': '4μ',
    'm': 'μμ',
    '2e2m': '2e2μ'
}
bin_options = [5, 10, 20, 50, 70, 100, 200, 400]

# Ensure upload directory exists
os.makedirs(data_dir, exist_ok=True)

# Streamlit setup
st.set_page_config(page_title="Invariant Mass Event Plotter", layout="wide")
st.title("Invariant Mass Event Plotter")

# File uploader in sidebar
def save_upload(uploaded_file):
    path = os.path.join(data_dir, uploaded_file.name)
    with open(path, 'wb') as f:
        f.write(uploaded_file.getbuffer())

uploaded_files = st.sidebar.file_uploader(
    "Upload text files (.txt)",
    type=['txt'],
    accept_multiple_files=True
)
if uploaded_files:
    for uf in uploaded_files:
        save_upload(uf)
        st.sidebar.success(f"Saved {uf.name}")

# Load datasets from disk
def load_datasets():
    datasets = {}
    for fname in sorted(os.listdir(data_dir)):
        if not fname.lower().endswith('.txt'):
            continue
        df = pd.read_csv(os.path.join(data_dir, fname), sep=r"\s+", header=None, names=['mass', 'event'])
        # Skip two rows after specific labels
        mask = pd.Series(False, index=df.index)
        for idx, lbl in df['event'].items():
            if lbl in skip_labels:
                mask.loc[idx+1:idx+2] = True
        datasets[fname] = df.loc[~mask]
    return datasets

datasets = load_datasets()
if not datasets:
    st.info("Please upload one or more text files to begin.")
    st.stop()

# Global event filter
events = sorted({e for df in datasets.values() for e in df['event'].unique()})
selected_events = st.sidebar.multiselect(
    "Select event types to include",
    options=events,
    default=events,
    format_func=lambda x: display_map.get(x, x)
)

# Combine masses for axis bounds
all_masses = pd.concat([
    df[df['event'].isin(selected_events)]['mass'] for df in datasets.values()
])
min_mass, max_mass = int(all_masses.min()), int(all_masses.max())

# X-axis bounds inputs
def get_axis_bounds():
    x_min = st.sidebar.number_input(
        "X-axis min",
        min_value=0,
        max_value=max_mass,
        value=0
    )
    x_max = st.sidebar.number_input(
        "X-axis max",
        min_value=0,
        max_value=max_mass,
        value=min(max_mass, 2000)
    )
    return x_min, x_max

x_min, x_max = get_axis_bounds()

# Statistics table helper
def stats_table(series):
    filtered = series[(series >= x_min) & (series <= x_max)]
    return pd.DataFrame({
        'Statistic': ['Count', 'Mean', 'Std', 'Min', 'Max'],
        'Value': [
            int(filtered.count()),
            filtered.mean(),
            filtered.std(),
            filtered.min(),
            filtered.max()
        ]
    })

# Plot individual histograms with per-plot bin selector
for name, df in datasets.items():
    st.subheader(f"Histogram for {name}")
    sel = df[df['event'].isin(selected_events)]['mass']
    col1, col2 = st.columns([3, 1])
    with col1:
        bins_ind = st.selectbox(
            f"Bins for {name}",
            options=bin_options,
            index=bin_options.index(50),
            key=f"bins_{name}"
        )
        show_counts = st.checkbox(
            f"Show bin counts for {name}",
            key=f"count_{name}"
        )
        # Base chart with dynamic binning and extent
        base = alt.Chart(pd.DataFrame({'mass': sel})).encode(
            alt.X(
                'mass:Q',
                bin=alt.Bin(maxbins=bins_ind, extent=[x_min, x_max]),
                title='Invariant Mass',
                axis=alt.Axis(grid=True, ticks=True)
            ),
            alt.Y(
                'count()',
                # y-title should be: "counts/"+str((x_max-x_min)/bins_ind),
                title='Counts/'+ str((x_max-x_min)/bins_ind),
                axis=alt.Axis(grid=True)
            )#,
            # # the tooltip should provide the mass range with 1 decimal place and count with 1 decimal place
            # tooltip=[
            #     alt.Tooltip('mass:Q', bin=alt.Bin(maxbins=bins_ind, extent=[x_min, x_max]), format='.1f'),
            #     alt.Tooltip('count()', format='.1f')
            # ]
            
        )
        chart = base.mark_bar(opacity=0.7, color='#1f77b4').interactive()
        if show_counts:
            text = alt.Chart(pd.DataFrame({'mass': sel})).mark_text(dy=-5, fontSize=10).encode(
                alt.X(
                    'mass:Q',
                    bin=alt.Bin(maxbins=bins_ind, extent=[x_min, x_max])
                ),
                text='count()'
            )
            chart = chart + text
        st.altair_chart(chart.properties(width=500, height=250), use_container_width=True)
    with col2:
        st.table(stats_table(sel))

# Summed histogram with its own bin selector
st.subheader("Summed Histogram of All Uploaded Files")
summed = all_masses
col1, col2 = st.columns([3, 1])
with col1:
    bins_sum = st.selectbox(
        "Bins for Summed",
        options=bin_options,
        index=bin_options.index(50),
        key="bins_summed"
    )
    show_sum = st.checkbox(
        "Show bin counts for Summed",
        key="count_summed"
    )
    base_sum = alt.Chart(pd.DataFrame({'mass': summed})).encode(
        alt.X(
            'mass:Q',
            bin=alt.Bin(maxbins=bins_sum, extent=[x_min, x_max]),
            title='Invariant Mass',
            axis=alt.Axis(grid=True, ticks=True)
        ),
        alt.Y(
            'count()',
            # y-title should be: "counts/"+str((x_mass-x_min)/bins_sum),
            title='Counts/'+ str((x_max-x_min)/bins_sum),
            axis=alt.Axis(grid=True)
        )
    )
    chart_sum = base_sum.mark_bar(opacity=0.7, color='#d62728').interactive()
    if show_sum:
        text_sum = alt.Chart(pd.DataFrame({'mass': summed})).mark_text(dy=-5, fontSize=10).encode(
            alt.X(
                'mass:Q',
                bin=alt.Bin(maxbins=bins_sum, extent=[x_min, x_max])
            ),
            text='count()'
        )
        chart_sum = chart_sum + text_sum
    st.altair_chart(chart_sum.properties(width=500, height=250), use_container_width=True)
with col2:
    st.table(stats_table(summed))
