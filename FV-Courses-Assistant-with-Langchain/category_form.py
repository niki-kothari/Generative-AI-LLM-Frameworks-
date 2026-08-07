import streamlit as st
import uuid
from firebase_config import get_db


def category_form():
    db = get_db()
    COLLECTION_NAME = "course_category"

    st.set_page_config(page_title="Category Manager", layout="wide")
    st.title("📚 Course Category Manager")


    # ==============================
    # ➕ ADD CATEGORY
    # ==============================
    st.subheader("➕ Add New Category")

    with st.form("add_category_form"):
        name = st.text_input("Category Name")
        description = st.text_area("Description")
        submit = st.form_submit_button("Add Category")

        if submit:
            if name.strip() == "":
                st.warning("⚠️ Category name is required!")
            else:
                category_id = str(uuid.uuid4())
                data = {
                    "id": category_id,
                    "name": name,
                    "description": description
                }
                db.collection(COLLECTION_NAME).document(category_id).set(data)
                st.success("✅ Category added successfully!")


    # ==============================
    # 📋 LIST CATEGORIES
    # ==============================
    st.subheader("📋 All Categories")

    docs = db.collection(COLLECTION_NAME).stream()
    categories = [doc.to_dict() for doc in docs]

    if categories:
        for cat in categories:
            with st.expander(f"📌 {cat['name']}"):
                st.write(f"**ID:** {cat['id']}")
                st.write(f"**Description:** {cat.get('description', '')}")

                col1, col2 = st.columns(2)

                # ==============================
                # ✏️ UPDATE
                # ==============================
                with col1:
                    with st.form(f"update_{cat['id']}"):
                        new_name = st.text_input("New Name", value=cat["name"])
                        new_desc = st.text_area("New Description", value=cat.get("description", ""))
                        update_btn = st.form_submit_button("Update")

                        if update_btn:
                            db.collection(COLLECTION_NAME).document(cat["id"]).update({
                                "name": new_name,
                                "description": new_desc
                            })
                            st.success("✅ Updated successfully!")
                            st.rerun()

                # ==============================
                # ❌ DELETE
                # ==============================
                with col2:
                    if st.button("Delete", key=cat["id"]):
                        db.collection(COLLECTION_NAME).document(cat["id"]).delete()
                        st.warning("🗑️ Category deleted!")
                        st.rerun()
    else:
        st.info("No categories found.")

def get_categories():
    db = get_db()
    docs =db.collection("course_category").stream()

    categories = {}
    for doc in docs:
        data = doc.to_dict()
        categories[doc.id] = data.get("name", "")

    return categories

def get_category_id(category):
    db = get_db()
    docs = db.collection("course_category").where("name", "==", category).stream()
    for doc in docs:
        data = doc.to_dict()
        return data.get("id")

    return None  # If not found

def get_category_name(category_id):
    db = get_db()
    docs = db.collection("course_category").where("id", "==", category_id).stream()
    for doc in docs:
        data = doc.to_dict()
        return data.get("name")
    
    return None  # If not found
