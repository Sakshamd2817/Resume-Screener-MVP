import streamlit as st
import requests

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="Resume Screener", layout="centered")
st.title("📄 AI Resume Screener")

# User inputs
job_description = st.text_area("Job Description", height=100)
education = st.text_input("Education Qualification")
experience = st.number_input("Minimum Experience (years)", min_value=0, max_value=50, step=1)
skills = st.text_input("Required Skills (comma-separated)")
files = st.file_uploader("Upload Resumes (PDFs)", type=['pdf'], accept_multiple_files=True)

# Submit
if st.button("🧠 Analyze Resumes"):
    if not all([job_description, education, skills]) or not files:
        st.warning("Please fill all fields and upload at least one resume.")
    else:
        st.info("🚀 Sending resumes to server...")

        # Prepare files and form data
        files_data = [("files", (f.name, f, "application/pdf")) for f in files]
        payload = {
            "description": job_description,
            "education": education,
            "min_exp": str(experience),
            "skills": skills,
        }

        try:
            response = requests.post(
                "http://127.0.0.1:8000/resume/",
                data=payload,
                files=files_data
            )
            data = response.json()

            if "results" in data:
                st.success(data["message"])
                for result in data["results"]:
                    st.subheader(result["filename"])
                    st.write(f"**Similarity:** {result['similarity']} | **{result['eligibility']}**")
            else:
                st.error("Unexpected response format. Check FastAPI server logs.")
        except Exception as e:
            st.error(f"Error: {e}")
