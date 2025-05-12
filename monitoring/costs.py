import streamlit as st
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
headers = {
    "Authorization": f"Bearer {api_key}"
}

# Streamlit app
st.title("OpenAI API Cost Dashboard")

# Date range selector
start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
end_date = st.date_input("End Date", datetime.now())

# Fetch data from OpenAI API
@st.cache_data(ttl=3600)  # Cache the data for 1 hour
def fetch_usage_data(start_date, end_date):
    usage_url = f"https://api.openai.com/v1/usage?start_date={start_date}&end_date={end_date}"
    response = requests.get(usage_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None

usage_data = fetch_usage_data(start_date, end_date)

if usage_data:
    try:
        import pandas as pd
        # Process data
        df = pd.DataFrame(usage_data['data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        # Total cost
        total_cost = df['cost'].sum()
        st.metric("Total Cost", f"${total_cost:.2f}")

        # Daily cost chart
        st.subheader("Daily Cost")
        daily_cost = df.groupby(df['timestamp'].dt.date)['cost'].sum().reset_index()
        fig, ax = plt.subplots()
        ax.bar(daily_cost['timestamp'], daily_cost['cost'])
        ax.set_xlabel("Date")
        ax.set_ylabel("Cost ($)")
        st.pyplot(fig)

        # Cost by model
        st.subheader("Cost by Model")
        model_cost = df.groupby('model')['cost'].sum().sort_values(ascending=False)
        st.bar_chart(model_cost)

        # Raw data
        st.subheader("Raw Data")
        st.dataframe(df)
    except AttributeError as e:
        st.error(f"An error occurred while processing the data: {str(e)}")
        st.write("This might be due to an issue with the pandas library. Please check your environment and dependencies.")
else:
    st.write("No data available. Please check your API key and date range.")