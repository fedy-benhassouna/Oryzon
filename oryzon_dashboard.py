"""
=============================================================================
ORYZON PARTNERS - Panneau de Contrôle Master Rag Agent
=============================================================================
Tableau de bord unifié pour la gestion de :
- Identifiants utilisateurs (authentification pour l'accès au chatbot)
- Base de connaissances (ingestion de documents PDF pour le chatbot)
=============================================================================
"""

import os
import streamlit as st
import warnings
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson.objectid import ObjectId
import bcrypt
from datetime import datetime
import re

# Support PDF
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Charger les variables d'environnement
load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

# Configuration MongoDB
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "admin_db")
MONGO_COLLECTION = os.getenv("COLLECTION_NAME", "users")

# Constantes de validation
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 30
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Branding Oryzon Partners
COMPANY_NAME = "Oryzon Partners"
CHATBOT_NAME = "Master Rag Agent"
PRIMARY_COLOR = "#132338"  # Bleu foncé RGB(19, 35, 56)
ACCENT_COLOR = "#25A587"   # Teal RGB(37, 165, 135)
LOGO_PATH = "logo.png"

# =============================================================================
# CONFIGURATION DE LA PAGE & STYLE
# =============================================================================

st.set_page_config(
    page_title=f"{COMPANY_NAME} - Panneau de Contrôle {CHATBOT_NAME}",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour le branding Oryzon Partners
st.markdown(f"""
<style>
    /* Fond blanc global */
    .stApp {{
        background-color: #FFFFFF;
    }}
    
    /* Forcer le texte blanc dans les en-têtes spécifiques */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] p {{
        color: white !important;
    }}
    
    /* Texte principal en noir/gris foncé */
    .stApp p, .stApp span, .stApp label {{
        color: #333333;
    }}
    
    /* Labels des inputs */
    .stTextInput label, .stSelectbox label, .stNumberInput label, .stCheckbox label, .stRadio label {{
        color: #333333 !important;
    }}
    
    /* Texte dans les formulaires */
    .stTextInput input, .stSelectbox select, .stNumberInput input {{
        color: #333333 !important;
        background-color: #FFFFFF !important;
    }}
    
    /* Style de l'en-tête */
    .main-header {{
        background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, #1a3a4f 100%);
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white !important;
        text-align: center;
    }}
    .main-header h1, .main-header h2, .main-header h3 {{
        color: white !important;
        margin: 0;
        font-size: 2rem;
    }}
    .main-header p {{
        color: #E2E8F0 !important;
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }}
    
    /* En-têtes de section */
    .section-header {{
        background: {PRIMARY_COLOR};
        color: white !important;
        padding: 0.75rem 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }}
    .section-header h1, .section-header h2, .section-header h3, .section-header h4 {{
        color: white !important;
    }}
    .section-header p, .section-header span {{
        color: white !important;
    }}
    
    /* Sous-titres et headers normaux */
    h1, h2, h3, h4, h5, h6 {{
        color: {PRIMARY_COLOR};
    }}
    
    /* File uploader - texte blanc sur fond sombre */
    [data-testid="stFileUploader"] {{
        background: {PRIMARY_COLOR};
        padding: 1rem;
        border-radius: 10px;
    }}
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] div {{
        color: white !important;
    }}
    [data-testid="stFileUploader"] button {{
        background-color: {ACCENT_COLOR} !important;
        color: white !important;
    }}
    
    /* Style des cartes */
    .info-card {{
        background: #FFFFFF;
        border-left: 4px solid {ACCENT_COLOR};
        padding: 1rem;
        border-radius: 0 5px 5px 0;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    /* Style de la barre latérale */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {PRIMARY_COLOR} 0%, #1a3a4f 100%);
    }}
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown span {{
        color: white !important;
    }}
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stRadio p {{
        color: white !important;
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        color: white !important;
    }}
    
    /* Logo avec fond blanc */
    .logo-container {{
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px auto;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }}
    .logo-container img {{
        max-width: 180px;
        height: auto;
    }}
    
    /* Boutons stylisés */
    .stButton > button {{
        background-color: {ACCENT_COLOR} !important;
        color: white !important;
        border: none;
        border-radius: 5px;
    }}
    .stButton > button:hover {{
        background-color: {PRIMARY_COLOR} !important;
        color: white !important;
    }}
    
    /* Onglets */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #f0f2f6;
        border-radius: 5px;
        color: #333333 !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {ACCENT_COLOR} !important;
        color: white !important;
    }}
    
    /* Messages succès/erreur/info/warning */
    .stSuccess {{
        background-color: #D4EDDA !important;
        color: #155724 !important;
        border-left: 4px solid {ACCENT_COLOR};
    }}
    .stError {{
        background-color: #F8D7DA !important;
        color: #721c24 !important;
    }}
    .stInfo {{
        background-color: #D1ECF1 !important;
        color: #0c5460 !important;
    }}
    .stWarning {{
        background-color: #FFF3CD !important;
        color: #856404 !important;
    }}
    
    /* Métriques */
    [data-testid="stMetricValue"] {{
        color: {PRIMARY_COLOR} !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: #333333 !important;
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        color: #333333 !important;
        background-color: #f8f9fa !important;
    }}
    
    /* Selectbox et inputs */
    [data-baseweb="select"] {{
        color: #333333 !important;
    }}
    [data-baseweb="input"] {{
        color: #333333 !important;
    }}
    
    /* Texte dans les code blocks */
    code {{
        color: {PRIMARY_COLOR} !important;
        background-color: #f4f4f4 !important;
    }}
    
    /* Dividers */
    hr {{
        border-color: #e0e0e0 !important;
    }}
    
    /* Captions */
    .stCaption {{
        color: #666666 !important;
    }}
    
    /* Table/Dataframe */
    .stDataFrame {{
        color: #333333 !important;
    }}
    
    /* Form labels */
    .stForm label {{
        color: #333333 !important;
    }}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CONNEXION À LA BASE DE DONNÉES
# =============================================================================

def get_mongo_collection():
    """Initialiser la connexion MongoDB pour la gestion des utilisateurs."""
    try:
        if not MONGO_URI:
            return None, "MONGO_URI non trouvé dans les variables d'environnement"
        
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        
        # Vérifier la connexion
        client.admin.command('ping')
        
        # S'assurer que le nom d'utilisateur est indexé
        collection.create_index("username", unique=True)
        
        return collection, None
    except PyMongoError as e:
        return None, str(e)

# =============================================================================
# FONCTIONS DE MOT DE PASSE
# =============================================================================

def hash_password(password: str) -> str:
    """Hasher un mot de passe avec bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Vérifier un mot de passe contre son hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

# =============================================================================
# FONCTIONS DE VALIDATION
# =============================================================================

def validate_username(username: str) -> tuple[bool, str]:
    """Valider le format et la longueur du nom d'utilisateur."""
    if not username or not isinstance(username, str):
        return False, "Le nom d'utilisateur ne peut pas être vide"
    
    username = username.strip()
    
    if len(username) < MIN_USERNAME_LENGTH:
        return False, f"Le nom d'utilisateur doit contenir au moins {MIN_USERNAME_LENGTH} caractères"
    
    if len(username) > MAX_USERNAME_LENGTH:
        return False, f"Le nom d'utilisateur ne doit pas dépasser {MAX_USERNAME_LENGTH} caractères"
    
    if not re.match(r"^[a-zA-Z0-9._-]+$", username):
        return False, "Le nom d'utilisateur peut uniquement contenir des lettres, chiffres, points, tirets et underscores"
    
    return True, ""

def validate_password(password: str) -> tuple[bool, str]:
    """Valider la force du mot de passe."""
    if not password or not isinstance(password, str):
        return False, "Le mot de passe ne peut pas être vide"
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caractères"
    
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Le mot de passe ne doit pas dépasser {MAX_PASSWORD_LENGTH} caractères"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Le mot de passe doit contenir des majuscules, minuscules et chiffres"
    
    return True, ""

# =============================================================================
# OPÉRATIONS BASE DE DONNÉES UTILISATEURS
# =============================================================================

def get_all_users(collection) -> list:
    """Récupérer tous les utilisateurs de la base de données."""
    try:
        users = collection.find({}, {"username": 1, "password_plain": 1, "password": 1, "_id": 0}).sort("username", 1)
        return list(users)
    except PyMongoError as e:
        st.error(f"❌ Échec de la récupération des utilisateurs : {str(e)}")
        return []

def user_exists(collection, username: str) -> bool:
    """Vérifier si un utilisateur existe."""
    try:
        return collection.find_one({"username": username}) is not None
    except PyMongoError:
        return False

def add_user(collection, username: str, password: str) -> tuple[bool, str]:
    """Ajouter un nouvel utilisateur à la base de données."""
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        return False, error_msg
    
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return False, error_msg
    
    if user_exists(collection, username):
        return False, f"L'utilisateur '{username}' existe déjà"
    
    try:
        hashed_password = hash_password(password)
        collection.insert_one({
            "username": username,
            "password_plain": password,
            "password": hashed_password,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        return True, f"Utilisateur '{username}' créé avec succès"
    except PyMongoError as e:
        return False, f"Erreur base de données : {str(e)}"

def edit_user(collection, old_username: str, new_username: str, new_password: str) -> tuple[bool, str]:
    """Modifier un utilisateur existant."""
    if new_username != old_username:
        is_valid, error_msg = validate_username(new_username)
        if not is_valid:
            return False, error_msg
        
        if user_exists(collection, new_username):
            return False, f"Le nom d'utilisateur '{new_username}' existe déjà"
    
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        return False, error_msg
    
    try:
        hashed_password = hash_password(new_password)
        result = collection.update_one(
            {"username": old_username},
            {
                "$set": {
                    "username": new_username,
                    "password_plain": new_password,
                    "password": hashed_password,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            return False, f"Utilisateur '{old_username}' non trouvé"
        
        if new_username != old_username:
            return True, f"Utilisateur mis à jour : '{old_username}' → '{new_username}'"
        else:
            return True, f"Mot de passe mis à jour pour '{new_username}'"
    except PyMongoError as e:
        return False, f"Erreur base de données : {str(e)}"

def delete_user(collection, username: str) -> tuple[bool, str]:
    """Supprimer un utilisateur de la base de données."""
    try:
        result = collection.delete_one({"username": username})
        
        if result.deleted_count == 0:
            return False, f"Utilisateur '{username}' non trouvé"
        
        return True, f"Utilisateur '{username}' supprimé avec succès"
    except PyMongoError as e:
        return False, f"Erreur base de données : {str(e)}"

# =============================================================================
# FONCTIONS BASE DE CONNAISSANCES
# =============================================================================

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Diviser le texte en chunks chevauchants."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks

def extract_text_from_pdf(uploaded_file):
    """Extraire le texte d'un fichier PDF téléchargé."""
    if not PDF_SUPPORT:
        return None, "Le support PDF nécessite 'pdfplumber'. Installez avec : pip install pdfplumber"
    
    try:
        content = ""
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*FontBBox.*")
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    content += page.extract_text() or ""
                    content += "\n\n"
        return content, None
    except Exception as e:
        return None, f"Erreur lors de la lecture du PDF : {e}"

def extract_text_from_file(uploaded_file):
    """Extraire le texte d'un fichier texte téléchargé."""
    try:
        content = uploaded_file.read().decode("utf-8")
        return content, None
    except UnicodeDecodeError:
        try:
            uploaded_file.seek(0)
            content = uploaded_file.read().decode("latin-1")
            return content, None
        except Exception as e:
            return None, f"Erreur lors de la lecture du fichier : {e}"

# =============================================================================
# NAVIGATION BARRE LATÉRALE
# =============================================================================

def render_sidebar():
    """Afficher la navigation de la barre latérale."""
    with st.sidebar:
        # Logo avec fond blanc
        try:
            import base64
            from pathlib import Path
            
            logo_path = Path(LOGO_PATH)
            if logo_path.exists():
                with open(logo_path, "rb") as f:
                    logo_data = base64.b64encode(f.read()).decode()
                st.markdown(f"""
                <div style='background-color: white; padding: 15px; border-radius: 10px; margin: 10px 0; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.15);'>
                    <img src='data:image/png;base64,{logo_data}' style='max-width: 180px; height: auto;'>
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            pass
        
        # Titre du chatbot
        st.markdown(f"""
        <div style='text-align: center; padding: 0.5rem 0;'>
            <h2 style='color: white !important; margin: 0; font-size: 1.3rem;'>🤖 {CHATBOT_NAME}</h2>
            <p style='color: {ACCENT_COLOR} !important; font-size: 0.9rem;'>Panneau de Contrôle</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation
        st.markdown("<p style='color: white !important; font-weight: bold;'>📌 Navigation</p>", unsafe_allow_html=True)
        
        section = st.radio(
            "Sélectionner une section :",
            ["🔐 Identifiants Utilisateurs", "📚 Base de Connaissances"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Info entreprise
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem 0;'>
            <p style='color: #E2E8F0; font-size: 0.8rem;'>Propulsé par</p>
            <h3 style='color: {ACCENT_COLOR}; margin: 0;'>{COMPANY_NAME}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        return section

# =============================================================================
# SECTION IDENTIFIANTS UTILISATEURS
# =============================================================================

def render_credentials_section(collection):
    """Afficher la section de gestion des identifiants utilisateurs."""
    
    st.markdown(f"""
    <div style='background: {PRIMARY_COLOR}; padding: 0.75rem 1rem; border-radius: 5px; margin: 1rem 0;'>
        <div style='margin: 0; color: #FFFFFF; font-size: 1.2rem; font-weight: bold;'>🔐 <span style='color: #FFFFFF;'>{CHATBOT_NAME} - Identifiants Utilisateurs</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"Gérez les identifiants d'authentification pour les utilisateurs accédant à **{CHATBOT_NAME}**")
    
    # Sous-onglets pour les opérations sur les identifiants
    cred_tab1, cred_tab2, cred_tab3, cred_tab4 = st.tabs([
        "📋 Voir Utilisateurs", "➕ Ajouter", "✏️ Modifier", "🗑️ Supprimer"
    ])
    
    # ===== VOIR UTILISATEURS =====
    with cred_tab1:
        st.subheader("Utilisateurs Enregistrés")
        users = get_all_users(collection)
        
        if users:
            st.write(f"**Total Utilisateurs : {len(users)}**")
            st.markdown("---")
            
            for idx, user in enumerate(users, 1):
                username = user.get("username", "N/A")
                password = user.get("password_plain") or user.get("password", "N/A")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(f"**{idx}. Nom d'utilisateur :**")
                    st.code(username)
                with col2:
                    st.markdown(f"**Mot de passe :**")
                    st.code(password)
                st.divider()
        else:
            st.info("📭 Aucun utilisateur trouvé. Ajoutez un utilisateur dans l'onglet 'Ajouter'.")
    
    # ===== AJOUTER UTILISATEUR =====
    with cred_tab2:
        st.subheader("Créer un Nouvel Utilisateur")
        st.markdown(f"Ajouter un nouvel utilisateur pouvant accéder à **{CHATBOT_NAME}**")
        
        with st.form("add_user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input(
                    "Nom d'utilisateur",
                    placeholder="Entrez le nom d'utilisateur (3-30 caractères)",
                    help="Lettres, chiffres, points, tirets et underscores autorisés"
                )
            
            with col2:
                new_password = st.text_input(
                    "Mot de passe",
                    type="password",
                    placeholder="Entrez le mot de passe (8+ caractères)",
                    help="Doit contenir majuscules, minuscules et chiffres"
                )
            
            submitted = st.form_submit_button("➕ Créer Utilisateur", use_container_width=True)
            
            if submitted:
                success, message = add_user(collection, new_username, new_password)
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    # ===== MODIFIER UTILISATEUR =====
    with cred_tab3:
        st.subheader("Modifier un Utilisateur Existant")
        
        users = get_all_users(collection)
        
        if users:
            usernames = [user["username"] for user in users]
            
            with st.form("edit_user_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    selected_user = st.selectbox(
                        "Sélectionner l'utilisateur à modifier",
                        usernames,
                        key="edit_user_select"
                    )
                
                with col2:
                    new_username = st.text_input(
                        "Nouveau nom d'utilisateur",
                        value=selected_user if selected_user else "",
                        help="Laisser identique pour conserver le nom actuel"
                    )
                
                new_password = st.text_input(
                    "Nouveau mot de passe",
                    type="password",
                    placeholder="Entrez le nouveau mot de passe",
                    help="Obligatoire. Doit contenir majuscules, minuscules et chiffres"
                )
                
                submitted = st.form_submit_button("✏️ Mettre à jour", use_container_width=True)
                
                if submitted:
                    if not new_username:
                        st.error("Le nom d'utilisateur ne peut pas être vide")
                    elif not new_password:
                        st.error("Le mot de passe est obligatoire")
                    else:
                        success, message = edit_user(
                            collection,
                            selected_user,
                            new_username.strip(),
                            new_password
                        )
                        if success:
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
        else:
            st.info("📭 Aucun utilisateur disponible à modifier")
    
    # ===== SUPPRIMER UTILISATEUR =====
    with cred_tab4:
        st.subheader("Supprimer un Utilisateur")
        
        users = get_all_users(collection)
        
        if users:
            usernames = [user["username"] for user in users]
            st.warning("⚠️ Cette action est permanente et irréversible")
            
            with st.form("delete_user_form"):
                user_to_delete = st.selectbox(
                    "Sélectionner l'utilisateur à supprimer",
                    usernames,
                    key="delete_user_select"
                )
                
                confirm = st.checkbox(
                    f"Je confirme vouloir supprimer '{user_to_delete}'",
                    value=False
                )
                
                submitted = st.form_submit_button("🗑️ Supprimer", use_container_width=True)
                
                if submitted:
                    if not confirm:
                        st.error("❌ Veuillez confirmer la suppression")
                    else:
                        success, message = delete_user(collection, user_to_delete)
                        if success:
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
        else:
            st.info("📭 Aucun utilisateur disponible à supprimer")

# =============================================================================
# SECTION BASE DE CONNAISSANCES
# =============================================================================

def render_knowledge_section():
    """Afficher la section de gestion de la base de connaissances."""
    
    st.markdown(f"""
    <div style='background: {PRIMARY_COLOR}; padding: 0.75rem 1rem; border-radius: 5px; margin: 1rem 0;'>
        <div style='margin: 0; color: #FFFFFF; font-size: 1.2rem; font-weight: bold;'>📚 <span style='color: #FFFFFF;'>{CHATBOT_NAME} - Base de Connaissances</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"Gérez les documents de connaissances qui alimentent l'intelligence de **{CHATBOT_NAME}**")
    
    # Sous-onglets pour les opérations sur les connaissances
    kb_tab1, kb_tab2, kb_tab3 = st.tabs([
        "📤 Ajouter Document", "🗑️ Supprimer Document", "📋 Voir Documents"
    ])
    
    # ===== AJOUTER DOCUMENT =====
    with kb_tab1:
        st.subheader("Télécharger un Nouveau Document")
        
        st.info("📄 Téléchargez des fichiers PDF ou texte pour les ajouter à la base de connaissances du chatbot")
        
        uploaded_file = st.file_uploader(
            "Sélectionner un fichier à télécharger",
            type=["pdf", "txt", "md", "json"],
            help="Formats supportés : PDF, TXT, MD, JSON"
        )
        
        custom_title = st.text_input(
            "Titre du Document (optionnel)",
            placeholder="Laisser vide pour utiliser le nom du fichier"
        )
        
        # Paramètres de chunking
        with st.expander("⚙️ Paramètres Avancés"):
            col1, col2 = st.columns(2)
            with col1:
                chunk_size = st.number_input("Taille du Chunk", min_value=100, max_value=5000, value=1000)
            with col2:
                overlap = st.number_input("Chevauchement", min_value=0, max_value=500, value=200)
        
        if uploaded_file is not None:
            file_name = uploaded_file.name
            file_extension = Path(file_name).suffix.lower()
            title = custom_title if custom_title else Path(file_name).stem
            
            st.markdown(f"**📁 Fichier :** `{file_name}`")
            
            # Extraire le texte
            if file_extension == ".pdf":
                with st.spinner("Extraction du texte du PDF..."):
                    content, error = extract_text_from_pdf(uploaded_file)
            else:
                with st.spinner("Lecture du fichier texte..."):
                    content, error = extract_text_from_file(uploaded_file)
            
            if error:
                st.error(f"❌ {error}")
            elif content:
                # Aperçu du texte
                with st.expander("📄 Aperçu du Texte", expanded=False):
                    st.text_area(
                        "Texte Extrait",
                        content[:5000] + ("..." if len(content) > 5000 else ""),
                        height=200,
                        disabled=True
                    )
                
                # Créer les chunks
                chunks = chunk_text(content, chunk_size, overlap)
                
                st.success("✅ Texte extrait avec succès !")
                
                # Statistiques
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Caractères", f"{len(content):,}")
                with col2:
                    st.metric("Nombre de Chunks", len(chunks))
                with col3:
                    avg_size = sum(len(c) for c in chunks) / len(chunks) if chunks else 0
                    st.metric("Taille Moyenne", f"{avg_size:.0f}")
                
                st.markdown("---")
                
                # Aperçu des chunks
                st.subheader("📦 Aperçu des Chunks")
                if chunks:
                    display_chunks = chunks[:5]
                    tabs = st.tabs([f"Chunk {i+1}" for i in range(len(display_chunks))])
                    
                    for i, (tab, chunk) in enumerate(zip(tabs, display_chunks)):
                        with tab:
                            st.text_area(
                                f"Chunk {i+1} ({len(chunk)} car.)",
                                chunk,
                                height=150,
                                key=f"chunk_{i}"
                            )
                    
                    if len(chunks) > 5:
                        st.info(f"ℹ️ Affichage de 5 sur {len(chunks)} chunks")
                
                st.markdown("---")
                
                # Résumé du document
                st.subheader("📊 Résumé du Document")
                st.json({
                    "titre": title,
                    "fichier_source": file_name,
                    "total_chunks": len(chunks),
                    "taille_chunk": chunk_size,
                    "chevauchement": overlap,
                    "pret_pour_upload": True
                })
                
                # Bouton d'upload
                if st.button("🚀 Envoyer à la Base de Connaissances", use_container_width=True, type="primary"):
                    st.warning("⚠️ **Intégration Requise** : Connectez ceci à votre instance Qdrant pour télécharger les documents.")
                    st.info("Le document découpé est prêt pour l'ingestion. Implémentez la fonction d'upload Qdrant pour activer cette fonctionnalité.")
    
    # ===== SUPPRIMER DOCUMENT =====
    with kb_tab2:
        st.subheader("Supprimer un Document de la Base")
        
        st.warning("⚠️ Cette action supprimera le document des connaissances du chatbot")
        
        remove_method = st.radio(
            "Supprimer par :",
            ["Fichier Source", "Titre du Document", "ID du Point"],
            horizontal=True
        )
        
        if remove_method == "Fichier Source":
            source_file = st.text_input(
                "Chemin du Fichier Source",
                placeholder="ex: AI Prompt/Landing Page.pdf"
            )
            
            if source_file and st.button("🗑️ Supprimer le Document", use_container_width=True):
                st.warning("⚠️ **Intégration Requise** : Connectez ceci à votre instance Qdrant pour supprimer les documents.")
                st.json({
                    "action": "supprimer_par_source",
                    "fichier_source": source_file,
                    "statut": "EN ATTENTE - Intégration Qdrant nécessaire"
                })
        
        elif remove_method == "Titre du Document":
            doc_title = st.text_input(
                "Titre du Document",
                placeholder="ex: Landing Page"
            )
            
            if doc_title and st.button("🗑️ Supprimer le Document", use_container_width=True):
                st.warning("⚠️ **Intégration Requise** : Connectez ceci à votre instance Qdrant pour supprimer les documents.")
                st.json({
                    "action": "supprimer_par_titre",
                    "titre_document": doc_title,
                    "statut": "EN ATTENTE - Intégration Qdrant nécessaire"
                })
        
        else:
            point_id = st.number_input("ID du Point", min_value=0, value=0, step=1)
            
            if st.button("🗑️ Supprimer le Point", use_container_width=True):
                st.warning("⚠️ **Intégration Requise** : Connectez ceci à votre instance Qdrant pour supprimer les documents.")
                st.json({
                    "action": "supprimer_par_id",
                    "id_point": point_id,
                    "statut": "EN ATTENTE - Intégration Qdrant nécessaire"
                })
    
    # ===== VOIR DOCUMENTS =====
    with kb_tab3:
        st.subheader("Documents de la Base de Connaissances")
        
        st.info("ℹ️ Connectez-vous à Qdrant pour voir les documents réels. Affichage de données exemple ci-dessous.")
        
        # Données exemple
        import pandas as pd
        sample_docs = [
            {"titre": "Guide Landing Page", "source": "AI Prompt/Landing Page.pdf", "chunks": 15, "statut": "Actif"},
            {"titre": "Guide Produits", "source": "Produits/guide.pdf", "chunks": 23, "statut": "Actif"},
            {"titre": "Aperçu FBA", "source": "Expédition/fba.pdf", "chunks": 18, "statut": "Actif"},
            {"titre": "FAQ Vendeur", "source": "Aide/faq.md", "chunks": 12, "statut": "Actif"},
        ]
        
        df = pd.DataFrame(sample_docs)
        df.columns = ["Titre du Document", "Fichier Source", "Chunks", "Statut"]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Statistiques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Documents", len(sample_docs))
        with col2:
            st.metric("Total Chunks", sum(d["chunks"] for d in sample_docs))
        with col3:
            st.metric("Statut", "Données Exemple")
        
        st.caption("⚠️ Ceci est des données exemple. Connectez-vous à Qdrant pour voir les documents réels.")

# =============================================================================
# APPLICATION PRINCIPALE
# =============================================================================

def main():
    """Point d'entrée principal de l'application."""
    
    # Charger le logo en base64 pour l'en-tête
    logo_b64 = ""
    try:
        from pathlib import Path
        import base64
        logo_path = Path(LOGO_PATH)
        if logo_path.exists():
            with open(logo_path, "rb") as f:
                logo_b64 = base64.b64encode(f.read()).decode()
    except Exception:
        pass
    
    # En-tête avec logo
    if logo_b64:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, #1a3a4f 100%); padding: 1.5rem 2rem; border-radius: 10px; margin-bottom: 2rem; text-align: center;'>
            <div style='background-color: white; display: inline-block; padding: 10px 20px; border-radius: 8px; margin-bottom: 10px;'>
                <img src='data:image/png;base64,{logo_b64}' style='max-height: 60px; width: auto;'>
            </div>
            <div style='color: #FFFFFF; margin: 0; font-size: 2rem; font-weight: bold;'>🤖 <span style='color: #FFFFFF;'>{CHATBOT_NAME}</span></div>
            <div style='color: #FFFFFF; margin: 0.5rem 0 0 0; font-size: 1rem;'><span style='color: #FFFFFF;'>Panneau de Contrôle | {COMPANY_NAME}</span></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, #1a3a4f 100%); padding: 1.5rem 2rem; border-radius: 10px; margin-bottom: 2rem; text-align: center;'>
            <div style='color: #FFFFFF; margin: 0; font-size: 2rem; font-weight: bold;'>🤖 <span style='color: #FFFFFF;'>{CHATBOT_NAME}</span></div>
            <div style='color: #FFFFFF; margin: 0.5rem 0 0 0; font-size: 1rem;'><span style='color: #FFFFFF;'>Panneau de Contrôle | {COMPANY_NAME}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    # Navigation barre latérale
    section = render_sidebar()
    
    # Connexion MongoDB (pour les identifiants)
    collection, error = get_mongo_collection()
    
    # Afficher la section sélectionnée
    if section == "🔐 Identifiants Utilisateurs":
        if collection is None:
            st.error(f"❌ Échec de connexion à la base de données : {error}")
            st.warning("Veuillez vérifier votre configuration MongoDB dans le fichier .env")
        else:
            st.success("✅ Connecté à MongoDB")
            render_credentials_section(collection)
    
    elif section == "📚 Base de Connaissances":
        render_knowledge_section()
    
    # Pied de page avec logo
    st.markdown("---")
    if logo_b64:
        st.markdown(f"""
        <div style='text-align: center; color: #888; font-size: 0.8rem; padding: 1rem 0;'>
            <div style='background-color: #f8f9fa; display: inline-block; padding: 8px 15px; border-radius: 5px; margin-bottom: 10px;'>
                <img src='data:image/png;base64,{logo_b64}' style='max-height: 30px; width: auto;'>
            </div>
            <p><strong>{CHATBOT_NAME}</strong> - Panneau de Contrôle</p>
            <p>© 2026 {COMPANY_NAME} | Tous Droits Réservés</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='text-align: center; color: #888; font-size: 0.8rem; padding: 1rem 0;'>
            <p><strong>{CHATBOT_NAME}</strong> - Panneau de Contrôle</p>
            <p>© 2026 {COMPANY_NAME} | Tous Droits Réservés</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
