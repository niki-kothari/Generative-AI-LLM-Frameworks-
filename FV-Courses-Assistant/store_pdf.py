import os
from pathlib import Path
from dotenv import load_dotenv
import faiss
import numpy as np
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
import nltk
from nltk.stem import WordNetLemmatizer
import re
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from firebase_admin import firestore
from firebase_config import get_db
import retrieve_data
#import new_retrieve_data
from category_form import category_form, get_categories, get_category_id, get_category_name


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "data" / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)
FAISS_PATH = BASE_DIR / "data" / "faiss_index"

# =========================
# 🔹 FIND KEYWORDS
# =========================

nltk.download('wordnet')
lemmatizer = WordNetLemmatizer()

def preprocess_text(text):
    words = re.findall(r'\b\w+\b', text.lower())
    lemmatized = [lemmatizer.lemmatize(word) for word in words]
    return " ".join(lemmatized)

def remove_redundant_keywords(keywords):
    final_keywords = []
    
    for kw in keywords:
        # If keyword is already covered by a longer phrase, skip it
        if not any(kw in longer and kw != longer for longer in keywords):
            final_keywords.append(kw)
    
    return final_keywords

def extract_keywords_tfidf(texts, top_k=30):

    full_text = " ".join(texts).lower()

    # 🔥 Your custom words
    custom_stopwords = {
    "course", "student", "learn", "training", "institute", "learning", "data", "using", "skills",
    "projects", "real-world", "world", "models", "deep", "text", "vision", "computer", "system",
    "development", "program", "module", "duration", "introduction", "advanced", "professional",
    "real", "classification", "systems", "applications", "business", "languages", "model", "industry",
    "time", "web", "app", "career", "opportunities", "job", "market", "trends", "customer", "build",
    "future", "vision", "institute", "time", "structured", "like", "unstructured", "data", "natural",
    "language", "processing", "computer", "content", "management", "patterns", "networks", "experience",
    "image", "ready", "based", "computers", "practicals", "outcomes", "key", "create", "20", "internet",
    "documents", "use", "word", "product", "student", "courses", "growth", "house", "students", "learn",
    "training", "institute", "learning", "data", "using", "skills", "01", "02", "03", "04", "05", "06",
    "07", "08", "09", "10"
    }

    # 🔥 Combine both
    all_stopwords = list(ENGLISH_STOP_WORDS.union(custom_stopwords))

    vectorizer = TfidfVectorizer(
        stop_words=all_stopwords,
        max_features=1000,
        ngram_range=(1, 2)
    )

    X = vectorizer.fit_transform([full_text])

    scores = zip(vectorizer.get_feature_names_out(), X.toarray()[0])
    sorted_keywords = sorted(scores, key=lambda x: x[1], reverse=True)

    keywords = [word for word, score in sorted_keywords[:top_k * 2]]  # take more first

     # 🔥 Remove redundancy
    keywords = remove_redundant_keywords(keywords)

    return keywords[:top_k]

# =========================
# 🔹 SAVE PDF LOCALLY AND LOAD
# =========================
def save_uploaded_file(uploaded_file):
    save_path = PDF_DIR / uploaded_file.name
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return save_path

def process_tools(tools_input):
    if not tools_input:
        return []

    tools_list = [
        tool.strip().lower()   # remove spaces + normalize
        for tool in tools_input.split(",")
        if tool.strip()        # remove empty values
    ]

    # remove duplicates while keeping order
    tools_list = list(dict.fromkeys(tools_list))

    return tools_list

# =========================
# 🔹 STORE FUNCTION
# =========================
def store_pdf(pdf_path, metadata):
    db = get_db()

    # Load PDF
    loader = PyMuPDFLoader(pdf_path)
    documents = loader.load()

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " ", ""]        
    )
    chunks = splitter.split_documents(documents)

    if not chunks:
        raise ValueError("❌ No chunks created from PDF. Check PDF content")

    # Embeddings
    embedding_model = OpenAIEmbeddings()

    # 🔥 Enrich text with Category + Tools + Course Name
    category_name = get_category_name(metadata["category"])
    #tools_text = ", ".join(metadata.get("tools", []))
    course_name = metadata.get("name", "")

    texts = [
        f"""
        Course: {course_name}
        Category: {category_name}
        Tools: {metadata.get("tools", [])}

        Content:
        {chunk.page_content}
        """
        for chunk in chunks
    ]

    #texts = [chunk.page_content for chunk in chunks]
    embeddings = embedding_model.embed_documents(texts)
    embeddings = np.array(embeddings).astype("float32")

    if len(embeddings) == 0:
        raise ValueError("❌ Embeddings are empty.")
    
    # =========================
    # 🔹 STORE IN FAISS
    # =========================
    dim = embeddings.shape[1]

    if os.path.exists(f"{FAISS_PATH}/index.faiss"):
        index = faiss.read_index(f"{FAISS_PATH}/index.faiss")
        start_id = index.ntotal
    else:
        index = faiss.IndexIDMap(faiss.IndexFlatL2(dim))
        start_id = 0

    # storing in FAISS with custom IDs to link with Firebase
    ids = np.arange(start_id, start_id + len(embeddings)).astype("int64")
    index.add_with_ids(embeddings, ids)

    os.makedirs(FAISS_PATH, exist_ok=True)
    faiss.write_index(index, f"{FAISS_PATH}/index.faiss")

    # =========================
    # 🔹 STORE IN FIREBASE
    # =========================
    #course_ref = db.collection("Future Vision Computer Institute Courses").document(course_name)
    course_ref = db.collection ("courses").document()
    course_id = course_ref.id  # 🔥 Get auto-generated ID for linking

    # ---- Keywords ----
    keywords = extract_keywords_tfidf(texts)

    # Store chunks separately
    chunks_collection = db.collection("chunks")  # 🔥 GLOBAL COLLECTION

    faiss_ids = []
    for i, chunk in enumerate(chunks):
        chunk_id = int(start_id + i)   # 🔥 THIS LINKS TO FAISS
        faiss_ids.append(chunk_id)

        chunks_collection.document(str(chunk_id)).set({
            "text": texts[i],
            "course_id": course_id,
            "chunk_index": i
        })

    # Store metadata only
    course_ref.set({
        "id": course_id,
        "name": metadata["name"],
        "category": metadata["category"],
        "tools": process_tools(metadata["tools"]),
        "level": metadata["level"],
        "fees": metadata["fees"],
        "duration": metadata["duration"],
        "weeks": metadata["weeks"],
        "hours": metadata["hours"],
        "keywords": keywords,
        "faiss_ids": faiss_ids,
        "time":firestore.SERVER_TIMESTAMP
    })

    return course_id  # 🔥 Return course ID for UI use

# =========================
# 🔹 UPDATE FUNCTION
# =========================
def update_course(course_id, pdf_path, metadata):
    db = get_db()
    course_ref = db.collection("courses").document(course_id)

    doc = course_ref.get()

    if doc.exists:
        old_data = doc.to_dict()
        old_ids = old_data.get("faiss_ids", [])

        # 🔥 LOAD FAISS
        index = faiss.read_index(f"{FAISS_PATH}/index.faiss")

        # 🔥 REMOVE OLD VECTORS
        if isinstance(index, faiss.IndexIDMap):
            remove_ids = np.array(old_ids, dtype=np.int64)
            index.remove_ids(remove_ids)

        faiss.write_index(index, f"{FAISS_PATH}/index.faiss")

        # 🔥 DELETE OLD CHUNKS
        chunks_collection = db.collection("chunks")
        for fid in old_ids:
            #chunk.reference.delete()
            chunks_collection.document(str(fid)).delete()

    # 🔥 STORE NEW DATA
    store_pdf(pdf_path, metadata)

# =========================
# 🔹 DELETE FUNCTION
# =========================
def delete_course(course_id):
    db = get_db()
    course_ref = db.collection("courses").document(course_id)

    doc = course_ref.get()

    if not doc.exists:
        st.error("Course not found")
        return

    data = doc.to_dict()
    faiss_ids = data.get("faiss_ids", [])

    # 🔥 LOAD FAISS
    index = faiss.read_index(f"{FAISS_PATH}/index.faiss")

    if isinstance(index, faiss.IndexIDMap):
        remove_ids = np.array(faiss_ids, dtype=np.int64)
        index.remove_ids(remove_ids)

    faiss.write_index(index, f"{FAISS_PATH}/index.faiss")

    # 🔥 DELETE CHUNKS
    chunks_collection = db.collection("chunks")

    for fid in faiss_ids:
        chunks_collection.document(str(fid)).delete()

    # 🔥 DELETE COURSE DOC
    course_ref.delete()
    st.success("✅ Course deleted successfully from FAISS + Firebase")

def load_course_ids():
    db = get_db()

    courses = db.collection("courses").stream()
#    course_options = {doc.to_dict()["name"]: doc.id for doc in courses}

    course_options = {doc.to_dict()["name"]: doc.to_dict()["id"] for doc in courses}

    return course_options

def get_course_id(course_name):
    db = get_db()
    docs = db.collection("courses").where("name", "==", course_name).stream()
    for doc in docs:
        data = doc.to_dict()
        return data.get("id")

def get_course_details(course_id):
    db = get_db()
    doc = db.collection("courses").document(course_id).get()
    if doc.exists:
        return doc.to_dict()
    return {}

if __name__ == "__main__":

    st.set_page_config(page_title="FV Assisstant", layout="wide")
    st.title("🤖 Future Vision Assistant Ready!")
    
    # Sidebar with options
    option = st.sidebar.selectbox(
        "Choose an option",
        ["Add New Course", "Update Course", "List Courses", "Delete Course", "Add New Course Category", "Ask Questions"]
    )

    if option == "Add New Course":
        pdf = st.file_uploader("Upload course PDF", type=["pdf"])
        if pdf is not None:
            course_name=st.text_input("Enter course name: ")
            categories = get_categories()
            category = st.selectbox("Select Course Category", options=list(categories.values()))
            category_id = get_category_id(category)
            tools_input = st.text_input("Enter tools (comma separated):", placeholder="e.g. Photoshop, Illustrator, Figma")
            level = st.selectbox("Enter course level: ", ["beginner", "intermediate", "advanced"])
            duration = st.number_input("Enter course duration (in months): ", value=0.0, step=0.1, format="%.1f")
            #duration = float(re.search(r"(\d+\.?\d*)", duration).group())
            weeks = st.number_input("Enter course duration (in weeks): ", value=round(duration * 4))
            if level == "beginner":
                hours = st.number_input("Enter course duration (in hours): ", value=round(weeks * 6))
            elif level == "intermediate":
                hours = st.number_input("Enter course duration (in hours): ", value=round(weeks * 9))
            elif level == "advanced":
                hours = st.number_input("Enter course duration (in hours): ", value=round(weeks * 12))
            fees = st.number_input("Enter course fees: ", value=0)
            if st.button("Store Course"):
                new_course_id = store_pdf(
                    pdf_path=save_uploaded_file(pdf),
                    metadata={
                    "name":course_name,
                    "category": category_id,
                    "tools": tools_input,
                    "level": level,
                    "duration": duration,
                    "fees":fees,
                    "weeks":weeks,
                    "hours":hours
                }
            )
                st.success("✅ Stored successfully in FAISS + Firebase! Course ID: " + new_course_id)

    elif option == "Ask Questions":
        query = st.text_input("Ask your query : ")
        if query:
            results = retrieve_data.search(query)

            # ✅ PRINT RESPONSE
            st.success("🤖 Answer:\n")
            st.write(results)

    elif option == "List Courses":
        df = retrieve_data.get_courses_dataframe()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No courses found.")

    elif option == "Update Course":
        course_options = load_course_ids()

        selected_name = st.selectbox("Select Course", list(course_options.keys()))
        course_id = course_options[selected_name]

        if course_id:
            # 🔥 Fetch existing course data
            course_data = get_course_details(course_id)
            
            if course_data:
                pdf = st.file_uploader("Upload new course PDF", type=["pdf"])
                course_name = st.text_input("Enter course name to update: ", value=course_data.get("name", selected_name))
                categories = get_categories()
                category_id = course_data.get("category")
                category_name = get_category_name(category_id)
                category_names = list(categories.values())
                selected_index = category_names.index(category_name) if category_name in category_names else 0
                category = st.selectbox("Select Course Category", options=category_names,
                                        index=selected_index)
                category_id = get_category_id(category)
                level_options = ["beginner", "intermediate", "advanced"]
                level = st.selectbox("Enter course level: ", level_options,
                                    index=level_options.index(course_data.get("level"))
                                    if course_data.get("level") in level_options else 0)

                duration = st.number_input("Enter course duration (in months): ", value=course_data.get("duration", 0.0))
                #duration = float(re.search(r"(\d+\.?\d*)", duration).group())
                
                weeks = st.number_input("Enter course duration (in weeks): ", value=course_data.get("weeks", round(duration * 4)))
                if level == "beginner":
                    hours = st.number_input("Enter course duration (in hours): ", value=course_data.get("hours", 0))
                elif level == "intermediate":
                    hours = st.number_input("Enter course duration (in hours): ", value=course_data.get("hours", 0))
                elif level == "advanced":
                    hours = st.number_input("Enter course duration (in hours): ", value=course_data.get("hours", 0))
                fees = st.number_input("Enter course fees: ", value=course_data.get("fees", 0))
                if st.button("Update Course"):
                    update_course(
                        course_id=course_id,
                        pdf_path=save_uploaded_file(pdf) if pdf else course_data.get("pdf_path"),
                        metadata={
                        "name":course_name,
                        "category": category_id,
                        "level": level,
                        "duration": duration,
                        "fees":fees,
                        "weeks":weeks,
                        "hours":hours
                    }
                )
                    st.success("✅ Course updated successfully in FAISS + Firebase")

    elif option == "Delete Course":
        course_ids = load_course_ids()
        selected_course = st.selectbox("Select Course to Delete:", options=course_ids)
        if selected_course and st.button("Delete Course"):
            course_id = get_course_id(selected_course)
            delete_course(course_id)

    elif option == "Add New Course Category":
        category_form()

