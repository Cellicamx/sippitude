import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

# --- Page Configuration ---
st.set_page_config(
    page_title="Interactive Media Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
# Streamlit does not directly support arbitrary font imports or full CSS theming
# in a single Python file without a .streamlit/config.toml file or custom CSS injection.
# We will use custom CSS injection for the font and some basic color hints.
# For overall app colors, Streamlit's theming uses "primaryColor" and "backgroundColor"
# which are set in .streamlit/config.toml. We cannot set these directly in the script.
# So, the "blue and pink dominance" will be primarily in Plotly charts and through
# selective use of custom CSS for text elements and button colors.
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    .stApp {
        background: linear-gradient(to bottom right, #E0F7FA, #FCE4EC); /* Light blue to light pink */
    }
    h1, h2, h3, h4 {
        font-family: 'Poppins', sans-serif !important;
    }
    .stFileUploader > div > button {
        background-color: #007BFF; /* Blue for upload button */
        color: white;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stFileUploader > div > button:hover {
        background-color: #0056b3;
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
    }
    .stSuccess, .stInfo, .stError {
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    /* Specific styles for sections for blue/pink dominant borders/backgrounds */
    section[data-testid="stVerticalBlock"] > div:nth-child(1) > div:nth-child(1) {
        background-color: white;
        border-radius: 1rem;
        box-shadow: 0 10px 15px rgba(0,0,0,0.1);
        padding: 2rem;
        margin-bottom: 2rem;
    }
    /* Section 1: Upload CSV */
    section[data-testid="stVerticalBlock"] > div:nth-child(1) > div:nth-child(2) {
        background-color: #E3F2FD; /* Lighter blue */
        border: 1px solid #90CAF9;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    /* Section 2: Data Cleaning Summary */
    section[data-testid="stVerticalBlock"] > div:nth-child(1) > div:nth-child(3) {
        background-color: #F8E5EE; /* Lighter pink */
        border: 1px solid #F48FB1;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Data Cleaning Function ---
@st.cache_data
def clean_data(_df):
    """
    Cleans the uploaded CSV data.
    - Converts 'Date' to datetime objects.
    - Fills missing 'Engagements' with 0.
    - Normalizes column names to lowercase with underscores.
    """
    if _df.empty:
        return pd.DataFrame(), "No data to clean or process."

    # Normalize column names
    _df.columns = _df.columns.str.lower().str.replace(' ', '_')

    required_columns = ['date', 'platform', 'sentiment', 'location', 'engagements', 'media_type']
    missing_columns = [col for col in required_columns if col not in _df.columns]

    if missing_columns:
        return pd.DataFrame(), f"Missing required columns: {', '.join(missing_columns)}. Please ensure your CSV has 'Date', 'Platform', 'Sentiment', 'Location', 'Engagements', 'Media Type' columns."

    # Convert 'date' to datetime, coercing errors to NaT
    _df['date'] = pd.to_datetime(_df['date'], errors='coerce')

    # Fill missing 'engagements' with 0 and convert to numeric
    _df['engagements'] = pd.to_numeric(_df['engagements'], errors='coerce').fillna(0)

    # Filter out rows with invalid dates
    _df = _df.dropna(subset=['date'])

    return _df, ""

# --- Generate Insights Function ---
def generate_insights(chart_type, data):
    """
    Generates insights based on chart type and data.
    These insights are derived algorithmically from the data presented.
    """
    insights = []
    if data.empty:
        return ["No data available for insights."]

    if chart_type == 'sentiment':
        sentiment_counts = data['sentiment'].value_counts(normalize=True) * 100
        if not sentiment_counts.empty:
            top_sentiment = sentiment_counts.idxmax()
            insights.append(f"Dominant sentiment: **{top_sentiment}** ({sentiment_counts.max():.1f}%).")
            if len(sentiment_counts) > 1:
                second_sentiment = sentiment_counts.drop(top_sentiment).idxmax()
                insights.append(f"Second most common sentiment: **{second_sentiment}** ({sentiment_counts.drop(top_sentiment).max():.1f}%).")
            insights.append(f"Overall, {data['sentiment'].count()} sentiment entries were analyzed.")

    elif chart_type == 'engagement_trend':
        daily_engagements = data.groupby(data['date'].dt.date)['engagements'].sum()
        if not daily_engagements.empty:
            peak_date = daily_engagements.idxmax()
            peak_engagements = daily_engagements.max()
            insights.append(f"Peak engagement occurred on **{peak_date}** with **{peak_engagements:,.0f}** total engagements.")
            avg_engagements = daily_engagements.mean()
            insights.append(f"Average daily engagements across the period: **{avg_engagements:,.0f}**.")
            insights.append(f"Data covers the period from **{daily_engagements.index.min()}** to **{daily_engagements.index.max()}**.")
        else:
            insights.append("No valid date-based engagement data found.")

    elif chart_type == 'platform_engagements':
        platform_engagement_sums = data.groupby('platform')['engagements'].sum().sort_values(ascending=False)
        if not platform_engagement_sums.empty:
            insights.append(f"The platform with the highest engagement is **{platform_engagement_sums.index[0]}** with **{platform_engagement_sums.iloc[0]:,.0f}** engagements.")
            if len(platform_engagement_sums) > 1:
                insights.append(f"The second highest engaging platform is **{platform_engagement_sums.index[1]}** with **{platform_engagement_sums.iloc[1]:,.0f}** engagements.")
            insights.append(f"A total of **{len(platform_engagement_sums)}** unique platforms were identified.")

    elif chart_type == 'media_type_mix':
        media_type_counts = data['media_type'].value_counts(normalize=True) * 100
        if not media_type_counts.empty:
            top_media_type = media_type_counts.idxmax()
            insights.append(f"The most prevalent media type is **{top_media_type}** ({media_type_counts.max():.1f}%).")
            if len(media_type_counts) > 1:
                second_media_type = media_type_counts.drop(top_media_type).idxmax()
                insights.append(f"The second most common media type is **{second_media_type}** ({media_type_counts.drop(top_media_type).max():.1f}%).")
            insights.append(f"In total, **{data['media_type'].count()}** media type entries were counted.")

    elif chart_type == 'top_locations':
        location_counts = data['location'].value_counts().head(5) # Top 5 locations
        if not location_counts.empty:
            insights.append(f"The top location for mentions is **{location_counts.index[0]}** with **{location_counts.iloc[0]:,.0f}** occurrences.")
            if len(location_counts) > 1:
                insights.append(f"The second top location is **{location_counts.index[1]}** with **{location_counts.iloc[1]:,.0f}** occurrences.")
            if len(location_counts) > 2:
                insights.append(f"The third top location is **{location_counts.index[2]}** with **{location_counts.iloc[2]:,.0f}** occurrences.")
        else:
            insights.append("No location data available for analysis.")
    return insights

# --- Main Application Logic ---

st.title("Interactive Media Intelligence Dashboard")

st.markdown("---")

st.header("1. Upload Your CSV File")
st.markdown("Please upload a CSV file with the following columns: `Date`, `Platform`, `Sentiment`, `Location`, `Engagements`, `Media Type`.")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

# Initialize session state for cleaned_data and file_name if they don't exist
if 'cleaned_data' not in st.session_state:
    st.session_state['cleaned_data'] = pd.DataFrame()
if 'file_name' not in st.session_state:
    st.session_state['file_name'] = ""

df = pd.DataFrame() # Initialize df outside the if block

if uploaded_file is not None:
    # Read CSV
    try:
        # Use io.BytesIO to read the uploaded file as a file-like object
        df = pd.read_csv(io.BytesIO(uploaded_file.getvalue()))
        st.session_state['file_name'] = uploaded_file.name
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        df = pd.DataFrame()

    # Clean data
    if not df.empty:
        cleaned_df, cleaning_error = clean_data(df.copy())
        if cleaning_error:
            st.error(cleaning_error)
            st.session_state['cleaned_data'] = pd.DataFrame() # Clear data on error
        else:
            st.session_state['cleaned_data'] = cleaned_df
            st.success(f"Selected: **{st.session_state['file_name']}**")
            st.markdown("---")
            st.header("2. Data Cleaning Summary")
            st.markdown("""
                Data has been successfully cleaned:
                * 'Date' column converted to datetime format (invalid dates filtered out).
                * Missing 'Engagements' values filled with 0.
                * Column names normalized to lowercase and underscores (e.g., 'Media Type' to 'media_type').
            """)
            st.info(f"Successfully processed **{len(cleaned_df)}** valid rows.")
    else:
        st.session_state['cleaned_data'] = pd.DataFrame() # Clear data if initial df is empty
else:
    # If no file is uploaded (or cleared), ensure data and filename are reset
    if st.session_state['file_name'] != "":
        st.session_state['file_name'] = ""
        st.session_state['cleaned_data'] = pd.DataFrame()


st.markdown("---")

# --- 3. Interactive Charts Section ---
if not st.session_state['cleaned_data'].empty:
    cleaned_df = st.session_state['cleaned_data']
    st.header("3. Interactive Media Intelligence Charts")

    # Chart 1: Sentiment Breakdown (Pie Chart)
    st.subheader("Sentiment Breakdown")
    sentiment_counts = cleaned_df['sentiment'].value_counts().reset_index()
    sentiment_counts.columns = ['sentiment', 'count']
    fig_sentiment = px.pie(
        sentiment_counts,
        values='count',
        names='sentiment',
        title='Distribution of Sentiments',
        color_discrete_sequence=['#007BFF', '#E91E63', '#6A1B9A', '#1DE9B6'], # Blue, Pink, Purple, Teal
        hole=0.4 # Donut chart
    )
    fig_sentiment.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#FFFFFF', width=1)))
    fig_sentiment.update_layout(
        font=dict(family='Poppins, sans-serif'),
        title_font_color="#007BFF", # Blue title
        margin=dict(t=50, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="right", x=1)
    )
    st.plotly_chart(fig_sentiment, use_container_width=True)
    st.markdown("**Top Insights:**")
    for insight in generate_insights('sentiment', cleaned_df):
        st.markdown(f"- {insight}")
    st.markdown("---")

    # Chart 2: Engagement Trend over time (Line Chart)
    st.subheader("Engagement Trend over Time")
    daily_engagements = cleaned_df.groupby(cleaned_df['date'].dt.date)['engagements'].sum().reset_index()
    daily_engagements.columns = ['date', 'engagements']
    fig_engagement = px.line(
        daily_engagements,
        x='date',
        y='engagements',
        title='Total Engagements Over Time',
        markers=True,
        line_shape='spline', # Smooth line
        color_discrete_sequence=['#E91E63'] # Pink
    )
    fig_engagement.update_layout(
        font=dict(family='Poppins, sans-serif'),
        title_font_color="#E91E63", # Pink title
        xaxis_title="Date",
        yaxis_title="Total Engagements",
        margin=dict(t=50, b=80, l=50, r=20),
        hovermode="x unified"
    )
    st.plotly_chart(fig_engagement, use_container_width=True)
    st.markdown("**Top Insights:**")
    for insight in generate_insights('engagement_trend', cleaned_df):
        st.markdown(f"- {insight}")
    st.markdown("---")

    # Chart 3: Platform Engagements (Bar Chart)
    st.subheader("Platform Engagements")
    platform_engagements = cleaned_df.groupby('platform')['engagements'].sum().reset_index()
    platform_engagements.columns = ['platform', 'engagements']
    platform_engagements = platform_engagements.sort_values('engagements', ascending=False)
    fig_platform = px.bar(
        platform_engagements,
        x='platform',
        y='engagements',
        title='Total Engagements by Platform',
        color_discrete_sequence=['#007BFF'] # Blue
    )
    fig_platform.update_layout(
        font=dict(family='Poppins, sans-serif'),
        title_font_color="#007BFF", # Blue title
        xaxis_title="Platform",
        yaxis_title="Total Engagements",
        margin=dict(t=50, b=60, l=50, r=20)
    )
    st.plotly_chart(fig_platform, use_container_width=True)
    st.markdown("**Top Insights:**")
    for insight in generate_insights('platform_engagements', cleaned_df):
        st.markdown(f"- {insight}")
    st.markdown("---")

    # Chart 4: Media Type Mix (Pie Chart)
    st.subheader("Media Type Mix")
    media_type_counts = cleaned_df['media_type'].value_counts().reset_index()
    media_type_counts.columns = ['media_type', 'count']
    fig_media_type = px.pie(
        media_type_counts,
        values='count',
        names='media_type',
        title='Distribution of Media Types',
        color_discrete_sequence=['#E91E63', '#F48FB1', '#FFEBEE', '#C2185B', '#880E4F'], # Shades of Pink
        hole=0.4
    )
    fig_media_type.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#FFFFFF', width=1)))
    fig_media_type.update_layout(
        font=dict(family='Poppins, sans-serif'),
        title_font_color="#E91E63", # Pink title
        margin=dict(t=50, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="right", x=1)
    )
    st.plotly_chart(fig_media_type, use_container_width=True)
    st.markdown("**Top Insights:**")
    for insight in generate_insights('media_type_mix', cleaned_df):
        st.markdown(f"- {insight}")
    st.markdown("---")

    # Chart 5: Top 5 Locations (Bar Chart)
    st.subheader("Top 5 Locations")
    top_locations = cleaned_df['location'].value_counts().head(5).reset_index()
    top_locations.columns = ['location', 'count']
    fig_locations = px.bar(
        top_locations,
        x='location',
        y='count',
        title='Top 5 Locations by Mentions',
        color_discrete_sequence=['#007BFF'] # Blue
    )
    fig_locations.update_layout(
        font=dict(family='Poppins, sans-serif'),
        title_font_color="#007BFF", # Blue title
        xaxis_title="Location",
        yaxis_title="Mentions",
        margin=dict(t=50, b=60, l=50, r=20)
    )
    st.plotly_chart(fig_locations, use_container_width=True)
    st.markdown("**Top Insights:**")
    for insight in generate_insights('top_locations', cleaned_df):
        st.markdown(f"- {insight}")
    st.markdown("---")

else:
    st.info("Upload a CSV file to see the interactive dashboard.")
  
