import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI Ticket Assistant",
    layout="wide",
)

st.title("AI Support Ticket Assistant")
st.caption("Natural language queries + anomaly detection for customer support tickets")

tab1, tab2, tab3 = st.tabs(["Ask a Question", "Anomalies", "System Health"])


with tab1:
    st.subheader("Ask anything about the tickets")

    example_questions = [
        "How many tickets are currently open?",
        "Which agent resolved the most tickets this month?",
        "Which agent has the lowest average customer rating?",
        "Show me all Critical tickets not resolved within 12 hours",
        "What is the average customer rating for Technical category tickets?",
        "Are there any anomalies in resolution times this week?",
    ]

    selected_example = st.selectbox(
        "Try an example:",
        [""] + example_questions,
    )

    question = st.text_input(
        "Your question:",
        value=selected_example,
        placeholder="e.g., How many Critical tickets are unresolved?",
    )

    if st.button("Ask", type="primary") and question.strip():
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}/query",
                    json={"question": question},
                    timeout=120,
                )
                response.raise_for_status()
                result = response.json()

                st.success("Answer")
                st.markdown(f"### {result['answer']}")

                with st.expander("Generated SQL"):
                    st.code(result["sql"], language="sql")

                st.caption(f"Rows returned: {result['rows']}")

                if result.get("data") and len(result["data"]) <= 20:
                    with st.expander("Raw data"):
                        st.dataframe(result["data"])

            except requests.exceptions.RequestException as exc:
                st.error(f"API error: {exc}")
            except Exception as exc:
                st.error(f"Unexpected error: {exc}")


with tab2:
    st.subheader("Detected anomalies")

    col1, col2 = st.columns([3, 1])
    with col2:
        severity_filter = st.selectbox(
            "Filter by severity:",
            ["All", "critical", "high", "medium", "low"],
        )

    if st.button("Run detection", type="primary"):
        with st.spinner("Scanning tickets..."):
            try:
                params = {}
                if severity_filter != "All":
                    params["severity"] = severity_filter

                response = requests.get(
                    f"{API_URL}/anomalies",
                    params=params,
                    timeout=120,
                )
                response.raise_for_status()
                result = response.json()

                st.metric(
                    "Total anomalies",
                    result["total_anomalies"],
                )

                if result.get("by_severity"):
                    cols = st.columns(len(result["by_severity"]))
                    for idx, (sev, count) in enumerate(result["by_severity"].items()):
                        cols[idx].metric(sev.capitalize(), count)

                if result["anomalies"]:
                    st.markdown("### Flagged tickets")
                    st.dataframe(
                        [
                            {
                                "ticket_id": a["ticket_id"],
                                "severity": a["severity"],
                                "reason": a["reason"],
                            }
                            for a in result["anomalies"]
                        ],
                        use_container_width=True,
                    )
                else:
                    st.info("No anomalies found for this filter.")

            except requests.exceptions.RequestException as exc:
                st.error(f"API error: {exc}")
            except Exception as exc:
                st.error(f"Unexpected error: {exc}")


with tab3:
    st.subheader("System health")

    if st.button("Check health", type="primary"):
        try:
            response = requests.get(f"{API_URL}/health", timeout=10)
            response.raise_for_status()
            result = response.json()

            status = result["status"]
            if status == "healthy":
                st.success(f"Status: {status.upper()}")
            elif status == "degraded":
                st.warning(f"Status: {status.upper()}")
            else:
                st.error(f"Status: {status.upper()}")

            col1, col2, col3 = st.columns(3)
            col1.metric("Tickets loaded", result["tickets_loaded"])
            col2.metric("LLM provider", result["llm_provider"])
            col3.metric("LLM available", "Yes" if result["llm_available"] else "No")

            st.json(result)

        except requests.exceptions.RequestException as exc:
            st.error(f"API error: {exc}")
            st.caption("Make sure the FastAPI server is running on port 8000.")