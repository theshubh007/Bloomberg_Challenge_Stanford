import streamlit as st
import time

# Set page configuration
st.set_page_config(page_title="Argument Linking Tool", layout="wide")

# Custom CSS
st.markdown("""
<style>
body {
    background-color: #121212;
    color: #ffffff;
}
.stButton>button {
    background-color: #0d6efd;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    font-weight: bold;
    transition: 0.3s;
}
.stButton>button:hover {
    background-color: #0b5ed7;
}
div[data-testid="stMarkdownContainer"] > div {
    animation: fadeIn 1s ease-in;
}
@keyframes fadeIn {
    from {opacity: 0;}
    to {opacity: 1;}
}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📊 Dashboard")
    st.write("Welcome to the Bloomberg Argument Analyzer")
    st.write("🕘 Recent: None")
    st.write("⚙️ Mode: Dark")

# Title
st.title("🧠 Argument-Counterargument Analyzer")

# Tabs for Upload or Input
tab1, tab2 = st.tabs(["🖊️ Text Input", "📁 Upload Document"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📝 Arguments")
        arg_text = st.text_area("Enter your arguments:", height=200)

    with col2:
        st.markdown("### 📄 Counter Arguments")
        counterarg_text = st.text_area("Enter counterarguments:", height=200)

with tab2:
    uploaded_file = st.file_uploader("Upload Document (TXT, PDF, DOCX)", type=["txt", "pdf", "docx"])

# Analyze Button
if st.button("🔍 Analyze Arguments"):
    if arg_text and counterarg_text:
        with st.spinner("🧠 Crunching logic..."):
            time.sleep(2)  # Replace with actual processing
            st.balloons()
            st.success("🔗 Linking Complete!")

            st.markdown(f"""
            <div style="background-color: #e2f0d9; padding: 15px; border-radius: 10px;">
                <h4 style="color: #495057;">🔗 Matched Pair:</h4>
                <b style="color: #0d6efd;">Argument:</b> <i>{arg_text[:100]}...</i><br>
                <b style="color: #dc3545;">Counterargument:</b> <i>{counterarg_text[:100]}...</i>
            </div>
            """, unsafe_allow_html=True)

            st.metric(label="💡 Confidence Score", value="85%", delta="▲ 5%")
            st.text_input("🖊️ Notes / Annotation")

            if st.button("📥 Export Matched Pairs"):
                st.download_button(label="Download Results",
                    data=f"Argument: {arg_text}\nCounterargument: {counterarg_text}",
                    file_name="matched_pairs.txt",
                    mime="text/plain")
    else:
        st.error("❌ Please enter both arguments and counterarguments.")

# Footer
st.markdown("---")
st.caption("📘 For help & documentation, visit the sidebar settings or documentation tab.")
