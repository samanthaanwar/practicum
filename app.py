import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
import string
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# from streamlit_gsheets import GSheetsConnection


def get_similarity_score(resume_text, job_description):
    # Create a CountVectorizer instance to transform text into word frequency vectors
    vectorizer = CountVectorizer().fit([resume_text, job_description])
    
    # Transform both texts into frequency vectors
    resume_vector = vectorizer.transform([resume_text])
    job_vector = vectorizer.transform([job_description])
    
    # Compute cosine similarity between the resume and job description vectors
    similarity_matrix = cosine_similarity(resume_vector, job_vector)
    
    # Extract similarity score as a percentage
    similarity_score = similarity_matrix[0, 0] * 100  # Convert to percentage
    return round(similarity_score, 2)


def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


tab1, tab2, tab3 = st.tabs(['Resume Match', 'All Jobs', 'About Us'])

with tab1:
    # Streamlit App
    st.title("F.A.S.T. Internship Search")
    st.subheader("Federal Aggregator of Science & Technology Internships")
    
    # Upload the resume in PDF format
    resume_pdf = st.file_uploader("Upload your resume in PDF format to get matches to federal internships.", 
                                  type=["pdf"])
    if resume_pdf is not None:
        col1, col2 = st.columns(2)
        
        with col1:
        
            citizenship = st.selectbox("Eligibility", 
                ["US Citizen", "Permanent Resident", "International Student", "Other"])
        
        with col2:
            
            applicant_type = st.selectbox("Applicant Type", [
                "High School", 
                "Undergraduate",
                "Graduate",
                "PhD", 
                "Postdoctoral"
            ])
        
        jobs = pd.read_csv("jobs.csv", encoding='latin-1')
        
        # filter jobs based on citizenship selection
        filter_index = []
        
        for i, row in jobs.iterrows():
            check1 = row['Citizenship Eligibility']
            check2 = row['Education Level']
            if citizenship in check1 and applicant_type in check2:
                filter_index.append(i)
            elif citizenship == 'Unspecified' and applicant_type in check2:
                filter_index.append(i)
        
                
        user = jobs.iloc[filter_index]
        user = user.dropna(subset='Description').reset_index(drop = True)
        
    
        
        # create count of words in resume
        resume_text = extract_text_from_pdf(resume_pdf)
        resume_text = resume_text.replace('\n', '')
        
        for c in string.punctuation:
            resume_text = resume_text.replace(c, ' ')
        
            
        user['Score'] = [get_similarity_score(resume_text, row['Description'])
                         for i, row in user.iterrows()]
        
        # filter user to top 3 jobs
        user = user.sort_values(by = 'Score', ascending = False).reset_index(drop = True)
        
        user_result = user.head(3)
        
        # st.data_editor(
        #     user_result,
        #     column_config={'Link': st.column_config.LinkColumn('Link')},
        #     hide_index = True)
        
        st.divider()
        st.subheader('Top Internship Matches:')
    
        for i, row in user_result.iterrows():
            label = row['Agency'] + ' | ' + row['Opportunity Name']
            listing = st.expander(label).write(row['Description'])

    
    
    











