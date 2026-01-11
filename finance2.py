import streamlit as st
import requests
from datetime import datetime, timedelta
import os
from pytrends.request import TrendReq

# YouTube API Key from environment variable (for better security)
API_KEY = os.getenv("YOUTUBE_API_KEY")  # Set your API key in the environment variables
if not API_KEY:
    st.error("API Key is missing. Please set the API key in the environment variables.")
    st.stop()

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("Trending YouTube Finance Topics Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)

# Initialize pytrends for Google Trends
pytrends = TrendReq(hl='en-US', tz=360)

# Fetch trending Google finance topics
pytrends.build_payload(['finance', 'stocks', 'bitcoin', 'economy'], cat=0, timeframe='now 7-d', geo='', gprop='')
related_queries = pytrends.related_queries()
# Extract trending queries related to finance
trending_queries = related_queries['finance']['top']

# Extract just the keywords for simplicity
trending_keywords = [query['query'] for query in trending_queries]

# Add more specific finance-related topics for good coverage
additional_keywords = [
    "Stock Market News", "Cryptocurrency Trends", "Bitcoin Price Prediction", 
    "Investment Tips 2026", "Financial Crisis Update", "Real Estate Trends 2026", 
    "Venture Capital 2026", "Startups and Investment", "Financial News Today", 
    "Market Crash", "Stock Market 2026", "Cryptocurrency Investment", 
    "Economic Collapse 2026", "Best Stocks to Buy Now", "Personal Finance Tips", 
    "Financial Freedom", "Retirement Planning 2026", "Passive Income Strategies", 
    "Real Estate Investment Tips", "Economy Recovery 2026", "Saving for Retirement"
]

# Combine trending queries with additional static ones
keywords = trending_keywords + additional_keywords

# Fetch Data Button
if st.button("Fetch Data"):
    try:
        # Calculate date range
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat("T") + "Z"
        all_results = []

        # Iterate over the list of keywords
        for keyword in keywords:
            st.write(f"Searching for keyword: {keyword}")

            # Define search parameters
            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",  # Order by view count to simulate trending
                "publishedAfter": start_date,
                "maxResults": 5,
                "key": API_KEY,
            }

            # Fetch video data
            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()

            # Check if "items" key exists
            if "items" not in data or not data["items"]:
                st.warning(f"No videos found for keyword: {keyword}")
                continue

            videos = data["items"]
            video_ids = [video["id"]["videoId"] for video in videos if "id" in video and "videoId" in video["id"]]
            channel_ids = [video["snippet"]["channelId"] for video in videos if "snippet" in video and "channelId" in video["snippet"]]

            if not video_ids or not channel_ids:
                st.warning(f"Skipping keyword: {keyword} due to missing video/channel data.")
                continue

            # Fetch video statistics
            stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            if "items" not in stats_data or not stats_data["items"]:
                st.warning(f"Failed to fetch video statistics for keyword: {keyword}")
                continue

            # Fetch channel statistics
            channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()

            if "items" not in channel_data or not channel_data["items"]:
                st.warning(f"Failed to fetch channel statistics for keyword: {keyword}")
                continue

            stats = stats_data["items"]
            channels = channel_data["items"]

            # Collect results
            for video, stat, channel in zip(videos, stats, channels):
                title = video["snippet"].get("title", "N/A")
                description = video["snippet"].get("description", "")[:200]
                video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                views = int(stat["statistics"].get("viewCount", 0))
                subs = int(channel["statistics"].get("subscriberCount", 0))

                # Only include channels with fewer than 3,000 subscribers (this can be modified or made configurable)
                if subs < 3000:
                    all_results.append({
                        "Title": title,
                        "Description": description,
                        "URL": video_url,
                        "Views": views,
                        "Subscribers": subs
                    })

        # Display results
        if all_results:
            st.success(f"Found {len(all_results)} results across all keywords!")
            for result in all_results:
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}"
                )
                st.write("---")
        else:
            st.warning("No results found for channels with fewer than 3,000 subscribers.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
