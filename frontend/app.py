
import os
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Enterprise AI Support",
    page_icon="🤖",
    layout="wide"
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "token" not in st.session_state:
    st.session_state.token = ""

if "messages" not in st.session_state:
    st.session_state.messages = []


# --------------------------------------------------
# API FUNCTIONS
# --------------------------------------------------

def headers():
    if st.session_state.token:
        return {
            "Authorization": f"Bearer {st.session_state.token}"
        }
    return {}


def api_get(path):
    return requests.get(
        API + path,
        headers=headers(),
        timeout=30
    )


def api_post(path, **kwargs):
    return requests.post(
        API + path,
        headers=headers(),
        timeout=90,
        **kwargs
    )


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

st.sidebar.title("Enterprise AI Support")

page = st.sidebar.radio(
    "Navigation",
    [
        "AI Assistant",
        "Dashboard",
        "Customers",
        "Orders",
        "Products & Inventory",
        "Support Tickets",
        "Knowledge Documents"
    ]
)

st.sidebar.caption("Demo account: admin / admin123")


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

if not st.session_state.token:

    st.title("Sign in")

    with st.form("login"):

        username = st.text_input("Username", "admin")

        password = st.text_input(
            "Password",
            type="password",
            value="admin123"
        )

        submitted = st.form_submit_button(
            "Sign in",
            type="primary"
        )

    if submitted:

        try:
            r = requests.post(
                API + "/auth/login",
                json={
                    "username": username,
                    "password": password
                },
                timeout=15
            )

            r.raise_for_status()

            st.session_state.token = r.json()["access_token"]

            st.rerun()

        except Exception as e:
            st.error(
                f"Login failed. Is the FastAPI server running? Details: {e}"
            )

    st.stop()


# --------------------------------------------------
# AUTHENTICATED SIDEBAR
# --------------------------------------------------

st.sidebar.success("Authenticated")

if st.sidebar.button("Sign out"):

    st.session_state.token = ""
    st.session_state.messages = []

    st.rerun()


# --------------------------------------------------
# AI ASSISTANT
# --------------------------------------------------

if page == "AI Assistant":

    st.title("🤖 AI Customer Support Assistant")

    st.write(
        "Ask about company policies, orders, customers, "
        "inventory or business performance."
    )

    # Display complete previous conversation
    for m in st.session_state.messages:

        with st.chat_message(m["role"]):

            st.markdown(m["content"])

            # Restore previously saved tables
            if m.get("data"):
                st.dataframe(
                    pd.DataFrame(m["data"]),
                    use_container_width=True
                )

            # Restore sources
            if m.get("sources"):
                st.caption(
                    "Sources: " + ", ".join(m["sources"])
                )

            # Restore routing information
            if m.get("route"):
                st.caption(
                    f"Handled by: {m['route'].upper()}"
                )

    # New question input
    prompt = st.chat_input(
        "Example: Where is order 3? or What is the refund policy?"
    )

    if prompt:

        # Save user question
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response
        with st.chat_message("assistant"):

            with st.spinner(
                "Checking documents and business data..."
            ):

                try:

                    r = api_post(
                        "/chat",
                        json={"question": prompt}
                    )

                    r.raise_for_status()

                    result = r.json()

                    answer = result.get(
                        "answer",
                        "No answer returned."
                    )

                    data = result.get("data", [])

                    sources = [
                        x["source"]
                        for x in result.get("sources", [])
                    ]

                    route = result.get("route", "")

                    # Display answer
                    st.markdown(answer)

                    # Display table
                    if data:

                        st.dataframe(
                            pd.DataFrame(data),
                            use_container_width=True
                        )

                    # Display sources
                    if sources:

                        st.caption(
                            "Sources: " + ", ".join(sources)
                        )

                    # Display route
                    st.caption(
                        f"Handled by: {route.upper()}"
                    )

                    # Save complete assistant response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "data": data,
                        "sources": sources,
                        "route": route
                    })

                except Exception as e:

                    error_message = f"Request failed: {e}"

                    st.error(error_message)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message,
                        "data": [],
                        "sources": [],
                        "route": ""
                    })


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

elif page == "Dashboard":

    st.title("📊 Operations Dashboard")

    try:

        orders = api_get("/orders")
        orders.raise_for_status()

        products = api_get("/products")
        products.raise_for_status()

        odf = pd.DataFrame(orders.json())
        pdf = pd.DataFrame(products.json())

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total orders",
            len(odf)
        )

        c2.metric(
            "Recorded order value",
            f"₹{odf['total_amount'].sum():,.0f}"
            if len(odf) else "₹0"
        )

        c3.metric(
            "Low-stock products",
            int((pdf["stock"] < 5).sum())
            if len(pdf) else 0
        )

        st.subheader("Order status")

        if len(odf):
            st.bar_chart(
                odf["status"].value_counts()
            )

        st.subheader("Inventory")

        if len(pdf):
            st.bar_chart(
                pdf.set_index("name")["stock"]
            )

    except Exception as e:
        st.error(str(e))


# --------------------------------------------------
# CUSTOMERS
# --------------------------------------------------

elif page == "Customers":

    st.title("👥 Customers")

    try:

        r = api_get("/customers")
        r.raise_for_status()

        st.dataframe(
            pd.DataFrame(r.json()),
            use_container_width=True
        )

    except Exception as e:
        st.error(str(e))


# --------------------------------------------------
# ORDERS
# --------------------------------------------------

elif page == "Orders":

    st.title("📦 Orders")

    try:

        r = api_get("/orders")
        r.raise_for_status()

        st.dataframe(
            pd.DataFrame(r.json()),
            use_container_width=True
        )

    except Exception as e:
        st.error(str(e))


# --------------------------------------------------
# PRODUCTS AND INVENTORY
# --------------------------------------------------

elif page == "Products & Inventory":

    st.title("🛍️ Products & Inventory")

    try:

        r = api_get("/products")
        r.raise_for_status()

        df = pd.DataFrame(r.json())

        st.dataframe(
            df,
            use_container_width=True
        )

        if len(df):

            st.warning(
                f"{int((df['stock'] < 5).sum())} "
                "products currently have fewer than 5 units."
            )

    except Exception as e:
        st.error(str(e))


# --------------------------------------------------
# SUPPORT TICKETS
# --------------------------------------------------

elif page == "Support Tickets":

    st.title("🎫 Support Tickets")

    try:

        r = api_get("/tickets")
        r.raise_for_status()

        st.dataframe(
            pd.DataFrame(r.json()),
            use_container_width=True
        )

    except Exception as e:
        st.error(str(e))


# --------------------------------------------------
# KNOWLEDGE DOCUMENTS
# --------------------------------------------------

elif page == "Knowledge Documents":

    st.title("📚 Knowledge Base")

    st.write(
        "Upload PDF, DOCX, TXT, CSV or Excel documents. "
        "The backend chunks and indexes their content."
    )

    uploaded = st.file_uploader(
        "Choose a document",
        type=["pdf", "docx", "txt", "csv", "xlsx", "xls"]
    )

    if uploaded and st.button(
        "Upload and index",
        type="primary"
    ):

        try:

            r = api_post(
                "/documents/upload",
                files={
                    "file": (
                        uploaded.name,
                        uploaded.getvalue(),
                        uploaded.type or "application/octet-stream"
                    )
                }
            )

            r.raise_for_status()

            st.success(
                f"Indexed {r.json()['chunks_indexed']} "
                f"chunks from {uploaded.name}"
            )

        except Exception as e:
            st.error(str(e))

    c1, c2 = st.columns(2)

    with c1:

        if st.button("Index sample documents"):

            try:

                r = api_post("/documents/ingest-samples")
                r.raise_for_status()

                st.json(r.json())

            except Exception as e:
                st.error(str(e))

    with c2:

        if st.button("Refresh document list"):
            st.rerun()

    try:

        r = api_get("/documents")
        r.raise_for_status()

        st.write(
            "Available files:",
            r.json()["documents"]
        )

    except Exception as e:
        st.error(str(e))
