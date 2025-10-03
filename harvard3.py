import mysql.connector
import pandas as pd
import requests
import streamlit as st
from sqlalchemy import create_engine

# ---------------- DB Connection ----------------
def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="thisisMaryam07",
        database="harvard_artifacts"
    )

def get_engine():
    return create_engine("mysql+mysqlconnector://root:thisisMaryam07@127.0.0.1/harvard_artifacts")

engine = get_engine()

# ---------------- Create Tables ----------------
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artifact_metadata (
      id INT PRIMARY KEY,
      title TEXT,
      culture TEXT,
      period TEXT,
      century TEXT,
      medium TEXT,
      dimensions TEXT,
      description TEXT,
      department TEXT,
      classification TEXT,
      accessionyear INT,
      accessionmethod TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artifact_media (
      objectid INT PRIMARY KEY,
      imagecount INT,
      mediacount INT,
      colorcount INT,
      rank_value INT,
      datebegin INT,
      dateend INT,
      CONSTRAINT fk1_id FOREIGN KEY (objectid) REFERENCES artifact_metadata(id)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artifact_colors (
      objectid INT,
      color TEXT,
      spectrum TEXT,
      hue TEXT,
      percent REAL,
      css3 TEXT,
      CONSTRAINT fk2_id FOREIGN KEY (objectid) REFERENCES artifact_metadata(id)
    );
    """)
    conn.commit()
    cursor.close()
    conn.close()

create_tables()

# ---------------- API Fetch ----------------
harvard_api = '042c9b34-c6c5-4f1f-8bce-55ce15462072'
url = 'https://api.harvardartmuseums.org/object'

def fetch_classifications(classi, pages=25):
    all_records = []
    for page in range(1, pages+1):
        params = {
            'apikey': harvard_api,
            'size': 100,
            'page': page,
            'classification': classi
        }
        response = requests.get(url, params=params)
        data = response.json()
        all_records.extend(data.get('records', []))
    return all_records

# ---------------- Data Processing ----------------
def artifact_details(all_records):
    artifact_metadata, artifact_media, artifact_colors = [], [], []

    for i in all_records:
        artifact_metadata.append((
            i.get('id'),
            i.get('title'),
            i.get('culture'),
            i.get('period'),
            i.get('century'),
            i.get('medium'),
            i.get('dimensions'),
            i.get('description'),
            i.get('department'),
            i.get('classification'),
            i.get('accessionyear'),
            i.get('accessionmethod')
        ))
        artifact_media.append((
            i.get('id'),
            i.get('imagecount'),
            i.get('mediacount'),
            i.get('colorcount'),
            i.get('rank'),
            i.get('datebegin'),
            i.get('dateend')
        ))
        colors = i.get('colors')
        if colors:
            for j in colors:
                artifact_colors.append((
                    i.get('id'),
                    j.get('color'),
                    j.get('spectrum'),
                    j.get('hue'),
                    j.get('percent'),
                    j.get('css3')
                ))
    return artifact_metadata, artifact_media, artifact_colors

# ---------------- Insert Data ----------------
def insert_metadata(records):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
    INSERT IGNORE INTO artifact_metadata (
        id, title, culture, period, century, medium, dimensions, 
        description, department, classification, accessionyear, accessionmethod
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    cursor.executemany(sql, records)
    conn.commit()
    cursor.close()
    conn.close()

def insert_media(records):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
    INSERT IGNORE INTO artifact_media (
        objectid, imagecount, mediacount, colorcount, rank_value, datebegin, dateend
    ) VALUES (%s,%s,%s,%s,%s,%s,%s)
    """
    cursor.executemany(sql, records)
    conn.commit()
    cursor.close()
    conn.close()

def insert_colors(records):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
    INSERT IGNORE INTO artifact_colors (
        objectid, color, spectrum, hue, percent, css3
    ) VALUES (%s,%s,%s,%s,%s,%s)
    """
    cursor.executemany(sql, records)
    conn.commit()
    cursor.close()
    conn.close()

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Harvard Artifact Explorer", layout="wide")

# Elegant Header
st.markdown("""
    <div style='text-align:center; background:linear-gradient(to right, #ffffff, #fdf5e6); 
                padding:20px; border-radius:15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);'>
        <h1 style='color:#B22222; font-size:46px; font-family:Georgia;'>🏛 Harvard Artifact Explorer</h1>
        <p style='color:#333333; font-size:20px; font-family:Trebuchet MS;'>
            Discover the beauty of history with <b style='color:#DAA520;'>golden insights</b> into Harvard Art Museum artifacts.
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# ---------------- Sidebar ----------------
st.sidebar.markdown("""
    <div style='text-align:center; padding:15px; background:linear-gradient(to bottom, #fff, #fdf5e6); 
                border-radius:12px; box-shadow: 0 3px 6px rgba(0,0,0,0.1);'>
        <h2 style='color:#B22222; font-family:Georgia;'>🔍 Classification</h2>
        <p style='font-size:15px; color:#444;'>Choose an artifact type</p>
    </div>
""", unsafe_allow_html=True)

chosen_class = st.sidebar.selectbox(" ", ["Paintings", "Sculpture", "Drawings", "Fragments", "Photographs"])

# ---------------- Expander Styling ----------------
with st.expander("📥 Fetch & Insert Data"):
    st.markdown("<h3 style='color:#DAA520; font-family:Georgia;'>Fetch Harvard Artifacts</h3>", unsafe_allow_html=True)
    st.write(f"Fetching and inserting artifacts for classification: **{chosen_class}**")

    if st.button("✨ Fetch & Insert Data"):
        with st.spinner("Fetching data... ⏳"):
            records = fetch_classifications(chosen_class, pages=25)
            meta, media, colors = artifact_details(records)
            insert_metadata(meta)
            insert_media(media)
            insert_colors(colors)

        st.success(f"✅ Inserted {len(meta)} metadata, {len(media)} media, {len(colors)} colors.")

        # Show fetched data instantly
        with st.expander("📄 Show Fetched Data"):
            st.subheader("📑 Metadata")
            st.dataframe(pd.DataFrame(meta, columns=[
                "id", "title", "culture", "period", "century", "medium", "dimensions",
                "description", "department", "classification", "accessionyear", "accessionmethod"
            ]))

            st.subheader("🖼 Media")
            st.dataframe(pd.DataFrame(media, columns=[
                "objectid", "imagecount", "mediacount", "colorcount", "rank_value", "datebegin", "dateend"
            ]))

            st.subheader("🎨 Colors")
            st.dataframe(pd.DataFrame(colors, columns=[
                "objectid", "color", "spectrum", "hue", "percent", "css3"
            ]))

# ---------------- View Database Section ----------------
with st.expander("🔍 View Database Tables by Classification"):
    st.markdown("<h3 style='color:#B22222; font-family:Georgia;'>📊 Explore Database</h3>", unsafe_allow_html=True)
    st.write("Select a table to view all artifacts stored in the database.")

    table_choice = st.selectbox("📂 Choose a Table", ["artifact_metadata", "artifact_media", "artifact_colors"])

    if st.button("📖 Show Table Data"):
        if table_choice == "artifact_metadata":
            query = f"SELECT * FROM {table_choice} WHERE classification = '{chosen_class}';"
        else:
            query = f"""
                SELECT t.* FROM {table_choice} t
                JOIN artifact_metadata m ON t.objectid = m.id
                WHERE m.classification = '{chosen_class}';
            """
        df = pd.read_sql(query, engine)

        st.success(f"✅ Loaded {len(df)} rows from **{table_choice}**")

        # Fancy styled dataframe
        st.dataframe(df.style.set_properties(**{
            'background-color': '#fdf5e6',
            'color': '#000',
            'border-color': 'gray'
        }))

# ---------------- Query Workspace ----------------
st.markdown("""
    <div style='text-align:center; padding:20px; background:linear-gradient(to right, #ffffff, #fdf5e6); 
                border-radius:15px; box-shadow:0 4px 10px rgba(0,0,0,0.1); margin-bottom:15px;'>
        <h2 style='color:#B22222; font-family:Georgia;'>📊 Query & Visualization</h2>
        <p style='font-size:16px; color:#444; font-family:Trebuchet MS;'>
            Run pre-built queries or customize your own to explore the Harvard Artifacts database.
        </p>
    </div>
""", unsafe_allow_html=True)

query_options = [
    "1.  List all artifacts from the 11th century belonging to Byzantine culture",
    "2.  What are the unique cultures represented in the artifacts?",
    "3.  List all artifacts from the Archaic Period",
    "4.  List artifact titles ordered by accession year descending",
    "5.  How many artifacts are there per department?",
    "6.  Which artifacts have more than 1 image?",
    "7.  What is the average rank of all artifacts?",
    "8.  Which artifacts have a higher colorcount than mediacount?",
    "9.  List all artifacts created between 1500 and 1600",
    "10. List artifact titles and hues for Byzantine culture",
    "11. List each artifact title with its associated hues",
    "12. Get artifact titles, cultures, and media ranks where the period is not null",
    "13. Find artifact titles ranked in the top 10 that include the hue 'Grey'",
    "14. How many artifacts exist per classification, and average media count",
    "15. How many artifacts have no media files?",
    "16. What are all distinct hues used?",
    "17. Top 5 most used colors by frequency",
    "18. Average coverage percentage for each hue",
    "19. List all colors used for a given artifact ID",
    "20. Total number of color entries",
    "21. Show artifacts where accession method contains 'purchase'",
    "22. List all artifacts from a specific department",
    "23. Find artifacts that have no description",
    "24. Show artifacts ordered by object ID",
    "25. Count artifacts with a non-null period"
]

selected_query = st.selectbox("✨ Select a Query to Run", query_options)

if st.button("🚀 Run Query"):
    query = ""
    if selected_query == query_options[0]:
        query = "SELECT * FROM artifact_metadata WHERE century='11th century' AND culture='Byzantine';"
    elif selected_query == query_options[1]:
        query = "SELECT DISTINCT culture FROM artifact_metadata WHERE culture IS NOT NULL;"
    elif selected_query == query_options[2]:
        query = "SELECT * FROM artifact_metadata WHERE period='Archaic';"
    elif selected_query == query_options[3]:
        query = "SELECT title, accessionyear FROM artifact_metadata ORDER BY accessionyear DESC;"
    elif selected_query == query_options[4]:
        query = "SELECT department, COUNT(*) as artifact_count FROM artifact_metadata GROUP BY department;"
    elif selected_query == query_options[5]:
        query = "SELECT title FROM artifact_media WHERE imagecount > 1;"
    elif selected_query == query_options[6]:
        query = "SELECT AVG(rank_value) as avg_rank FROM artifact_media;"
    elif selected_query == query_options[7]:
        query = "SELECT title FROM artifact_metadata m JOIN artifact_media md ON m.id=md.objectid WHERE md.colorcount > md.mediacount;"
    elif selected_query == query_options[8]:
        query = "SELECT * FROM artifact_metadata WHERE accessionyear BETWEEN 1500 AND 1600;"
    elif selected_query == query_options[9]:
        query = "SELECT m.title, c.hue FROM artifact_metadata m JOIN artifact_colors c ON m.id=c.objectid WHERE m.culture='Byzantine';"
    elif selected_query == query_options[10]:
        query = "SELECT m.title, c.hue FROM artifact_metadata m JOIN artifact_colors c ON m.id=c.objectid;"
    elif selected_query == query_options[11]:
        query = "SELECT title, culture, rank_value FROM artifact_metadata m JOIN artifact_media md ON m.id=md.objectid WHERE m.period IS NOT NULL;"
    elif selected_query == query_options[12]:
        query = "SELECT title FROM artifact_media md JOIN artifact_colors c ON md.objectid=c.objectid WHERE c.hue='Grey' ORDER BY rank_value DESC LIMIT 10;"
    elif selected_query == query_options[13]:
        query = "SELECT classification, COUNT(*) as artifact_count, AVG(mediacount) as avg_media FROM artifact_metadata m JOIN artifact_media md ON m.id=md.objectid GROUP BY classification;"
    elif selected_query == query_options[14]:
        query = "SELECT COUNT(*) FROM artifact_media WHERE mediacount=0;"
    elif selected_query == query_options[15]:
        query = "SELECT DISTINCT hue FROM artifact_colors;"
    elif selected_query == query_options[16]:
        query = "SELECT color, COUNT(*) as frequency FROM artifact_colors GROUP BY color ORDER BY frequency DESC LIMIT 5;"
    elif selected_query == query_options[17]:
        query = "SELECT hue, AVG(percent) as avg_percent FROM artifact_colors GROUP BY hue;"
    elif selected_query == query_options[18]:
        artifact_id = st.number_input("Enter Artifact ID", min_value=1)
        query = f"SELECT color FROM artifact_colors WHERE objectid={artifact_id};"
    elif selected_query == query_options[19]:
        query = "SELECT COUNT(*) FROM artifact_colors;"
    elif selected_query == query_options[20]:
        query = "SELECT * FROM artifact_metadata WHERE accessionmethod LIKE '%purchase%';"
    elif selected_query == query_options[21]:
        department = st.text_input("Enter Department Name")
        query = f"SELECT * FROM artifact_metadata WHERE department='{department}';"
    elif selected_query == query_options[22]:
        query = "SELECT * FROM artifact_metadata WHERE description IS NULL;"
    elif selected_query == query_options[23]:
        query = "SELECT * FROM artifact_metadata ORDER BY id;"
    elif selected_query == query_options[24]:
        query = "SELECT COUNT(*) FROM artifact_metadata WHERE period IS NOT NULL;"

    if query:
        df_query = pd.read_sql(query, engine)
        st.success(f"✅ Query executed successfully! Rows returned: {len(df_query)}")
        st.dataframe(df_query.style.set_properties(**{
            'background-color': '#fffaf0',
            'color': '#000',
            'border-color': 'gray'
        }))



