import streamlit as st
import pandas as pd
import altair as alt
import os

# Constants
data_dir = "uploads"
skip_labels = {'4ee', '4em', '4mm'}

# Ensure upload directory exists
os.makedirs(data_dir, exist_ok=True)

# Streamlit page setup
st.set_page_config(page_title="Invariant Mass Event Plotter", layout="wide")
st.title("Invariant Mass Event Plotter")

# Sidebar: bin selection and axis bounds
st.sidebar.header("Plot Settings")
bin_options = [5, 10, 20, 50, 70, 100, 200, 400]
bins = st.sidebar.selectbox("Number of bins", options=bin_options, index=bin_options.index(50))

# After all uploads, reload files from disk each time

def load_datasets():
    datasets = {}
    for fname in sorted(os.listdir(data_dir)):
        if not fname.lower().endswith('.txt'):
            continue
        path = os.path.join(data_dir, fname)
        try:
            df = pd.read_csv(path, sep=r"\s+", header=None, names=['mass', 'event'])
            if df.shape[1] != 2 or not pd.api.types.is_float_dtype(df['mass']):
                continue
            # process skip logic
            mask = pd.Series(False, index=df.index)
            for idx, lbl in df['event'].items():
                if lbl in skip_labels:
                    mask.loc[idx+1:idx+2] = True
            df = df.loc[~mask]
            datasets[fname] = df
        except Exception:
            # skip invalid
            continue
    return datasets

# Handle new uploads
def save_upload(uploaded_file):
    # overwrite if same name
    save_path = os.path.join(data_dir, uploaded_file.name)
    with open(save_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())

uploaded_files = st.file_uploader(
    "Upload one or more text files with invariant mass data", 
    type=['txt'], accept_multiple_files=True
)
if uploaded_files:
    for uf in uploaded_files:
        try:
            save_upload(uf)
            st.success(f"Saved {uf.name}")
        except Exception as e:
            st.error(f"Failed to save {uf.name}: {e}")

# Load all stored datasets
datasets = load_datasets()

if datasets:
    # global combined masses for bounds and filter defaults
    all_events = sorted({e for df in datasets.values() for e in df['event'].unique()})
    selected_events = st.sidebar.multiselect(
        "Select event types to include", options=all_events, default=all_events
    )

    all_masses = pd.concat([df[df['event'].isin(selected_events)]['mass'] for df in datasets.values()])
    global_min, global_max = float(all_masses.min()), float(all_masses.max())
    x_min = st.sidebar.number_input("Lower bound", value=global_min)
    x_max = st.sidebar.number_input("Upper bound", value=global_max)

    # stats helper
    def stats_table(series: pd.Series) -> pd.DataFrame:
        return pd.DataFrame({
            'Statistic': ['Count', 'Mean', 'Std', 'Min', 'Max'],
            'Value': [
                int(series.count()),
                round(series.mean(), 3),
                round(series.std(), 3),
                round(series.min(), 3),
                round(series.max(), 3)
            ]
        })

    # Individual
    for name, df in datasets.items():
        sel = df[df['event'].isin(selected_events)]['mass']
        st.subheader(f"Histogram for {name}")
        col1, col2 = st.columns([3, 1])
        with col1:
            chart = alt.Chart(pd.DataFrame({'mass': sel})).mark_bar(color='#1f77b4', opacity=0.7).encode(
                alt.X('mass:Q', bin=alt.Bin(maxbins=bins), scale=alt.Scale(domain=[x_min, x_max]), title='Invariant Mass'),
                alt.Y('count()', title='Counts')
            ).properties(width=500, height=250, title=name).interactive()
            st.altair_chart(chart, use_container_width=True)
        with col2:
            st.table(stats_table(sel))

    # Summed
    if len(datasets) > 1:
        summed = all_masses
        st.subheader("Summed Histogram of All Uploaded Files")
        col1, col2 = st.columns([3, 1])
        with col1:
            chart_sum = alt.Chart(pd.DataFrame({'mass': summed})).mark_bar(color='#d62728', opacity=0.7).encode(
                alt.X('mass:Q', bin=alt.Bin(maxbins=bins), scale=alt.Scale(domain=[x_min, x_max]), title='Invariant Mass'),
                alt.Y('count()', title='Counts')
            ).properties(width=500, height=250, title='Summed Invariant Mass').interactive()
            st.altair_chart(chart_sum, use_container_width=True)
        with col2:
            st.table(stats_table(summed))

        st.subheader("Interactive Summed Histogram (Zoomable)")
        col1, col2 = st.columns([3, 1])
        with col1:
            chart_int = alt.Chart(pd.DataFrame({'mass': summed})).mark_bar(color='#2ca02c', opacity=0.7).encode(
                alt.X('mass:Q', bin=alt.Bin(maxbins=bins), scale=alt.Scale(domain=[x_min, x_max]), title='Invariant Mass'),
                alt.Y('count()', title='Counts')
            ).properties(width=500, height=250, title='Interactive Summed Invariant Mass').interactive()
            st.altair_chart(chart_int, use_container_width=True)
        with col2:
            st.table(stats_table(summed))
else:
    st.info("Please upload one or more text files (.txt) to visualize invariant mass distributions.")
