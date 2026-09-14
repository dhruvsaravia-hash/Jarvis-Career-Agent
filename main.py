from agent import JarvisAgent
import webbrowser


def main():
    print("=" * 60)
    print("         🤖 JARVIS CAREER AGENT")
    print("          AI-Powered Career Assistant")
    print("=" * 60)

    query = input("\nWhat type of job are you looking for: ").strip()
    location = input("location: ").strip()

    resume_path = (
        input(
            "Enter resume path(press Enter for default resume.pdf): "
        )
        .strip()
        .strip('"')
    )

    if not resume_path:
        resume_path = "resume.pdf"

    print("\n" + "-" * 60)
    print("🎯 JOB SEARCH")
    print("-" * 60)
    print(f"Role     : {query}")
    print(f"Location : {location}")
    print(f"Resume   : {resume_path}")

    agent = JarvisAgent()

    print("\n" + "-" * 60)
    print("🧠 PHASE 1 — UNDERSTANDING REQUEST")
    print("-" * 60)
    print("🤖 JARVIS is activating...")
    print("✓ Understanding job requirements")
    print("✓ Understanding preferred location")
    print("✓ Preparing candidate analysis")

    result = agent.run(
        query,
        location,
        resume_path
    )

    if not result.get("success", False):
        print(
            "\n[JARVIS] "
            + result.get(
                "message",
                "Unable to complete the job search."
            )
        )
        return

    matches = result.get("jobs", [])

    if not matches:
        print("\n[JARVIS] No suitable jobs found.")
        return

    # =========================================================
    # TOP JOB MATCHES
    # =========================================================

    print("\n" + "-" * 60)
    print("🏆 TOP JOB MATCHES")
    print("-" * 60)

    for i, job in enumerate(matches[:5], 1):

        score = job.get("score", 0)

        if score >= 80:
            badge = "🔥 STRONG MATCH"
        elif score >= 60:
            badge = "🟡 GOOD MATCH"
        else:
            badge = "⚪ PARTIAL MATCH"

        print(
            f"\n#{i} "
            f"{job.get('title', 'Unknown title')}"
        )

        print(
            f"🏢 Company: "
            f"{job.get('company', 'Unknown company')}"
        )

        print(
            f"📍 Location: "
            f"{job.get('location', 'Not specified')}"
        )

        print(
            f"🏷️ Source: "
            f"{job.get('source', 'Unknown source')}"
        )

        print(
            f"⭐ Match Score: "
            f"{score}% — {badge}"
        )

        print(
            f"🎯 Confidence: "
            f"{job.get('confidence', 'medium').upper()}"
        )

        print(
            f"🤝 Recommendation: "
            f"{job.get('recommendation', 'REVIEW')}"
        )

        # -----------------------------------------------------
        # MATCH EVIDENCE
        # -----------------------------------------------------

        matched = job.get(
            "matched_skills",
            []
        )

        missing = job.get(
            "missing_skills",
            []
        )

        matched_count = job.get(
            "matched_skill_count",
            len(matched)
        )

        required_count = job.get(
            "required_skill_count",
            len(matched) + len(missing)
        )

        skill_percentage = job.get(
            "skill_match_percentage",
            0
        )

        print(
            f"   Skill Evidence: "
            f"{matched_count}/{required_count} "
            f"skills matched "
            f"({skill_percentage}%)"
        )

        print(
            f"   Role Match: "
            f"{'YES' if job.get('role_matched') else 'NO'}"
        )

        print(
            f"   Location Match: "
            f"{'YES' if job.get('location_matched') else 'NO'}"
        )

        print(
            f"   Internship: "
            f"{'CONFIRMED' if job.get('internship_confirmed') else 'NOT CONFIRMED'}"
        )

        print(
            f"   Education: "
            f"{'DETECTED' if job.get('education_detected') else 'NOT DETECTED'}"
        )

        # -----------------------------------------------------
        # JARVIS INSIGHTS
        # -----------------------------------------------------

        if matched:
            top_skills = ", ".join(
                matched[:5]
            )

            insight = (
                "Strong fit because your "
                f"{top_skills} skills "
                "match this role."
            )
        else:
            insight = (
                "Limited skill overlap found "
                "with this role."
            )

        if missing:
            insight += (
                " Main gaps to improve: "
                + ", ".join(missing[:3])
                + "."
            )
        else:
            print(
                "📚 Skills to Improve: None"
            )

        print(
            f"\n🧠 JARVIS INSIGHTS: {insight}"
        )

        
        # -----------------------------------------------------
        # FINAL DECISION
        # -----------------------------------------------------

        recommended = [
            job for job in matches
            if job.get("recommendation") == "APPLY"
        ]

        if recommended:
            best = max(
                recommended,
                key=lambda job: job.get("score", 0)
            )
        else:
            best = max(
                matches,
                key=lambda job: job.get("score", 0)
            )

        print("\n" + "=" * 60)
        print("🤖 JARVIS FINAL DECISION")
        print("=" * 60)

        print(f"\n🎯 BEST OPPORTUNITY")
        print(best.get("title", "Unknown title"))
        print(f"🏢 {best.get('company', 'Unknown company')}")
        print(f"📍 {best.get('location', 'Not specified')}")

        print("\n📊 MATCH ANALYSIS")
        print(f"Match Score : {best.get('score', 0)}%")
        print(f"Confidence  : {best.get('confidence', 'medium').upper()}")
        print(f"Recommendation : {best.get('recommendation', 'REVIEW')}")

        print("\n🔎 MATCH EVIDENCE")

        matched_skills = best.get("matched_skills", [])
        missing_skills = best.get("missing_skills", [])

        print(
            f"✓ Skills matched: "
            f"{best.get('matched_skill_count', len(matched_skills))}/"
            f"{best.get('required_skill_count', len(matched_skills) + len(missing_skills))}"
        )

        if matched_skills:
            print("✓ Matching skills: " + ", ".join(matched_skills))

        if missing_skills:
            print("⚠ Skill gaps: " + ", ".join(missing_skills))

        print("\n⚡ JARVIS ACTION")

        recommendation = best.get("recommendation", "REVIEW")

        if recommendation == "APPLY":
            print("Decision    : APPLY")
            print("Next Action : Open application page")

            url = best.get("url", "")

            if url:
                action = input(
                    "\nOpen this application in your browser? (yes/no): "
                ).strip().lower()

                if action == "yes":
                    webbrowser.open(url)
                    print("\n[JARVIS] Application webpage opened.")
                else:
                    print("\n[JARVIS] Application page not opened.")

        elif recommendation == "CONSIDER":
            print("Decision    : CONSIDER")
            print("Next Action : Review opportunity before applying")

        else:
            print("Decision    : REVIEW")
            print("Next Action : Continue searching for stronger matches")

    print("\n" + "=" * 60)
    print("🤖 JARVIS ANALYSIS COMPLETE")
    print("=" * 60)

    print("STATUS: SUCCESS ✓")


if __name__ == "__main__":
    main()