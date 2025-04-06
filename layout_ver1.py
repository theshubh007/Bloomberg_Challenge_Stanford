import streamlit as st
from MatchingEngine.matchingEngineService import ArgumentAnalyzer, process_file_content


def main():
    # Set page configuration
    st.set_page_config(page_title="Argument Linking Tool", layout="wide")

    # Custom CSS
    st.markdown(
        """
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
""",
        unsafe_allow_html=True,
    )

    # Initialize the argument analyzer
    @st.cache_resource
    def get_analyzer():
        return ArgumentAnalyzer()

    analyzer = get_analyzer()

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

    def display_analysis_results(results):
        """Display the analysis results in a structured format"""
        # Display similarity score
        similarity_percentage = results["similarity_score"] * 100
        st.metric(
            label="💡 Overall Similarity Score",
            value=f"{similarity_percentage:.1f}%",
            delta=f"{'▲' if similarity_percentage > 50 else '▼'} {abs(similarity_percentage - 50):.1f}% from neutral",
        )

        # Display key points from both arguments
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📝 Main Argument Points")
            for point in results["argument_points"]:
                st.markdown(f"- {point}")

        with col2:
            st.markdown("### 📄 Counter Argument Points")
            for point in results["counter_argument_points"]:
                st.markdown(f"- {point}")

        # Display missing points
        st.markdown("### 🔍 Unique Points Analysis")

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

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📝 Arguments")
            arg_text = st.text_area("Enter your arguments:", height=200)

        with col2:
            st.markdown("### 📄 Counter Arguments")
            counterarg_text = st.text_area("Enter counterarguments:", height=200)

    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📝 Arguments File")
            arg_file = st.file_uploader(
                "Upload Arguments (TXT)", type=["txt"], key="arg_file"
            )
            if arg_file:
                arg_text = process_file_content(arg_file.getvalue().decode("utf-8"))
                st.text_area(
                    "Arguments Content:", arg_text, height=200, key="arg_preview"
                )

        with col2:
            st.markdown("### 📄 Counter Arguments File")
            counterarg_file = st.file_uploader(
                "Upload Counter Arguments (TXT)", type=["txt"], key="counterarg_file"
            )
            if counterarg_file:
                counterarg_text = process_file_content(
                    counterarg_file.getvalue().decode("utf-8")
                )
                st.text_area(
                    "Counter Arguments Content:",
                    counterarg_text,
                    height=200,
                    key="counterarg_preview",
                )

    # Analyze Button
    if st.button("🔍 Analyze Arguments"):
        if arg_text and counterarg_text:
            with st.spinner("🧠 Analyzing arguments..."):
                # Perform analysis
                results = analyzer.analyze_arguments(arg_text, counterarg_text)

                # Display results
                st.success("✅ Analysis Complete!")
                display_analysis_results(results)

                # Export option
                if st.button("📥 Export Analysis"):
                    export_data = f"""Argument Analysis Results
                    
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
                    st.download_button(
                        label="Download Analysis",
                        data=export_data,
                        file_name="argument_analysis.txt",
                        mime="text/plain",
                    )
        else:
            st.error("❌ Please provide both arguments and counterarguments.")

    # Footer
    st.markdown("---")
    st.caption(
        "📘 For help & documentation, visit the sidebar settings or documentation tab."
    )


if __name__ == "__main__":
    main()
