import streamlit as st
from agent import JarvisAgent
import tempfile
import os

st.set_page_config(
    page_title="JARVIS Career Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 JARVIS Career Agent")
st.write("AI-powered career assistant that finds and ranks job opportunities.")

st.divider()

query = st.text_input(
    "What type of job are you looking for?",
    placeholder="e.g. Software Development Internship"
)

location = st.text_input(
    "Preferred location",
    placeholder="e.g. Mumbai"
)

resume = st.file_uploader(
    "Upload your resume",
    type=["pdf", "docx"]
)

if st.button("🚀 Find Jobs"):

    if not query or not location or not resume:
        st.warning("Please enter the job role, location, and upload your resume.")
    else:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(resume.name)[1]
        ) as temp_file:

            temp_file.write(resume.read())
            resume_path = temp_file.name

        st.info("🤖 JARVIS is analyzing your resume and searching for jobs...")

        try:
            agent = JarvisAgent()

            result = agent.run(
                query,
                location,
                resume_path
            )

            jobs = result.get("jobs", [])

            if not jobs:
                st.error(
                    result.get(
            "message",
            "JARVIS could not complete the job search."
                    )
            )

            elif not jobs:
                st.warning("No suitable jobs found.")
            else:

                st.success(f"Found {len(jobs)} suitable opportunities.")

                for i, job in enumerate(jobs[:5], 1):

                    score = job.get("score", 0)

                    st.subheader(f"#{i} {job.get('title', 'Unknown title')}")
                    st.write(f"🏢 **Company:** {job.get('company', 'Unknown')}")
                    st.write(f"📍 **Location:** {job.get('location', 'Not specified')}")
                    st.write(f"⭐ **Match Score:** {score}%")
                    st.write(f"🎯 **Recommendation:** {job.get('recommendation', 'REVIEW')}")

                    if job.get("matched_skills"):
                        st.write("✅ **Matching skills:** " + ", ".join(job["matched_skills"][:5]))

                    if job.get("missing_skills"):
                        st.write("⚠️ **Skill gaps:** " + ", ".join(job["missing_skills"][:3]))

                    if job.get("url"): st.link_button( "🔗 Apply", job["url"])

                    st.divider()

        except Exception as e:
            st.error(f"JARVIS encountered an error: {e}")

        finally:
            try:
                os.remove(resume_path)
            except:
                pass