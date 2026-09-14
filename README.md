# 🤖 JARVIS Career Agent

> An AI-powered career agent that searches live job opportunities, analyzes a candidate's resume, matches skills with job requirements, ranks opportunities, and takes action after user approval.

## 🚀 What is JARVIS?

JARVIS Career Agent is an AI agent designed to help students find relevant internships and software development opportunities.

Unlike a traditional chatbot, JARVIS doesn't simply recommend jobs.

It performs a multi-step workflow:

User Input → Resume Analysis → Live Job Search → Job Analysis → Candidate Matching → Ranking → Recommendation → User Approval → Action

## ✨ Features

- 📄 Resume parsing and skill extraction
- 🎯 Understands job role and preferred location
- 🌐 Searches live job opportunities
- 🔎 Analyzes job information and requirements
- 🧩 Matches resume skills with job requirements
- 📊 Calculates match scores
- 🏆 Ranks job opportunities
- 🤖 Makes a final recommendation
- ⚡ Takes action after user approval
- 🔗 Opens the selected application page

## 🧠 Why is it an AI Agent?

JARVIS follows an autonomous multi-step decision workflow.

It:

1. Observes user requirements
2. Reads the candidate's resume
3. Searches external sources for opportunities
4. Collects and analyzes job information
5. Compares candidate skills with job requirements
6. Calculates a match score
7. Ranks available opportunities
8. Makes a recommendation
9. Requests user approval
10. Takes an external action

This makes JARVIS more than a simple question-answering chatbot.

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │       USER          │
                    │ Job + Location +    │
                    │ Resume              │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   JARVIS AGENT      │
                    │     agent.py        │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
      ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
      │   Resume    │   │  Job Search │   │ User Intent │
      │   Analysis  │   │   Sources   │   │   Analysis  │
      └──────┬──────┘   └──────┬──────┘   └─────────────┘
             │                 │
             ▼                 ▼
      ┌─────────────────────────────────┐
      │       Job + Candidate Data      │
      └────────────────┬────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Candidate ↔ Job  │
              │     Matching     │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  Match Scoring   │
              │   & Ranking      │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Recommendation       │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ User Approval    │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Open Application │
              │     Website      │
              └──────────────────┘