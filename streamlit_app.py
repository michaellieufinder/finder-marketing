import os
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import pandas as pd
import requests as re

access_token = os.getenv("FACEBOOK_API_KEY")

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

# Initialize an empty list for data
data_frames = []

params = {
    'date_preset': 'last_7d',
    'level': 'ad',
    'fields': 'campaign_name, spend, impressions, inline_link_clicks',
    'action_report_time': 'impression',
    'action_attribution_windows': '1d_click',
    'time_increment': 1
}

response = re.get("https://graph.facebook.com/v20.0/act_1385837205024797/insights", headers=headers, params=params)

if response.status_code == 200:
    report = response.json()
    df = pd.json_normalize(report.get('data', []))
    data_frames.append(df)

    try:
        while 'next' in report.get('paging', {}):
            next_url = report['paging']['next']
            response = re.get(next_url, headers=headers)
            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
                break
            report = response.json()
            df = pd.json_normalize(report.get('data', []))
            data_frames.append(df)
    except KeyError:
        print("Finished looping through the pages")
else:
    print(f"Failed to fetch data: {response.status_code} - {response.text}")

# Concatenate all data into a single DataFrame
master_df = pd.concat(data_frames, ignore_index=True)
master_df = master_df.fillna(0)
# Rename and drop columns in one line
master_df = master_df.rename(columns={"inline_link_clicks": "clicks", "date_start": "date"}).drop(columns=["date_stop"])

# Show title and description.
st.title("👀 Finder Marketing Assistant (work-in-progress)")
st.write("This tool is designed to help marketers at Finder Australia analyze and understand their Facebook creative performance data. By leveraging OpenAI's capabilities, marketers can ask specific questions about their ad campaigns and receive insights based on key metrics like spend, impressions, and clicks. The tool simplifies data exploration, enabling quick decision-making and strategy optimization for campaigns.")
st.write("Terms & Conditions:")
st.write("This tool processes only the last 7 days of Facebook creative data. For comprehensive analysis or historical trends beyond this period, additional data integration may be required. Insights are based on the accuracy and availability of data provided through the Facebook API.")
st.write("Ask a question about your dataset:")

# Set up OpenAI API key
# Fetch the API key
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)

# Display the dataset for context (optional)
if st.checkbox("Show dataset"):
    st.write(master_df)  # Replace 'master_df' with your actual DataFrame

# Function to interact with OpenAI
def ask_openai_with_data(question, df):
    # Summarize the dataset as context
    dataset_summary = df.describe(include='all').to_string()
    prompt = f"""
    You are a data analysis expert. Here is a dataset summary:
    {dataset_summary}

    Now, answer the following question based on this dataset:
    {question}
    """

    # Call OpenAI API
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "developer",
                "content": [{
                    "type": "text",
                    "text":
                        "You are a data analysis tool specialising in analysing marketing data. Don't recommend data analysis software and provide short concise answers on exactly what is being asked."
                }],
            },
            {
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": prompt,
                    }]
            }
        ],
        model="gpt-4o",
    )

    # Extract and return the AI's response
    return chat_completion.choices[0].message.content

# Create a form for user input
with st.form(key="query_form"):
    user_question = st.text_input("Enter your question:")
    submit_button = st.form_submit_button(label="Submit")

# Handle form submission
if submit_button:
    st.write("Analyzing your question...")
    try:
        answer = ask_openai_with_data(user_question, master_df)
        st.write("Answer:")
        st.write(answer)
    except Exception as e:
        st.error(f"An error occurred: {e}")

