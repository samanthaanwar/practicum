import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from streamlit_gsheets import GSheetsConnection
from streamlit_extras.tags import tagger_component
from streamlit_dynamic_filters import DynamicFilters
from datetime import date
from datetime import datetime

# read in jobs file from live, public Google Sheet
url = 'https://docs.google.com/spreadsheets/d/1NBLoHTX_H6lNMNIn79YDncOa384fjgNGQQpFcIWDxTs/edit?usp=sharing'
conn = st.connection("gsheets", type=GSheetsConnection)
jobs = conn.read(spreadsheet=url)

def clean_jobs(df):
    df['Category'] = [x.split(', ') for x in df.Category]
    df['Citizenship Eligibility'] = [x.split(', ') for x in df['Citizenship Eligibility']]
    df['Education Level'] = [x.split(', ') for x in df['Education Level']]
    df['Deadline'] = [datetime.strptime(date_str, '%m/%d/%Y').date() for date_str in df['Deadline']]

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
unique_agency = sorted(unique_choices(jobs.Agency))
unique_agency += ['Other']

clean_jobs(jobs)

# organize streamlit app into tabs
tab1, tab2, tab3 = st.tabs(['Resume Match', 'All Jobs', 'Post a Job'])

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
            ['All']+unique_citizenship)
        with col2:
            applicant_type = st.selectbox('Applicant Type', 
            ['All'] + unique_education)
        
        # filter jobs based on user selection
        filter_index = []
        
        for i, row in jobs.iterrows():
            if citizenship == 'All':
                if applicant_type == 'All':
                    filter_index.append(i)
                elif applicant_type in row['Education Level']:
                    filter_index.append(i)
            else:
                if applicant_type == 'All':
                    if citizenship in row['Citizenship Eligibility']:
                        filter_index.append(i)
                else:
                    if citizenship in row['Citizenship Eligibility'] and applicant_type in row['Education Level']:
                        filter_index.append(i)
        
        user = jobs.iloc[filter_index]
        user = user.dropna(subset='Description').reset_index(drop = True)
        
        # clean up resume text, replace punctuation
        resume_text = extract_text_from_pdf(resume_pdf)

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
                st.write('Score: ', row['Score'])
                st.markdown(row['Description'])

with tab2:
    jobs = st.session_state.jobs
    jobs_index = []
    filter1, filter2, filter3 = st.columns(3)

    with filter1:
        d1 = {}
        box = st.expander('Eligibility')
        with box:
            for x in unique_citizenship:
                d1['{}'.format(x)] = st.checkbox(x, key = x)
    with filter2:
        d2 = {}
        box = st.expander('Applicant Type')
        with box:
            for x in unique_education:
                d2['{}'.format(x)] = st.checkbox(x, key = x)
    with filter3:
        d3 = {}
        box = st.expander('Category')
        with box:
            for x in unique_category:
                d3['{}'.format(x)] = st.checkbox(x, key = x)

    sort_select = st.radio('Sort results by', ['Alphabet', 'Deadline'])
    if sort_select == 'Alphabet':
        jobs = jobs.sort_values(by = 'Opportunity Name')
    else:
        jobs = jobs.sort_values(by = 'Deadline')
        
    st.subheader('Results')

    d1_select = {k for k,v in d1.items() if v}
    d2_select = {k for k,v in d2.items() if v}
    d3_select = {k for k,v in d3.items() if v}
    
    # filter results
    jobs1 = []
    jobs2 = []
    jobs3 = []
    for i, row in jobs.iterrows():
        for val in row['Citizenship Eligibility']:
            if val in d1_select:
                jobs1.append(i)
        for val in row['Education Level']:
            if val in d2_select:
                jobs2.append(i)
        for val in row.Category:
            if val in d3_select:
                jobs3.append(i)
    
    for i in range(len(jobs)):
        if len(jobs1) == 0:
            if len(jobs2) == 0:
                if len(jobs3) == 0:
                    jobs_index.append(i)
                else:
                    jobs_index = jobs3
            elif len(jobs2) != 0:
                if len(jobs3) == 0:
                    jobs_index = jobs2
                elif i in jobs2 and i in jobs3:
                    jobs_index.append(i)
        else:
            if len(jobs2) == 0:
                if len(jobs3) == 0:
                    jobs_index = jobs1
                elif i in jobs1 and i in jobs3:
                    jobs_index.append(i)
            else:
                if len(jobs3) == 0:
                    if i in jobs1 and i in jobs2:
                        jobs_index.append(i)
                elif i in jobs1 and i in jobs2 and i in jobs3:
                    jobs_index.append(i)

    jobs = jobs.iloc[jobs_index]

    # filter for jobs due after today
    jobs = jobs.loc[jobs.Deadline > date.today()]

    # job listings
    for i, row in jobs.iterrows():
        agency = row['Agency']
        opportunity = row['Opportunity Name']
        link = row['Link']
        deadline = row['Deadline']
        days_left = (deadline-date.today()).days
        deadline_str = deadline.strftime('%b %d, %Y')
        
        colors = []
        for x in row['Education Level']:
            colors.append('#06beea')

        for x in row['Citizenship Eligibility']:
            colors.append('#ffd909')

        with st.container(border=True):
            st.markdown('**' + agency + '  |  [' + opportunity + '](' + link + ')**')
            tags = row['Education Level'] + row['Citizenship Eligibility'] + row['Category'][:1]
            if days_left < 15:
                tags.append(f'App due in {days_left} day(s)')
                colors += ['#3bb273','red']
            else:
                tags.append('Due '+deadline_str)
                colors += ['#3bb273','orange']
            tagger_component('', tags, color_name = colors)

with tab3:

    st.title('Add a job to our database.')
    st.write('If you want your federal internship opportunity to be included in this dataset, fill out the form below!')
    st.write('Thank you for your contribution.')

    with st.form('post_job'):
        name = st.text_input('Opportunity Name')
        agency = st.selectbox('Agency', unique_agency)
        citizenship = st.multiselect('Eligibility', unique_citizenship)
        education = st.multiselect('Applicant Type', unique_education)
        category = st.selectbox('Category', unique_category)
        link = st.text_input('Link to application')
        deadline = st.date_input('Deadline', value=None)
        descr = st.text_area('Role description')
        submitted = st.form_submit_button("Submit")

        # transform into strings
        citizenship = ", ".join(citizenship)
        education = ", ".join(education)
    
        if submitted:
            # add row to jobs dataframe
            new_row = {
                'Agency':agency, 
                'Opportunity Name': name,
                'Citizenship Eligibility': citizenship,
                'Education Level': education,
                'Category': category,
                'Link': link,
                'Description': descr,
                'Deadline': deadline
            }

            new_row_df = pd.DataFrame(new_row, index=[0])
            clean_jobs(new_row_df)          
            updated_jobs = pd.concat([jobs, new_row_df], ignore_index=True)

            st.write('Job added. Thank you!')
            st.session_state.jobs = updated_jobs