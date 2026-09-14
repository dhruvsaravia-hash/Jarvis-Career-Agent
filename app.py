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

st.write(
    "AI-powered career assistant that finds, analyzes "
    "and ranks job opportunities."
)

st.divider()


query = st.text_input(
    "What type of job are you looking for?",
    placeholder="e.g. Data Analytics Internship"
)

location = st.text_input(
    "Preferred location",
    placeholder="e.g. Mumbai"
)

resume = st.file_uploader(
    "Upload your resume",
    type=["pdf", "docx"]
)


if st.button("🚀 Find Jobs", type="primary"):

    # -----------------------------
    # INPUT VALIDATION
    # -----------------------------

    if not query.strip():
        st.warning("Please enter the job role.")
        st.stop()

    if not location.strip():
        st.warning("Please enter your preferred location.")
        st.stop()

    if resume is None:
        st.warning("Please upload your resume.")
        st.stop()


    # -----------------------------
    # SAVE RESUME TEMPORARILY
    # -----------------------------

    resume_path = None

    try:

        suffix = os.path.splitext(resume.name)[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            temp_file.write(resume.getbuffer())
            resume_path = temp_file.name


        # -----------------------------
        # RUN JARVIS
        # -----------------------------

        with st.spinner(
            "🤖 JARVIS is analyzing your resume "
            "and searching live opportunities..."
        ):

            agent = JarvisAgent()

            result = agent.run(
                query.strip(),
                location.strip(),
                resume_path
            )


        # -----------------------------
        # HANDLE FAILURE
        # -----------------------------

        if not result.get("success", False):

            st.error(
                result.get(
                    "message",
                    "JARVIS could not complete the search."
                )
            )

            st.info(
                "Try a broader job title or location."
            )

            st.stop()


        # -----------------------------
        # GET JOBS
        # -----------------------------

        jobs = result.get("jobs", [])

        if not jobs:

            st.warning(
                "JARVIS completed the search but found "
                "no suitable opportunities."
            )

            st.stop()


        st.success(
            f"JARVIS found {len(jobs)} suitable opportunities."
        )


        # -----------------------------
        # BEST JOB
        # -----------------------------

        best = result.get("best_job")

        if best:

            st.subheader("🤖 JARVIS Recommendation")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Best Match",
                    f"{best.get('score', 0)}%"
                )

            with col2:
                st.metric(
                    "Confidence",
                    best.get(
                        "confidence",
                        "medium"
                    ).upper()
                )

            with col3:
                st.metric(
                    "Decision",
                    best.get(
                        "recommendation",
                        "REVIEW"
                    )
                )


            st.write(
                f"### 🎯 {best.get('title', 'Unknown title')}"
            )

            st.write(
                f"**🏢 Company:** "
                f"{best.get('company', 'Unknown')}"
            )

            st.write(
                f"**📍 Location:** "
                f"{best.get('location', 'Not specified')}"
            )


            matched = best.get(
                "matched_skills",
                []
            )

            missing = best.get(
                "missing_skills",
                []
            )


            if matched:

                st.success(
                    "✅ Matching skills: "
                    + ", ".join(matched[:8])
                )


            if missing:

                st.warning(
                    "⚠️ Skill gaps: "
                    + ", ".join(missing[:6])
                )


            if best.get("url"):

                st.link_button(
                    "🚀 Open Application",
                    best["url"]
                )


            st.divider()


        # -----------------------------
        # TOP JOB MATCHES
        # -----------------------------

        st.subheader("🏆 Top Job Matches")


        for i, job in enumerate(jobs[:5], 1):

            score = job.get("score", 0)


            if score >= 80:
                badge = "🔥 Strong Match"

            elif score >= 60:
                badge = "🟡 Good Match"

            else:
                badge = "⚪ Partial Match"


            with st.container(border=True):

                st.markdown(
                    f"### #{i} "
                    f"{job.get('title', 'Unknown title')}"
                )


                col1, col2 = st.columns(2)


                with col1:

                    st.write(
                        f"🏢 **Company:** "
                        f"{job.get('company', 'Unknown')}"
                    )

                    st.write(
                        f"📍 **Location:** "
                        f"{job.get('location', 'Not specified')}"
                    )

                    st.write(
                        f"🏷️ **Source:** "
                        f"{job.get('source', 'Web Search')}"
                    )


                with col2:

                    st.write(
                        f"⭐ **Match:** "
                        f"{score}% — {badge}"
                    )

                    st.write(
                        f"🎯 **Recommendation:** "
                        f"{job.get('recommendation', 'REVIEW')}"
                    )

                    st.write(
                        f"🔎 **Confidence:** "
                        f"{job.get('confidence', 'medium').upper()}"
                    )


                matched = job.get(
                    "matched_skills",
                    []
                )

                missing = job.get(
                    "missing_skills",
                    []
                )


                if matched:

                    st.write(
                        "✅ **Matching skills:** "
                        + ", ".join(matched[:6])
                    )


                if missing:

                    st.write(
                        "⚠️ **Skill gaps:** "
                        + ", ".join(missing[:5])
                    )


                if job.get("url"):

                    st.link_button(
                        "🔗 View / Apply",
                        job["url"]
                    )


        # -----------------------------
        # JARVIS ACTION
        # -----------------------------

        st.divider()

        st.subheader("⚡ JARVIS Action")


        if best and best.get("url"):

            st.write(
                "JARVIS has identified the strongest "
                "opportunity and its application page."
            )

            st.success(
                "Ready for user-approved action."
            )

        else:

            st.info(
                "No application URL was available for "
                "the recommended opportunity."
            )


    # -----------------------------
    # ERROR HANDLING
    # -----------------------------

    except Exception as e:

        st.error(
            f"JARVIS encountered an error: {e}"
        )


    # -----------------------------
    # CLEANUP
    # -----------------------------

    finally:

        if resume_path:

            try:
                os.remove(resume_path)

            except Exception:
                pass