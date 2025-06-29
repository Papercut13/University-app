import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Single-page University Dashboard
st.set_page_config(page_title="University Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('dummy_dataset_university.csv', dayfirst=True)
    # Parse date-like columns
    for col in df.columns:
        if df[col].dtype == 'object':
            sample = df[col].dropna().astype(str).head(5)
            if sample.str.match(r"^\d{2}/\d{2}/\d{4}$").all():
                df[col] = pd.to_datetime(df[col], dayfirst=True)
    # Ensure research quality numeric
    if 'Research quality (student ranked)' in df.columns:
        df['Research quality (student ranked)'] = pd.to_numeric(df['Research quality (student ranked)'], errors='coerce')
    return df

# Utility: render star rating
def render_stars(score):
    if pd.isna(score):
        return "No rating available"
    rounded = int(round(score))
    filled = '★' * rounded
    empty = '☆' * (5 - rounded)
    labels = {1: 'Very dissatisfied', 2: 'Dissatisfied', 3: 'Neutral', 4: 'Satisfied', 5: 'Very satisfied'}
    return f"<span style='font-size:2rem;color:#FFD700'>{filled}{empty}</span> <span style='font-size:1rem;color:#333'>{labels.get(rounded,'')}</span>"

# Load data
df = load_data()

# University selection at top
uni = st.selectbox("Select University", sorted(df['Official University Name'].dropna().unique()))
data = df[df['Official University Name'] == uni]

st.title(f"{uni} — University Dashboard")

# SECTION: Overall Satisfaction
st.header("Overall Satisfaction")
avg_sat = data['University score (1-5)'].mean()
st.markdown(render_stars(avg_sat), unsafe_allow_html=True)

# SECTION: Courses
courses_col, length_col = st.columns([2,1])
with courses_col:
    st.subheader("Top 5 Most-Pursued Courses")
    if 'Official Degree Name' in data.columns:
        top5 = data['Official Degree Name'].dropna().value_counts().nlargest(5).reset_index()
        top5.columns = ['Course','Count']
        fig_courses = px.bar(top5, x='Count', y='Course', orientation='h', height=300)
        fig_courses.update_layout(margin=dict(l=0,r=0,t=30,b=0))
        st.plotly_chart(fig_courses, use_container_width=True)
    else:
        st.write("No course data available.")

with length_col:
    st.subheader("Median Course Length & Popularity")
    # Compute course length: prefer date diff, fallback to 'Education year'
    if {'Start date','Graduation date'}.issubset(data.columns) and data[['Start date','Graduation date']].notna().all(axis=None):
        lengths = (data['Graduation date'] - data['Start date']).dt.days / 365
    elif 'Education year' in data.columns:
        lengths = pd.to_numeric(data['Education year'], errors='coerce')
    else:
        lengths = pd.Series([], dtype=float)
    if not lengths.empty and not lengths.isna().all():
        median_len = round(lengths.median(),1)
        st.metric("Median Length (yrs)", f"{median_len:.1f}")
    else:
        st.write("No length data available.")
    # Popularity donut
    if 'Official Degree Name' in data.columns:
        most = data['Official Degree Name'].dropna().mode()
        if not most.empty:
            most = most.iloc[0]
            pop = (data['Official Degree Name']==most).mean()
            pop_df = pd.DataFrame({'Category':[most,'Others'],'Pct':[pop,1-pop]})
            fig_pop = px.pie(pop_df, names='Category', values='Pct', hole=0.5, height=300)
            fig_pop.update_traces(texttemplate='%{percent}')
            st.plotly_chart(fig_pop, use_container_width=True)

# SECTION: Exams
st.header("Exams")
if 'Which exams you gave' in data.columns and data['Which exams you gave'].notna().any():
    exploded = data.assign(Exam=data['Which exams you gave'].dropna().str.split(',')).explode('Exam')
    exploded['Exam'] = exploded['Exam'].str.strip()
    # GRE vs GMAT
    gre_gmat = exploded[exploded['Exam'].isin(['GRE','GMAT'])]
    itp = exploded[exploded['Exam'].isin(['IELTS','TOEFL','PTE'])]
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("GRE vs GMAT")
        if not gre_gmat.empty:
            df1 = gre_gmat['Exam'].value_counts().reset_index()
            df1.columns=['Exam','Count']
            fig1 = px.pie(df1, names='Exam', values='Count', hole=0.4)
            fig1.update_traces(texttemplate='%{percent}')
            st.plotly_chart(fig1, use_container_width=True)
    with g2:
        st.subheader("IELTS / TOEFL / PTE")
        if not itp.empty:
            df2 = itp['Exam'].value_counts(normalize=True).reset_index()
            df2.columns=['Exam','Pct']
            fig2 = px.pie(df2, names='Exam', values='Pct', hole=0.4)
            fig2.update_traces(texttemplate='%{percent}')
            st.plotly_chart(fig2, use_container_width=True)
    # Coaching filter
    st.subheader("Coaching Usage by Exam")
    exam_list = exploded['Exam'].dropna().unique().tolist()
    sel_exam = st.selectbox("Exam", exam_list, key='coach')
    df_sel = exploded[exploded['Exam']==sel_exam]
    if 'Used coaching service' in df_sel.columns:
        coach_counts = df_sel['Used coaching service'].value_counts(normalize=True).reset_index()
        coach_counts.columns=['Used coaching','Pct']
        figc = px.bar(coach_counts, x='Used coaching', y='Pct', text=coach_counts['Pct'].apply(lambda x: f"{x:.0%}"))
        figc.update_yaxes(tickformat='%')
        st.plotly_chart(figc, use_container_width=True)

# SECTION: Transport
st.header("Transport")
if 'Primary transport mode' in data.columns:
    tm = data['Primary transport mode'].value_counts(normalize=True).reset_index()
    tm.columns=['Mode','Pct']
    fig_tm = px.pie(tm, names='Mode', values='Pct', hole=0.4)
    fig_tm.update_traces(texttemplate='%{percent}')
    t1, t2 = st.columns(2)
    with t1:
        st.subheader("Modes")
        st.plotly_chart(fig_tm, use_container_width=True)
if 'Transport days per week' in data.columns:
    tf = data['Transport days per week'].value_counts(normalize=True).reset_index()
    tf.columns=['Days','Pct']
    fig_tf = px.bar(tf, x='Days', y='Pct', text=tf['Pct'].apply(lambda x: f"{x:.0%}"))
    fig_tf.update_yaxes(tickformat='%')
    with t2:
        st.subheader("Frequency")
        st.plotly_chart(fig_tf, use_container_width=True)

# SECTION: Indian Community
st.header("Indian Community Presence")
if 'Big Indian community' in data.columns:
    ic = data['Big Indian community'].value_counts(normalize=True).reset_index()
    ic.columns=['Resp','Pct']
    fig_ic = px.pie(ic, names='Resp', values='Pct', hole=0.4)
    fig_ic.update_traces(texttemplate='%{percent}')
    st.plotly_chart(fig_ic, use_container_width=True)

# SECTION: Research
st.header("Research Metrics")
import plotly.graph_objects as go

col_rq, col_wr = st.columns(2)
with col_rq:
    st.subheader("Average Research Quality")
    if 'Research quality (1-5)' in data.columns:
        avg_q = data['Research quality (1-5)'].mean()

        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_q,
            number={'valueformat':'.1f','suffix':'/5'},
            gauge={
                'axis': {
                    'range': [0, 5],
                    'tickwidth': 1,
                    'tickcolor': 'darkblue'
                },
                'bar': {
                    'color': '#003f7f'            # solid navy-blue pointer
                },
                'bgcolor': 'white',
                'steps': [
                    {'range': [0, 1], 'color': '#e8f5ff'},
                    {'range': [1, 2], 'color': '#cceaff'},
                    {'range': [2, 3], 'color': '#99d5ff'},
                    {'range': [3, 4], 'color': '#66bfff'},
                    {'range': [4, 5], 'color': '#339aff'},
                ]
            }
        ))
        fig_g.update_layout(
            height=250,
            margin={'t': 0, 'b': 0, 'l': 0, 'r': 0}
        )

        st.plotly_chart(fig_g, use_container_width=True)

with col_wr:
    st.subheader("Worked in Research")
    if 'Worked in research' in data.columns:
        pct_res = data['Worked in research'].map({'Yes':1,'No':0}).mean()
        st.markdown(
            f"""
            <div style="background: linear-gradient(90deg,#4facfe,#00f2fe); padding:20px; border-radius:10px; text-align:center;">
              <span style="font-size:2rem; color:white; font-weight:bold;">{pct_res:.0%}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
