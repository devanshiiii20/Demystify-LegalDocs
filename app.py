import streamlit as st
from demystifying_docs import extract_text_from_document, simplify_long_text, explain_jargon
from google.cloud import translate_v2 as translate
import base64, time

# Import the same paths
#SERVICE_ACCOUNT_KEY_PATH, SAMPLE_DOC_PATH

#PDF preview
def show_pdf(file_bytes):
    base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

#translate
def translate_text(text, target_language):
    client = translate.Client.from_service_account_json("/content/drive/MyDrive/demystify/demystifying-legal-docs-656e8c1f99a1.json")
    lang_map = {"English": "en", "Hindi": "hi"}
    if target_language == "English":
        return text
    result = client.translate(text, target_language=lang_map[target_language])
    return result["translatedText"]

#risk detection
def detect_risks(text):
    risks = []
    risk_keywords = {
        "Penalty / Late Fees": ["penalty", "late fee", "fine"],
        "Termination / Lock-in": ["termination", "lock-in", "binding period", "expiry"],
        "Payment / Interest": ["interest", "payment", "due", "loan"],
        "Confidentiality": ["confidential", "non-disclosure", "nda"],
        "Liability": ["liability", "indemnify", "responsible"]
    }
    lowered = text.lower()
    for category, keywords in risk_keywords.items():
        for kw in keywords:
            if kw in lowered:
                risks.append(f"⚠️ {category}: contains '{kw}'")
                break
    return risks if risks else ["✅ No major risks detected."]

#UI/UX

st.set_page_config(
    page_title="Demystify Legal Docs",
    page_icon="📑",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main {
        background-color: var(--background-color);
        font-family: 'Helvetica', sans-serif;
    }
    h1, h2, h3 {
        color: #007BFF; /* bright blue */
    }
    .title {
        font-size:32px !important;
        font-weight:700 !important;
        color:#007BFF !important;
    }
    .subtitle {
        font-size:18px !important;
        color: var(--text-color) !important;
    }
    .stButton>button {
        background-color: #2b3a67;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        height: 3em;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #4056a1;
        color: #f5f5f5;
    }
    .sidebar-footer {
        color: var(--text-color) !important;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<p class='title'>📑 Demystify Legal Docs</p>", unsafe_allow_html=True);
st.markdown("<p class='subtitle'>Upload your legal document and get a simplified version instantly.</p>", unsafe_allow_html=True);

#sidebar
language = st.sidebar.selectbox(
    "🌍 Choose output language",
    ["English", "Hindi"]
)

st.sidebar.title("ℹ️ About")
st.sidebar.info("Demystify Legal Docs is a GenAI-powered tool that makes legal language accessible. It extracts contracts and judgments using Document AI, simplifies them with Vertex AI, explains jargon in plain English, and highlights hidden risks. Built to bridge the gap between law and people, so everyone can make informed decisions.\n")

#sample document option
use_sample = st.checkbox("📂 Try with Sample Document")

if use_sample:
    sample_pdf_path = "/content/drive/MyDrive/demystify/Non Disclosure Agreement.pdf"
    with open(sample_pdf_path, "rb") as f:
        file_bytes = f.read()
    uploaded_file = "sample.pdf"
else:
    uploaded_file = st.file_uploader("📂 Upload a PDF", type="pdf")
    file_bytes = uploaded_file.read() if uploaded_file else None

if file_bytes:
    st.write("Extracting text…")
    raw_text = extract_text_from_document(file_bytes)

    tabs = st.tabs([
        "📝 Simplified Text",
        "📑 Original PDF",
        "📘 Legal Jargon Explained",
        "🔍 Summary",
        "⚠️ Risks"
    ])

    #simplified text
    with tabs[0]:
        with st.spinner("⚡ Simplifying your document... Please wait."):
            simplified = simplify_long_text(raw_text)
        simplified_out = translate_text(simplified, language)
        print(f"Simplified Output: {simplified_out}")
        st.text_area("", simplified_out, height=400)
        st.download_button("✨ Download Simplified Doc", data=simplified_out, file_name="simplified.txt")

    #original PDF
    with tabs[1]:
        show_pdf(file_bytes)

    #legal jargon explained
    with tabs[2]:
        with st.spinner("📘 Explaining legal jargon..."):
            jargon_explained = explain_jargon(raw_text[:1500])
        jargon_out = translate_text(jargon_explained, language)
        print(f"Jargon Explanation Output: {jargon_out}")
        st.text_area("", jargon_out, height=400)
        st.download_button("📘 Download Jargon Explanation", data=jargon_out, file_name="jargon_explanation.txt")

    #summary
    with tabs[3]:
        with st.spinner("🧾 Generating summary..."):
            time.sleep(5)
            summary = simplify_long_text("Summarize this document in plain English:\n" + raw_text[:2000])
        summary_out = translate_text(summary, language)
        print(f"Summary Output: {summary_out}")
        st.text_area("", summary_out, height=250)
        st.download_button("🔍 Download Summary", data=summary_out, file_name="summary.txt")

    #risks
    with tabs[4]:
        with st.spinner("🔎 Checking for risks..."):
            risks = detect_risks(raw_text)
        for r in risks:
            st.write(r)


st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div class="sidebar-footer">
    👩‍💻 TEAM : AC/PC
    </div>
    """,
    unsafe_allow_html=True
)
