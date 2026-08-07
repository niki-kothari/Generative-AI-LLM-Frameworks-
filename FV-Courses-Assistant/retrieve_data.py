import os
from pathlib import Path
from dotenv import load_dotenv
import faiss
import pandas as pd
import numpy as np
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from collections import defaultdict
from firebase_config import get_db
from category_form import get_categories, get_category_name

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
FAISS_PATH = BASE_DIR / "data" / "faiss_index"

# =========================
# 🔹 LOAD FAISS
# =========================
def load_faiss():
    return faiss.read_index(f"{FAISS_PATH}/index.faiss")

# =========================
# 🔹 ANALYZE QUERY
# =========================
def analyze_query(query, categories):
    db = get_db()
    query_lower = query.lower()

    detected_category = None
    matched_tools = []
    matched_keywords = []

    # 🔹 Detect category
    for cat_id, cat_name in categories.items():
        if cat_name in query_lower:
            detected_category = cat_id
            break

    # 🔹 Collect all tools & keywords from DB
    course_docs = db.collection("courses").stream()

    all_tools = set()
    all_keywords = set()

    for doc in course_docs:
        data = doc.to_dict()
        all_tools.update([t.lower() for t in data.get("tools", [])])
        all_keywords.update([k.lower() for k in data.get("keywords", [])])

    # 🔹 Match tools
    for tool in all_tools:
        if tool in query_lower:
            matched_tools.append(tool)

    # 🔹 Match keywords
    for keyword in all_keywords:
        if keyword in query_lower:
            matched_keywords.append(keyword)

    return detected_category, matched_tools, matched_keywords


# =========================
# 🔹 MAIN SEARCH
# =========================
def search(query, top_k=30):

    db = get_db()
    index = load_faiss()
    embedding_model = OpenAIEmbeddings()

    query_lower = query.lower()

    # =========================
    # 🔹 1. LOAD CATEGORIES
    # =========================
    categories = get_categories()

    # =========================
    # 🔹 2. ANALYZE QUERY
    # =========================
    detected_category, matched_tools, matched_keywords = analyze_query(query, categories)

    # Decide filtering mode
    USE_FILTER = False
    if detected_category or matched_tools or matched_keywords:
        USE_FILTER = True

    # =========================
    # 🔹 3. FIRESTORE PRE-FILTER
    # =========================
    course_docs = list(db.collection("courses").stream())
    filtered_course_ids = set()

    if USE_FILTER:
        for doc in course_docs:
            course = doc.to_dict()

            # 🔹 Category filter
            if detected_category and course.get("category") != detected_category:
                continue

            # 🔹 Tool match
            tools = [t.lower() for t in course.get("tools", [])]
            if any(t in matched_tools for t in tools):
                filtered_course_ids.add(doc.id)
                continue

            # 🔹 Keyword match
            keywords = [k.lower() for k in course.get("keywords", [])]
            if any(k in matched_keywords for k in keywords):
                filtered_course_ids.add(doc.id)
                continue

            # 🔹 Only category match
            if detected_category:
                filtered_course_ids.add(doc.id)
    else:
        # No signals → allow all courses
        for doc in course_docs:
            filtered_course_ids.add(doc.id)

    # =========================
    # 🔹 4. VECTOR SEARCH (FAISS)
    # =========================
    query_vec = embedding_model.embed_query(query)
    query_vec = np.array([query_vec]).astype("float32")

    distances, indices = index.search(query_vec, top_k)

    hybrid_results = []

    # =========================
    # 🔹 5. FILTER FAISS RESULTS
    # =========================
    for i, idx in enumerate(indices[0]):

        if idx == -1:
            continue

        chunk_doc = db.collection("chunks").document(str(idx)).get()
        if not chunk_doc.exists:
            continue

        chunk = chunk_doc.to_dict()
        course_id = chunk.get("course_id")

        # 🔥 Restrict to filtered courses
        if course_id not in filtered_course_ids:
            continue

        course_doc = db.collection("courses").document(course_id).get()
        if not course_doc.exists:
            continue

        course = course_doc.to_dict()

        # =========================
        # 🔹 SCORING
        # =========================
        distance = distances[0][i]
        vector_score = 1 / (1 + distance)

        keywords = set([k.lower() for k in course.get("keywords", [])])
        keyword_matches = sum(1 for k in keywords if k in query_lower)
        keyword_score = keyword_matches / (len(keywords) + 1e-5)

        tool_boost = 0
        for tool in course.get("tools", []):
            if tool.lower() in query_lower:
                tool_boost += 0.2

        final_score = (0.6 * vector_score) + (0.3 * keyword_score) + tool_boost

        hybrid_results.append((final_score, chunk, course, course_id))

    # =========================
    # 🔹 6. GROUP BY COURSE
    # =========================
    course_scores = defaultdict(list)
    course_info = {}

    for score, chunk, course, course_id in hybrid_results:
        course_scores[course_id].append(score)
        course_info[course_id] = course

    ranked_courses = []

    for course_id, scores in course_scores.items():
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)

        final_course_score = (0.7 * max_score) + (0.3 * avg_score)
        ranked_courses.append((final_course_score, course_id))

    ranked_courses.sort(key=lambda x: x[0], reverse=True)

    # =========================
    # 🔹 7. FILTER LOW SCORES
    # =========================
    FILTER_THRESHOLD = 0.35

    filtered_courses = [
        (score, cid) for score, cid in ranked_courses
        if score >= FILTER_THRESHOLD
    ]

    if not filtered_courses:
        return "Sorry, we do not have any courses matching your request."

    # =========================
    # 🔹 8. BUILD CONTEXT
    # =========================
    context_text = ""

    #for score, course_id in filtered_courses[:7]:
    for score, course_id in filtered_courses:
        course = course_info[course_id]

        category_id = course.get("category")
        category_name = categories.get(category_id, "Unknown")

        context_text += f"""
        Course: {course.get("name")}
        Level: {course.get("level")}
        Category: {category_name}
        Fees: {course.get("fees")}
        Duration: {course.get("duration")}
        Tools: {course.get("tools")}
        """

    # =========================
    # 🔹 9. LLM RESPONSE
    # =========================
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )

    prompt = f"""
    You are a course advisor for "Future Vision Computer Institute".

    User Query:
    {query}

    Available Courses (ONLY source of truth):
    {context_text}

    STRICT RULES:
    - List ALL RELEVANT courses catgory wise
    - Dont repeat the course
    - Use EXACT course names
    - DO NOT add anything outside context
    - Sort the courses according to levels
    - If nothing relevant, say:
      "Sorry, we do not have any courses matching your request."
    - If the query is not related to course, if it is general query, dont give the answer in the below given response format. Just answer in general terms.

    RESPONSE FORMAT:
    - Course Name
    - Fees
    - Duration
    - Category
    - Tools
    - Level
    - Short Introduction

    Keep it clean and short.
    """

    response = llm.invoke(prompt)

    return response.content


def get_courses_dataframe():
    db = get_db()
    courses_ref = db.collection("courses")
    docs = courses_ref.stream()

    data = []

    for doc in docs:
        course = doc.to_dict()

        filtered_course = {
            "Name": course.get("name"),
            "ID": course.get("id"),
            "Category": get_category_name(course.get("category")),
            "Fees": course.get("fees"),
            "Duration": course.get("duration"),
            "Level": course.get("level"),
            "Tools": ", ".join(course.get("tools", [])) if isinstance(course.get("tools"), list) else course.get("tools")
        }
        data.append(filtered_course)

    df = pd.DataFrame(data)
    return df

