import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
import string
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from streamlit_gsheets import GSheetsConnection
from streamlit_extras.tags import tagger_component
from streamlit_dynamic_filters import DynamicFilters

# read in jobs file from live, public Google Sheet
url = 'https://docs.google.com/spreadsheets/d/1NBLoHTX_H6lNMNIn79YDncOa384fjgNGQQpFcIWDxTs/edit?usp=sharing'
conn = st.connection("gsheets", type=GSheetsConnection)
jobs = conn.read(spreadsheet=url)

def get_similarity_score(resume_text, job_description):
    # create a CountVectorizer instance to transform text into word frequency vectors
    vectorizer = CountVectorizer().fit([resume_text, job_description])
    
    # transform both texts into frequency vectors
    resume_vector = vectorizer.transform([resume_text])
    job_vector = vectorizer.transform([job_description])
    
    # compute cosine similarity between the resume and job description vectors
    similarity_matrix = cosine_similarity(resume_vector, job_vector)
    
    # extract similarity score as a percentage
    similarity_score = similarity_matrix[0, 0] * 100  # convert to percentage
    return round(similarity_score, 2)


def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text

def unique_choices(df_column):
    init = []
    for x in df_column:
        val = x.split(', ')
        for y in val:
            if y not in init:
                init.append(y)
    return init

unique_citizenship = unique_choices(jobs['Citizenship Eligibility'])
unique_education = unique_choices(jobs['Education Level'])
unique_category = unique_choices(jobs['Category'])

# organize streamlit app into tabs
tab1, tab2, tab3 = st.tabs(['Resume Match', 'All Jobs', 'About Us'])

with tab1:

    st.title("F.A.S.T. Internship Search")
    st.subheader("Federal Aggregator of Science & Technology Internships")
    
    # prompt resume upload
    resume_pdf = st.file_uploader("Upload your resume in PDF format to get matches to federal internships.", 
                                  type=["pdf"])
    if resume_pdf is not None:

        # add filter options
        col1, col2 = st.columns(2)
        with col1:
            citizenship = st.selectbox('Eligibility', 
                ['All', 'US Citizen', 'Permanent Resident', 
                'International Student'])
        with col2:
            applicant_type = st.selectbox('Applicant Type', [
                'All', 'High School', 'Undergraduate',
                'Graduate', 'PhD', 'Postdoctoral'
            ])
        
        # filter jobs based on user selection
        filter_index = []
        
        for i, row in jobs.iterrows():
            check1 = [row['Citizenship Eligibility']]
            check2 = [row['Education Level']]
            if citizenship in check1 and applicant_type in check2:
                filter_index.append(i)
            elif citizenship == 'Unspecified' and applicant_type in check2:
                filter_index.append(i)
            elif citizenship == 'All' and applicant_type in check2:
                filter_index.append(i)
            elif citizenship in check1 and applicant_type == 'All':
                filter_index.append(i)
            elif citizenship == 'All' and applicant_type == 'All':
                filter_index.append(i)
        
        user = jobs.iloc[filter_index]
        user = user.dropna(subset='Description').reset_index(drop = True)
        
        # clean up resume text, replace punctuation
        resume_text = extract_text_from_pdf(resume_pdf)
        resume_text = resume_text.replace('\n', '')
        
        for c in string.punctuation:
            resume_text = resume_text.replace(c, ' ')

        # compare against JDs to get a score
        user['Score'] = [get_similarity_score(resume_text, row['Description'])
                         for i, row in user.iterrows()]
        
        # filter user to top 3 scoring jobs
        user = user.sort_values(by = 'Score', ascending = False).reset_index(drop = True)
        user_result = user.head(3)
        
        st.divider()
        st.subheader('Top Internship Matches:')
    
        for i, row in user_result.iterrows():
            agency = row['Agency']
            opportunity = row['Opportunity Name']
            link = row['Link']

            # create container for each result
            with st.container(height = 150):
                st.markdown('**' + str(i+1)+ '.  ' + agency + ' | [' + opportunity+ '](' +link+ ')**')
                st.markdown(row['Description'])

    with tab2:

        # dynamic_filters = DynamicFilters(jobs, filters=['Citizenship Eligibility', 
        #                                                 'Education Level', 'Category'])

        # dynamic_filters.display_filters(location='columns', num_columns=3)

        # jobs = dynamic_filters.filter_df()
        # sep = ', '
        # jobs['Selections'] = jobs['Category'] + sep + jobs['Citizenship Eligibility'] + sep + jobs['Education Level']
        jobs['Category'] = [x.split(', ') for x in jobs.Category]
        jobs['Citizenship Eligibility'] = [x.split(', ') for x in jobs['Citizenship Eligibility']]
        jobs['Education Level'] = [x.split(', ') for x in jobs['Education Level']]
        st.dataframe(jobs)

        jobs_index = []
        filter1, filter2, filter3 = st.columns(3)

        with filter1:
            d = {}
            box = st.expander('Eligibility')
            with box:
                for i in range(len(unique_citizenship)):
                    d['choice{}'.format(i)] = st.checkbox(unique_citizenship[i])
        with filter2:
            box = st.expander('Applicant Type')
            with box:
                for x in unique_education:
                    choice = st.checkbox(x)
        with filter3:
            box = st.expander('Category')
            with box:
                for x in unique_category:
                    choice = st.checkbox(x)

        
        st.subheader('Results')

        # job listings
        for i, row in jobs.iterrows():
            agency = row['Agency']
            opportunity = row['Opportunity Name']
            link = row['Link']

            colors = []
            for x in row['Education Level']:
                colors.append('#06beea')

            for x in row['Citizenship Eligibility']:
                colors.append('#ffd909')

            with st.container(border=True):
                st.markdown('**' + agency + '  |  [' + opportunity + '](' + link + ')**')
                tags = row['Education Level'] + row['Citizenship Eligibility'] + row['Category']
                tag_cols = colors + ['#3bb273']
                tagger_component('', tags, color_name = tag_cols)
    
    with tab3:
        '''
        to do:
        - add copy to this About page
            - TOP summary
            - problem statement
            - user research
            - timeline
            - future enhancements
        '''

    











