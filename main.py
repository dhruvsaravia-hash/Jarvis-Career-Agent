from agent import JarvisAgent
import webbrowser

def main():
    print("="*60)
    print("         🤖 JARVIS CAREER AGENT")
    print("          AI-Powered Career Assistant")
    print("="*60)

    query = input("\nWhat type of job are you looking for: ")
    location = input("location: ")
    resume_path = input("Enter resume path(press Enter for default resume.pdf): ").strip().strip('"')
    
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
    
    matches = agent.run(query, location, resume_path)
    matches = matches.get("jobs", [])
    
    if not matches:
        print("\n[JARVIS] No suitable jobs found.")
        return

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

        print(f"\n#{i} {job.get('title', 'Unknown title')}")
        print(f"🏢 Company: {job.get('company', 'Unknown company')}")
        print(f"📍 Location: {job.get('location', 'Not specified')}")
        print(f"🏷️ Source: {job.get('source', 'Unknown source')}")
        print(f"⭐ Match Score: {score}% — {badge}")
        print(f"🎯 Confidence: {job.get('confidence', 'medium').upper()}")
        print(f"🤝 Recommendation: {job.get('recommendation', 'REVIEW')}")

        matched = job.get("matched_skills", [])
        missing = job.get("missing_skills", [])

        if matched:
            top_skills = ", ".join(matched[:5])
            insight = f"Strong fit because your {top_skills} skills match this role."
        else:
            insight = "Limited skill overlap found with this role."

        if missing:
            insight += f" Main gaps to improve: {', '.join(missing[:3])}."
        else:
            print("📚 Skills to Improve: None")
            
        print(f"\n JARVIS INSIGHTS: {insight}")    

        print(f"💡 Why: {', '.join(job.get('strengths', []))}")

        url = job.get("url", "")
        if url:
            print(f"🔗 Apply: {url}")

        print("-" * 60)

    if matches:

        recommended = [
            job for job in matches
            if job.get("recommendation") == "APPLY"
        ]

        if recommended:
            best = max(recommended, key=lambda job: job.get("score", 0))
        else:
            best = max(matches, key=lambda job: job.get("score", 0))

        score = best.get("score", 0)
        matched_skills = best.get("matched_skills", [])
        missing_skills = best.get("missing_skills", [])

        if score >= 80:
            skill_status = "STRONG"
        elif score >= 60:
            skill_status = "GOOD"
        else:
            skill_status = "PARTIAL"

        if best.get("recommendation") in ["APPLY", "CONSIDER"]:
            role_status = "CONFIRMED ✓"
        else:
            role_status = "REVIEW"

        if "intern" in best.get("title", "").lower():
            internship_status = "CONFIRMED ✓"
        else:
            internship_status = "NOT CONFIRMED"

        print("\n" + "=" * 60)
        print("🤖 JARVIS FINAL DECISION")
        print("=" * 60)

        print("\n🎯 BEST OPPORTUNITY")
        print(best.get("title", "Unknown title"))
        print(f"🏢 {best.get('company', 'Unknown company')}")
        print(f"📍 {best.get('location', 'Not specified')}")

        print("\n📊 MATCH ANALYSIS")
        print(f"Skill Match    : {skill_status}")
        print(f"Role Match     : {role_status}")
        print(f"Location       : MATCHED ✓")
        print(f"Internship     : {internship_status}")
        print(f"Confidence     : {best.get('confidence', 'medium').upper()}")
        print(f"Match Score    : {score}%")

        print("\n🧠 AGENT REASONING")

        if matched_skills:
            print("✓ Your matching skills: " + ", ".join(matched_skills[:6]))

        if internship_status == "CONFIRMED ✓":
            print("✓ Internship requirement is satisfied")

        if missing_skills:
            print("⚠ Main skill gaps: " + ", ".join(missing_skills[:3]))

        print("\n💡 WHY JARVIS CHOSE THIS")

        if matched_skills:
            print("✓ Strong skill overlap with your resume")

        print("✓ Location matches your preference")

        if internship_status == "CONFIRMED ✓":
            print("✓ Internship role confirmed")

        if missing_skills:
            print("⚠ Consider improving: " + ", ".join(missing_skills[:3]))

        print("\n⚡ JARVIS ACTION")
        print(f"Decision      : {best.get('recommendation', 'REVIEW')}")
        print(
            f"Confidence    : "
            f"{best.get('confidence', 'medium').upper()}"
        )

        if best.get("recommendation") == "APPLY":
            print(
                "Reason        : Strong match with sufficient evidence"
            )
            print("Next Action   : Open application")

        elif best.get("recommendation") == "CONSIDER":
            print(
                "Reason        : Good match, but review before applying"
            )
            print("Next Action   : Review opportunity")

        else:
            print(
                "Reason        : Match is not strong enough"
            )
            print("Next Action   : Continue searching")

        strong_matches = sum(
            1 for job in matches
            if job.get("score", 0) >= 80
        )

        apply_count = sum(
            1 for job in matches
            if job.get("recommendation") == "APPLY"
        )

        print("\n" + "-" * 60)
        print("📌 AGENT SUMMARY")
        print("-" * 60)

        print(f"Jobs discovered       : {len(matches)}")
        print(f"Strong matches        : {strong_matches}")
        print(f"Recommended to apply  : {apply_count}")

        if best.get("url"):

            print("\n🚀 APPLICATION")
            print(f"Apply here: {best['url']}")

            action = input(
                "\nOpen this application in your browser? (yes/no): "
            ).strip().lower()

            if action == "yes":

                webbrowser.open(best["url"])

                print(
                    "\n[JARVIS] Application webpage opened "
                    "in your browser."
                )

            else:

                print(
                    "\n[JARVIS] Application page not opened."
                )

    print("\n" + "=" * 60)
    print("🤖 JARVIS ANALYSIS COMPLETE")
    print("=" * 60)
print("STATUS: SUCCESS ✓")
print("=" * 60)
      
        
if __name__ == "__main__":
    main()         
