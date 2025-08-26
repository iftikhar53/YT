"""
Streamlit App: AI Topic & Content Generator (OpenRouter API Ready)

Features:
- Input niche, number of topics, script word count.
- User can dynamically enter their OpenRouter API key in the UI.
- Uses OpenRouter API to generate:
   * Topic ideas
   * Script (word-limited)
   * SEO pack (titles, description, keywords, tags, hashtags)
   * Thumbnail prompts
- UI-based output in Streamlit
- Download results as JSON or Markdown

Setup:
1. Save this file as `app.py` in a GitHub repo.
2. Install dependencies: `pip install streamlit requests`
3. Run with: `streamlit run app.py`
"""

import streamlit as st
import requests
import json
import time
import hashlib

# ---------------- Helpers ----------------
def call_openrouter(prompt: str, api_key: str, model: str = "openrouter-gpt-4", max_tokens: int = 512, temperature: float = 0.7):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    resp = requests.post("https://api.openrouter.ai/v1/chat/completions", headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"OpenRouter API error {resp.status_code}: {resp.text}")
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def slugify(text: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")


def approx_trim(text: str, word_target: int) -> str:
    words = text.split()
    return " ".join(words[:word_target]) if len(words) > word_target else text

# ---------------- Prompt Templates ----------------
def prompt_topics(niche, n):
    return f"Generate {n} unique, clickable video topic ideas for niche: '{niche}'. Return as a numbered list only."

def prompt_script(topic, words):
    return f"Write a {words}-word YouTube narration script on: '{topic}'. Conversational tone, intro, body, conclusion."

def prompt_seo(topic):
    return (
        f"For topic '{topic}', generate an SEO pack:\n"
        "1) 3-5 YouTube titles (under 70 chars)\n"
        "2) Short description (under 150 chars)\n"
        "3) Long description (200-300 words)\n"
        "4) 100 keywords (comma-separated)\n"
        "5) 50 hashtags (space-separated)\n"
    )

def prompt_thumbnails(topic):
    return f"Give 6 short AI thumbnail prompts for topic: '{topic}', cinematic style, 16:9 aspect ratio."

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="AI Topic Tool", layout="wide")
st.title("🎥 AI Topic, Script & SEO Generator (OpenRouter API)")

with st.sidebar:
    st.header("⚙️ Settings")
    niche = st.text_input("Enter niche", "fitness for beginners")
    num_topics = st.number_input("Number of topics", 1, 20, 5)
    words = st.number_input("Words per script", 100, 2000, 300)
    api_key = st.text_input("Enter OpenRouter API Key", type="password")
    model_name = st.text_input("Model Name", "openrouter-gpt-4")
    run_btn = st.button("🚀 Generate")

if run_btn and niche and api_key:
    with st.spinner("Generating with OpenRouter AI..."):
        output = {"niche": niche, "generated_at": time.ctime(), "topics": []}

        # 1) Generate topics
        raw_topics = call_openrouter(prompt_topics(niche, num_topics), api_key, model=model_name, max_tokens=256)
        topics = [line.split(".", 1)[-1].strip() if line[0].isdigit() else line for line in raw_topics.splitlines() if line.strip()]
        topics = topics[:num_topics]

        # 2) For each topic generate content
        for t in topics:
            entry = {"topic": t}
            try:
                script_raw = call_openrouter(prompt_script(t, words), api_key, model=model_name, max_tokens=800)
                entry["script"] = approx_trim(script_raw, words)
            except Exception as e:
                entry["script"] = f"[Error: {e}]"

            try:
                entry["seo"] = call_openrouter(prompt_seo(t), api_key, model=model_name, max_tokens=1000)
            except Exception as e:
                entry["seo"] = f"[Error: {e}]"

            try:
                entry["thumbnails"] = call_openrouter(prompt_thumbnails(t), api_key, model=model_name, max_tokens=400)
            except Exception as e:
                entry["thumbnails"] = f"[Error: {e}]"

            output["topics"].append(entry)

    # ---------------- Display ----------------
    st.success("✅ Generation Complete!")

    for idx, t in enumerate(output["topics"], 1):
        with st.expander(f"📌 Topic {idx}: {t['topic']}"):
            st.subheader("Script")
            st.write(t["script"])
            st.subheader("SEO Pack")
            st.text(t["seo"])
            st.subheader("Thumbnail Prompts")
            st.text(t["thumbnails"])

    # ---------------- Download Buttons ----------------
    st.download_button(
        "⬇️ Download JSON",
        data=json.dumps(output, ensure_ascii=False, indent=2),
        file_name=f"{slugify(niche)}_output.json",
        mime="application/json"
    )

    st.download_button(
        "⬇️ Download Markdown",
        data="\n\n".join([f"# {t['topic']}\n\n## Script\n{t['script']}\n\n## SEO\n{t['seo']}\n\n## Thumbnails\n{t['thumbnails']}" for t in output['topics']]),
        file_name=f"{slugify(niche)}_output.md",
        mime="text/markdown"
    )
