import streamlit as st
import time
from MatchingEngine.matchingEngineService import ArgumentAnalyzer
from fpdf import FPDF  # Ensure you have installed FPDF: pip install fpdf

def extract_file_content(file):
    """
    Extract text from a file supporting TXT and PDF formats.
    For PDFs, PyPDF2 is used to extract text from each page
    and return it as one continuous line.
    """
    file.seek(0)
    if file.type == "application/pdf" or file.name.lower().endswith(".pdf"):
        try:
            import PyPDF2
        except ImportError:
            return "Error: PyPDF2 module is not installed. Please install it using: pip install PyPDF2"
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
        return " ".join(text.split())
    else:
        return file.read().decode("utf-8")

def main():
    # Set page configuration
    st.set_page_config(page_title="Argument Linking Tool", layout="wide")

    # Custom CSS for a light mode UI: white backgrounds and bold black text everywhere.
    st.markdown(
        """
<style>
/* Main area styling */
body, div[data-testid="stAppViewContainer"] {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    font-family: "Times New Roman", Times, serif;
    font-size: 18px;
    font-weight: bold !important;
}
/* Style for the tab labels */
div[role="tabs"] {
    background-color: #000000 !important; /* White background */
    color: #000000 !important;           /* Black text */
    font-weight: bold !important;
    padding: 10px 20px !important;
    border: 1px solid #000000 !important;
    border-radius: 5px !important;
    margin-right: 5px;
}



/* Sidebar styling */
div[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    color: #000000 !important;
}
div[data-testid="stSidebar"] h1,
div[data-testid="stSidebar"] h2,
div[data-testid="stSidebar"] h3,
div[data-testid="stSidebar"] h4,
div[data-testid="stSidebar"] h5,
div[data-testid="stSidebar"] h6,
div[data-testid="stSidebar"] p,
div[data-testid="stSidebar"] label {
    color: #000000 !important;
    font-family: "Times New Roman", Times, serif;
    font-weight: bold !important;
}

/* Sidebar buttons */
div[data-testid="stSidebar"] .stButton>button {
    background-color: transparent !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 0 !important;
    font-weight: bold !important;
    transition: 0.3s;
    padding: 0.4rem 1rem;
    margin-bottom: 0.5rem;
}
div[data-testid="stSidebar"] .stButton>button:hover {
    text-decoration: underline;
}

/* Main area buttons */
.stButton>button {
    background-color: #FFFFFF;
    color: #000000;
    padding: 0.5rem 1rem;
    border: 1px solid #000000;
    border-radius: 4px;
    font-weight: bold;
    transition: 0.3s;
}
.stButton>button:hover {
    background-color: #000000;
}

/* Style text areas with white background and bold black text */
textarea {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #CCCCCC !important;
    font-weight: bold !important;
}

/* Force tab labels to be black and bold */
div[role="tabs"] span {
    color: #000000 !important;
    font-weight: bold !important;
}
[data-testid="stMetricValue"] {
        color: blue;
    }

/* Responsive adjustments */
@media (max-width: 768px) {
    div[data-testid="stAppViewContainer"] {
        font-size: 16px;
    }
}
</style>
""",
        unsafe_allow_html=True,
    )

    # Initialize the argument analyzer (cached)
    @st.cache_resource
    def get_analyzer():
        return ArgumentAnalyzer()
    analyzer = get_analyzer()

    # Sidebar
    with st.sidebar:
        st.header("Dashboard")
        st.write("Welcome to the Bloomberg Argument Analyzer. This tool analyzes arguments and counterarguments.")
        st.write("You can input your text manually or upload documents (TXT or PDF).")
        st.write("After providing the inputs, click **Analyze Arguments** to view insights. You may also download the results.")
        st.write("Version: 1.0.0")

    # Title
    st.title("Argument-Counterargument Analyzer")

    # Tabs for Input or File Upload
    tab1, tab2 = st.tabs(["**:red[Text Input]**", "**:red[Upload Document]**"])

    def display_analysis_results(results):
        """Display the analysis results in a structured format."""
        similarity_percentage = results["similarity_score"] * 100
        st.metric(
            label="**:blue[Overall Similarity Score]**",
            value=f"{similarity_percentage:.1f}%",
            delta=f"{'▲' if similarity_percentage > 50 else '▼'} {abs(similarity_percentage - 50):.1f}% from neutral",
        )
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Main Argument Points")
            for point in results["argument_points"]:
                st.markdown(f"- {point}")
        with col2:
            st.markdown("### Counter Argument Points")
            for point in results["counter_argument_points"]:
                st.markdown(f"- {point}")
        st.markdown("### Unique Points Analysis")
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("#### Points Unique to Main Argument")
            if results["missing_points"]["unique_to_argument"]:
                for point in results["missing_points"]["unique_to_argument"]:
                    st.markdown(f"- {point}")
            else:
                st.info("No unique points found")
        with col4:
            st.markdown("#### Points Unique to Counter Argument")
            if results["missing_points"]["unique_to_counterargument"]:
                for point in results["missing_points"]["unique_to_counterargument"]:
                    st.markdown(f"- {point}")
            else:
                st.info("No unique points found")

    # --- Text Input Tab ---
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Arguments")
            arg_text = st.text_area("Enter your arguments:", height=200)
        with col2:
            st.markdown("### Counter Arguments")
            counterarg_text = st.text_area("Enter counterarguments:", height=200)

    # --- Upload Document Tab ---
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Arguments File")
            arg_file = st.file_uploader("Upload Arguments (TXT or PDF)", type=["txt", "pdf"], key="arg_file")
            if arg_file:
                arg_text = extract_file_content(arg_file)
                st.text_area("Arguments Content:", arg_text, height=200, key="arg_preview")
        with col2:
            st.markdown("### Counter Arguments File")
            counterarg_file = st.file_uploader("Upload Counter Arguments (TXT or PDF)", type=["txt", "pdf"], key="counterarg_file")
            if counterarg_file:
                counterarg_text = extract_file_content(counterarg_file)
                st.text_area("Counter Arguments Content:", counterarg_text, height=200, key="counterarg_preview")

    # Analyze Button
    if st.button("Analyze Arguments"):
        if arg_text and counterarg_text:
            with st.spinner("Analyzing arguments..."):
                results = analyzer.analyze_arguments(arg_text, counterarg_text)
                time.sleep(2)
            st.success("**:blue[Analysis Complete!]**")
            display_analysis_results(results)
            # Generate export text for the analysis
            export_text = f"""Argument Analysis Results

Similarity Score: {results['similarity_score']*100:.1f}%

Main Argument Points:
{chr(10).join(f'- {point}' for point in results['argument_points'])}

Counter Argument Points:
{chr(10).join(f'- {point}' for point in results['counter_argument_points'])}

Unique Points in Main Argument:
{chr(10).join(f'- {point}' for point in results['missing_points']['unique_to_argument'])}

Unique Points in Counter Argument:
{chr(10).join(f'- {point}' for point in results['missing_points']['unique_to_counterargument'])}
"""
            # Create PDF using FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Times", size=12)
            pdf.multi_cell(0, 10, export_text)
            pdf_data = pdf.output(dest='S').encode('latin1')
            st.download_button(
                label=":red[Download Analysis]",
                data=pdf_data,
                file_name="argument_analysis.pdf",
                mime="application/pdf",
            )
        else:
            st.error("Please provide both arguments and counterarguments.")

    st.markdown("---")
    st.caption("For help & documentation, please refer to the sidebar.")

if __name__ == "__main__":
    main()
