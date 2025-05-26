# import streamlit as st
# import pandas as pd
# import altair as alt

# # Page setup
# st.set_page_config(page_title="Invariant Mass Event Plotter", layout="wide")
# st.title("Invariant Mass Event Plotter")

# # Sidebar controls
# st.sidebar.header("Plot Settings")
# bins = st.sidebar.slider("Number of bins", min_value=10, max_value=200, value=50)

# # Initialize storage for datasets
# if 'datasets' not in st.session_state:
#     st.session_state['datasets'] = {}

# # File uploader
# uploaded_files = st.file_uploader(
#     "Upload one or more text files with invariant mass data",
#     type=['txt'],
#     accept_multiple_files=True
# )

# # Processing function: skip two rows after specified labels
# def process_df(df: pd.DataFrame) -> pd.DataFrame:
#     skip_labels = {'4ee', '4em', '4mm'}
#     mask = pd.Series(False, index=df.index)
#     for idx, lbl in df['event'].items():
#         if lbl in skip_labels:
#             mask.loc[idx+1:idx+2] = True
#     return df.loc[~mask]

# # Read & validate uploads
# if uploaded_files:
#     for file in uploaded_files:
#         name = file.name
#         try:
#             df = pd.read_csv(file, sep=r"\s+", header=None, names=['mass', 'event'])
#             if df.shape[1] != 2 or not pd.api.types.is_float_dtype(df['mass']):
#                 raise ValueError
#         except Exception:
#             st.error(f"'{name}' is invalid. Please upload a two-column text file: float mass and event label.")
#             continue
#         st.session_state['datasets'][name] = process_df(df)

# # If data available, plot
# if st.session_state['datasets']:
#     # Event type filter
#     all_events = sorted(
#         {e for df in st.session_state['datasets'].values() for e in df['event'].unique()}
#     )
#     selected_events = st.sidebar.multiselect(
#         "Select event types to include", options=all_events, default=all_events
#     )

#     # Individual histograms (Altair)
#     for name, df in st.session_state['datasets'].items():
#         df_sel = df[df['event'].isin(selected_events)]
#         st.subheader(f"Histogram for {name}")
#         chart = alt.Chart(df_sel).mark_bar(opacity=0.7, color='#1f77b4').encode(
#             alt.X('mass:Q', bin=alt.Bin(maxbins=bins), title='Invariant Mass'),
#             alt.Y('count()', title='Counts')
#         ).properties(
#             width=600,
#             height=250,
#             title=f"{name}"
#         ).configure_title(
#             fontSize=14,
#             anchor='start'
#         ).configure_axis(
#             labelFontSize=11,
#             titleFontSize=12
#         ).configure_view(
#             strokeOpacity=0
#         )
#         st.altair_chart(chart, use_container_width=True)

#     # Summed histogram (static)
#     if len(st.session_state['datasets']) > 1:
#         st.subheader("Summed Histogram of All Uploaded Files")
#         all_masses = pd.concat([
#             df[df['event'].isin(selected_events)]['mass']
#             for df in st.session_state['datasets'].values()
#         ])
#         df_all = pd.DataFrame({'mass': all_masses})
#         chart_sum = alt.Chart(df_all).mark_bar(opacity=0.7, color='#d62728').encode(
#             alt.X('mass:Q', bin=alt.Bin(maxbins=bins), title='Invariant Mass'),
#             alt.Y('count()', title='Counts')
#         ).properties(
#             width=600,
#             height=250,
#             title='Summed Invariant Mass'
#         ).configure_title(
#             fontSize=14,
#             anchor='start'
#         ).configure_axis(
#             labelFontSize=11,
#             titleFontSize=12
#         ).configure_view(
#             strokeOpacity=0
#         )
#         st.altair_chart(chart_sum, use_container_width=True)

#         # Interactive summed histogram (Altair)
#         st.subheader("Interactive Summed Histogram (Zoomable)")
#         chart_int = alt.Chart(df_all).mark_bar(opacity=0.8, color='#2ca02c').encode(
#             alt.X('mass:Q', bin=alt.Bin(maxbins=bins), title='Invariant Mass'),
#             alt.Y('count()', title='Counts')
#         ).properties(
#             width=600,
#             height=250,
#             title='Interactive Summed Invariant Mass'
#         ).configure_title(
#             fontSize=14,
#             anchor='start'
#         ).configure_axis(
#             labelFontSize=11,
#             titleFontSize=12
#         ).configure_view(
#             strokeOpacity=0
#         ).interactive()
#         st.altair_chart(chart_int, use_container_width=True)
# else:
#     st.info("Please upload one or more text files (.txt) to visualize invariant mass distributions.")


import streamlit as st
import pandas as pd
import altair as alt

# Streamlit page setup
st.set_page_config(page_title="Invariant Mass Event Plotter", layout="wide")
st.title("Invariant Mass Event Plotter")

# Sidebar: bin selection
st.sidebar.header("Plot Settings")
bin_options = [5, 10, 20, 50, 70, 100, 200, 400]
bins = st.sidebar.selectbox("Number of bins", options=bin_options, index=bin_options.index(50))

# Initialize storage for datasets
def get_session_datasets():
    return st.session_state.setdefault('datasets', {})
datasets = get_session_datasets()

# File uploader
uploaded_files = st.file_uploader(
    "Upload one or more text files with invariant mass data",
    type=['txt'], accept_multiple_files=True
)

# Processing: skip two rows after specified labels
skip_labels = {'4ee', '4em', '4mm'}
def process_df(df: pd.DataFrame) -> pd.DataFrame:
    mask = pd.Series(False, index=df.index)
    for idx, lbl in df['event'].items():
        if lbl in skip_labels:
            mask.loc[idx+1:idx+2] = True
    return df.loc[~mask]

# Read & validate uploads
if uploaded_files:
    for file in uploaded_files:
        name = file.name
        try:
            df = pd.read_csv(file, sep=r"\s+", header=None, names=['mass', 'event'])
            if df.shape[1] != 2 or not pd.api.types.is_float_dtype(df['mass']):
                raise ValueError("Invalid format")
        except Exception:
            st.error(f"'{name}' is invalid. Please upload a two-column text file (float mass and event label).")
            continue
        datasets[name] = process_df(df)

# If data available, show filters, bounds, and plots
if datasets:
    # Combine all masses for global bounds
    all_masses = pd.concat(
        [df[df['event'].isin(sorted({e for d in datasets.values() for e in d['event'].unique()}))]['mass'] for df in datasets.values()]
    )
    global_min, global_max = float(all_masses.min()), float(all_masses.max())

    # Sidebar: x-axis bounds
    st.sidebar.header("X-axis Bounds")
    x_min = st.sidebar.number_input("Lower bound", value=global_min)
    x_max = st.sidebar.number_input("Upper bound", value=global_max)

    # Event type filter
    all_events = sorted({e for df in datasets.values() for e in df['event'].unique()})
    selected_events = st.sidebar.multiselect(
        "Select event types to include", options=all_events, default=all_events
    )

    # Plotting helper for stats table
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

    # Individual histograms
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

    # Summed histograms
    if len(datasets) > 1:
        summed = pd.concat([df[df['event'].isin(selected_events)]['mass'] for df in datasets.values()])
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
