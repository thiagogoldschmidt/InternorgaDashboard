import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np # Optional, useful for some data manipulations

# --- Page Configuration ---
st.set_page_config(
    page_title="INTERNORGA 2025 Leads Dashboard",
    page_icon="📊",
    layout="wide" # Use wide layout for more space
)

# --- Load Data ---
# Use caching to load data only once and improve performance
@st.cache_data
def load_data(file_path="internorga_leads.csv"):
    """Loads the lead data from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        # Basic Data Cleaning (Adapt as needed)
        # Handle potential '/' or blank scores - replace with 'Unscored'
        if 'Scoring' in df.columns:
            df['Scoring'] = df['Scoring'].fillna('Unscored').replace(['/', ''], 'Unscored')
        # Convert Yes/No columns to more standard format if necessary (e.g., boolean or consistent strings)
        # Example: df['Upsell Potential'] = df['Upsell Potential'].map({'Yes': True, 'No': False, 'Ja': True, 'Nein': False})
        return df
    except FileNotFoundError:
        st.error(f"Error: The file '{file_path}' was not found. Make sure it's in the same directory as the script.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        return None

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filter Leads:")

if df is not None:
    # Get unique values for filters, handling potential missing values
    scoring_options = sorted(df['Scoring'].dropna().unique())
    vertikal_options = sorted(df['Vertikal'].dropna().unique())
    follow_up_options = sorted(df['Follow up'].dropna().unique())
    rep_options = sorted(df['Rep'].dropna().unique())
    outcome_options = sorted(df['Event Outcome'].dropna().unique())

    # Add multiselect filters to the sidebar
    selected_scoring = st.sidebar.multiselect("Filter by Scoring:", scoring_options, default=scoring_options)
    selected_vertikal = st.sidebar.multiselect("Filter by Vertikal:", vertikal_options, default=vertikal_options)
    selected_follow_up = st.sidebar.multiselect("Filter by Follow up:", follow_up_options, default=follow_up_options)
    selected_rep = st.sidebar.multiselect("Filter by Rep:", rep_options, default=rep_options) # Added Rep filter
    selected_outcome = st.sidebar.multiselect("Filter by Event Outcome:", outcome_options, default=outcome_options) # Added Outcome filter

    # Add text search for Company or Contact
    search_term = st.sidebar.text_input("Search by Company or Contact Name:")

    # --- Filter Dataframe based on selections ---
    df_filtered = df.copy() # Start with a copy of the original data

    # Apply multiselect filters
    if selected_scoring:
        df_filtered = df_filtered[df_filtered['Scoring'].isin(selected_scoring)]
    if selected_vertikal:
        df_filtered = df_filtered[df_filtered['Vertikal'].isin(selected_vertikal)]
    if selected_follow_up:
        df_filtered = df_filtered[df_filtered['Follow up'].isin(selected_follow_up)]
    if selected_rep:
        df_filtered = df_filtered[df_filtered['Rep'].isin(selected_rep)]
    if selected_outcome:
        df_filtered = df_filtered[df_filtered['Event Outcome'].isin(selected_outcome)]

    # Apply text search filter (case-insensitive)
    if search_term:
        # Ensure search works even if names/company are numbers or missing (NaN)
        search_condition = (
            df_filtered['Firma'].astype(str).str.contains(search_term, case=False, na=False) |
            df_filtered['Vorname'].astype(str).str.contains(search_term, case=False, na=False) |
            df_filtered['Nachname'].astype(str).str.contains(search_term, case=False, na=False)
        )
        df_filtered = df_filtered[search_condition]

else:
    # If data loading failed, create an empty dataframe to avoid errors later
    df_filtered = pd.DataFrame()
    st.warning("Data could not be loaded. Please check the CSV file and path.")


# --- Main Dashboard Area ---
st.title("📊 INTERNORGA 2025 Leads Dashboard")
st.markdown("Use the filters in the sidebar to explore the lead data.")

if df_filtered is not None and not df_filtered.empty:
    # --- KPI Cards ---
    st.header("Key Metrics")
    total_leads = df_filtered.shape[0]
    # Count leads by score (example assumes 'A', 'B', 'C' are main scores)
    leads_a = df_filtered[df_filtered['Scoring'] == 'A'].shape[0] if 'A' in df_filtered['Scoring'].values else 0
    leads_b = df_filtered[df_filtered['Scoring'] == 'B'].shape[0] if 'B' in df_filtered['Scoring'].values else 0
    leads_c = df_filtered[df_filtered['Scoring'] == 'C'].shape[0] if 'C' in df_filtered['Scoring'].values else 0
    leads_unscored = df_filtered[df_filtered['Scoring'] == 'Unscored'].shape[0] if 'Unscored' in df_filtered['Scoring'].values else 0


    kpi_cols = st.columns(5) # Create columns for KPIs
    kpi_cols[0].metric("Total Leads", total_leads)
    kpi_cols[1].metric("A-Leads", leads_a)
    kpi_cols[2].metric("B-Leads", leads_b)
    kpi_cols[3].metric("C-Leads", leads_c)
    kpi_cols[4].metric("Unscored Leads", leads_unscored)

    st.markdown("---") # Separator

    # --- Charts ---
    st.header("Visualizations")
    chart_cols = st.columns(2) # Create two columns for charts

    # Leads per Vertical (Bar Chart)
    if 'Vertikal' in df_filtered.columns:
        vertical_counts = df_filtered['Vertikal'].value_counts().reset_index()
        vertical_counts.columns = ['Vertikal', 'Count']
        fig_vertical = px.bar(vertical_counts, x='Vertikal', y='Count', title='Leads per Vertical',
                              text_auto=True) # Show count on bars
        fig_vertical.update_layout(xaxis_title=None) # Cleaner axis
        chart_cols[0].plotly_chart(fig_vertical, use_container_width=True)

    # Leads per Rep (Pie Chart - use Bar if many Reps)
    if 'Rep' in df_filtered.columns:
        rep_counts = df_filtered['Rep'].value_counts().reset_index()
        rep_counts.columns = ['Rep', 'Count']
        # Use Pie for few reps, Bar for many
        if len(rep_counts) < 8:
             fig_rep = px.pie(rep_counts, names='Rep', values='Count', title='Leads per Rep', hole=0.3)
        else:
             fig_rep = px.bar(rep_counts.sort_values('Count', ascending=False),
                              x='Rep', y='Count', title='Leads per Rep', text_auto=True)
             fig_rep.update_layout(xaxis_title=None)
        chart_cols[1].plotly_chart(fig_rep, use_container_width=True)

    chart_cols2 = st.columns(2) # Another row for charts

    # Event Outcome Distribution (Pie Chart)
    if 'Event Outcome' in df_filtered.columns:
        outcome_counts = df_filtered['Event Outcome'].value_counts().reset_index()
        outcome_counts.columns = ['Event Outcome', 'Count']
        fig_outcome = px.pie(outcome_counts, names='Event Outcome', values='Count',
                             title='Event Outcome Distribution', hole=0.3)
        chart_cols2[0].plotly_chart(fig_outcome, use_container_width=True)

    # Placed in column 2
    if 'Scoring' in df_filtered.columns:
        scoring_counts = df_filtered['Scoring'].value_counts().reset_index()
        # Rename columns for clarity in Plotly
        scoring_counts.columns = ['Scoring', 'Count']
        fig_scoring = px.pie(scoring_counts,
                             names='Scoring',        # Column with categories (A, B, C...)
                             values='Count',         # Column with counts
                             title='Lead Quality Distribution (Scoring)',
                             hole=0.3)              # Make it a donut chart
        # Optional: Improve label display
        fig_scoring.update_traces(textposition='inside', textinfo='percent+label')
        # Display the chart in the 3rd column of the second row
        chart_cols2[1].plotly_chart(fig_scoring, use_container_width=True)


    st.markdown("---") # Separator

    # --- Interactive Table ---
    st.header("Lead Details")
    st.markdown("Scroll within the table to see all columns and rows.")

    # Select columns to display in the table (adjust as needed)
    display_columns = [
        'Rep', 'Scoring', 'Vertikal', 'Firma', 'Vorname', 'Nachname',
        'E-Mail', 'Phone', 'LinkedIn', # Add contact details if they exist
        'Event Outcome', 'Follow up', 'Upsell Potential',
        'Notizen', 'Extra Notizen' # Place notes at the end for readability
    ]
    # Filter out columns that might not exist in the loaded data
    display_columns = [col for col in display_columns if col in df_filtered.columns]

    # Use st.dataframe for a standard interactive table
    st.dataframe(df_filtered[display_columns], use_container_width=True, height=500)
    # Note: Showing full notes on hover requires more complex components.
    # st.dataframe usually allows scrolling within cells if text is long.

elif df is not None:
    st.warning("No leads match the current filter criteria.")