import streamlit as st
import pandas as pd
from youtubesearchpython import VideosSearch
import random

# Function to find topics
def find_topics(niche, num_topics=10):
    videos = VideosSearch(niche, limit=50).result()["result"]

    topic_list = []
    for v in videos:
        title = v["title"]
        views_text = v.get("viewCount", {}).get("text", "0 views")
        views = int(views_text.replace("views", "").replace(",", "").strip()) if views_text else 0
        duration = v.get("duration", "0:00")

        # CTR score (proxy: title length + random boost)
        ctr_score = len(title.split()) + random.randint(1, 5)

        # AVD score (proxy: video duration length)
        avd_score = len(duration.split(":"))  

        topic_list.append({
            "Title": title,
            "Views": views,
            "Duration": duration,
            "CTR_Score": ctr_score,
            "AVD_Score": avd_score,
            "Total_Score": ctr_score + avd_score
        })

    # Sort by CTR + AVD combined
    sorted_topics = sorted(topic_list, key=lambda x: x["Total_Score"], reverse=True)

    return pd.DataFrame(sorted_topics[:num_topics])


# ---------------- Streamlit UI ----------------
st.title("🎯 YouTube High CTR & AVD Topic Finder")
st.write("Find viral video topics in your selected niche")

# User Inputs
niche = st.text_input("Enter your niche/keyword:", "India vs USA geopolitics")
num_topics = st.number_input("How many topics do you want?", min_value=5, max_value=50, value=10)

if st.button("Find Topics"):
    df = find_topics(niche, num_topics)
    st.success("✅ Topics Found!")
    st.dataframe(df)

    # Download CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download as CSV", csv, "youtube_topics.csv", "text/csv")
