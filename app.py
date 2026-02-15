"""
🎙️ StoryForge Audio Builder - Streamlit Version
Generador de Audiolibros con IA usando Groq + Edge TTS
"""

import streamlit as st
import asyncio
import edge_tts
import os
import re
from datetime import datetime
import json

# ============================================
# SISTEMA DE AUTENTICACIÓN
# ============================================

# Credenciales de acceso
VALID_USERNAME = "pedrotorres"
VALID_PASSWORD = "860059h"

# Inicializar estado de autenticación
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Función de autenticación
def check_authentication():
    """Verifica si el usuario está autenticado"""
    if st.session_state.authenticated:
        return True
    
    # Configuración de página para login
    st.set_page_config(
        page_title="🔐 Login - StoryForge",
        page_icon="🔐",
        layout="centered"
    )
    
    # Estilo para la página de login
    st.markdown("""
        <style>
        .login-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 3rem;
            border-radius: 1rem;
            text-align: center;
            margin-top: 5rem;
        }
        .login-title {
            color: white;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .login-subtitle {
            color: #e0e0e0;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Contenedor de login
    st.markdown("""
        <div class='login-container'>
            <div class='login-title'>🎙️ StoryForge Audio Builder</div>
            <div class='login-subtitle'>Acceso Premium</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Formulario de login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("🔐 Iniciar Sesión")
        
        username = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
        password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingresa tu contraseña")
        
        if st.button("🚀 Ingresar", use_container_width=True, type="primary"):
            if username == VALID_USERNAME and password == VALID_PASSWORD:
                st.session_state.authenticated = True
                st.success("✅ ¡Acceso concedido! Bienvenido a StoryForge")
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
        
        st.divider()
        
        st.info("""
        **ℹ️ Información de Acceso:**
        
        Si compraste StoryForge, recibiste tus credenciales por email.
        
        ¿Problemas para acceder? Revisa tu email de compra o contáctanos.
        """)
        
        st.markdown("""
            <div style='text-align: center; margin-top: 2rem; color: #666;'>
                <p>🎙️ StoryForge Audio Builder - Premium Access</p>
                <p style='font-size: 0.9rem;'>Powered by Groq + Edge TTS</p>
            </div>
        """, unsafe_allow_html=True)
    
    return False

# Verificar autenticación antes de mostrar la app
if not check_authentication():
    st.stop()

# ============================================
# APLICACIÓN PRINCIPAL
# ============================================

def clean_text_for_audio(text):
    """Limpia el texto de formato markdown para audio natural"""
    # Eliminar asteriscos (negritas, cursivas)
    text = re.sub(r'\*{1,3}', '', text)
    # Eliminar guiones bajos (cursivas/negritas markdown)
    text = re.sub(r'_{1,3}(?=\S)', '', text)
    text = re.sub(r'(?<=\S)_{1,3}', '', text)
    # Eliminar encabezados markdown (## Título -> Título)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # Convertir viñetas (-, *, •, números) en texto continuo con punto y seguido
    lines = text.split('\n')
    cleaned_lines = []
    in_list = False
    list_items = []
    
    for line in lines:
        stripped = line.strip()
        # Detectar si es una viñeta
        is_bullet = bool(re.match(r'^[\-\*•]\s+', stripped)) or bool(re.match(r'^\d+[\.\)]\s+', stripped))
        
        if is_bullet:
            # Limpiar el marcador de viñeta
            item = re.sub(r'^[\-\*•]\s+', '', stripped)
            item = re.sub(r'^\d+[\.\)]\s+', '', item)
            item = item.strip()
            if item:
                list_items.append(item)
            in_list = True
        else:
            # Si salimos de una lista, unir los items en un párrafo
            if in_list and list_items:
                # Unir items con punto y seguido
                paragraph = '. '.join(
                    item.rstrip('.') for item in list_items
                ) + '.'
                cleaned_lines.append(paragraph)
                list_items = []
                in_list = False
            if stripped:
                cleaned_lines.append(stripped)
            elif cleaned_lines and cleaned_lines[-1] != '':
                cleaned_lines.append('')
    
    # Si terminó en lista
    if list_items:
        paragraph = '. '.join(item.rstrip('.') for item in list_items) + '.'
        cleaned_lines.append(paragraph)
    
    text = '\n'.join(cleaned_lines)
    # Limpiar espacios múltiples
    text = re.sub(r' {2,}', ' ', text)
    # Limpiar saltos de línea excesivos
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# Configuración de la página
st.set_page_config(
    page_title="🎙️ StoryForge Audio Builder",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.75rem;
        font-size: 1.1rem;
    }
    .stButton>button:hover {
        opacity: 0.9;
    }
    .prompt-box {
        background: #f7fafc;
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: 'Courier New', monospace;
        margin: 1rem 0;
        color: #000000;
    }
    .success-box {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar session state
if 'generated_story' not in st.session_state:
    st.session_state.generated_story = ""
if 'audio_generated' not in st.session_state:
    st.session_state.audio_generated = False

# Header
st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 0.5rem; margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0;'>🎙️ StoryForge Audio Builder</h1>
        <p style='color: #e0e0e0; margin: 0.5rem 0 0 0;'>
            Generador de Audiolibros con IA - Groq + Edge TTS
        </p>
    </div>
""", unsafe_allow_html=True)

# Sidebar - API Configuration
with st.sidebar:
    # Info del usuario
    st.success(f"✅ Sesión activa: **{VALID_USERNAME}**")
    
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
    
    st.divider()
    
    st.header("⚙️ Configuración")
    
    api_key = st.text_input(
        "🔑 API Key de Groq",
        type="password",
        help="Obtén tu API key gratis en console.groq.com"
    )
    
    if not api_key:
        st.warning("⚠️ Ingresa tu API key de Groq para comenzar")
        st.markdown("[🔗 Obtener API Key](https://console.groq.com)")
    else:
        st.success("✅ API key configurada")
    
    st.divider()
    
    st.header("ℹ️ Información")
    st.info("""
    **Características:**
    - ✅ 8 tipos de contenido
    - ✅ Generación ultra-rápida
    - ✅ Audio con voces naturales
    - ✅ Exportación MP3
    - ✅ 100% gratis de usar
    """)

# Main content
col1, col2 = st.columns([1, 1])

# LEFT COLUMN - Prompt Builder
with col1:
    st.header("📝 Constructor de Prompts")
    
    # Tipo de contenido
    st.subheader("📚 Tipo de Contenido")
    
    content_category = st.radio(
        "Categoría:",
        ["FICCIÓN", "NO FICCIÓN"],
        horizontal=True
    )
    
    if content_category == "FICCIÓN":
        content_type = st.selectbox(
            "Selecciona tipo:",
            ["Cuento ficticio", "Fábula con moraleja", "Metáfora de PNL"]
        )
    else:
        content_type = st.selectbox(
            "Selecciona tipo:",
            ["Historia verídica", "Relato histórico", "Biografía/Testimonio", "Leyenda/Mito cultural"]
        )
    
    st.divider()
    
    # Campos dinámicos según tipo
    dynamic_fields = {}
    
    if content_type == "Cuento ficticio":
        dynamic_fields['theme'] = st.text_input("🎨 Tema del cuento", placeholder="Ej: La importancia de la amistad")
        dynamic_fields['characters'] = st.selectbox("🦊 Personajes", ["Animales", "Humanos", "Seres fantásticos", "Mixto"])
    
    elif content_type == "Fábula con moraleja":
        dynamic_fields['moral'] = st.text_input("🎯 Moraleja/Enseñanza", placeholder="Ej: La perseverancia supera los obstáculos")
        dynamic_fields['animals'] = st.text_input("🦊 Animales protagonistas", placeholder="Ej: Tortuga y liebre")
    
    elif content_type == "Metáfora de PNL":
        dynamic_fields['therapeutic'] = st.text_input("🧠 Objetivo terapéutico", placeholder="Ej: Superar el miedo al cambio")
        st.write("🔮 Patrones PNL a incluir:")
        dynamic_fields['pnl_patterns'] = st.multiselect(
            "Patrones:",
            ["Metáfora isomórfica", "Lenguaje hipnótico (Milton Model)", "Sugestiones indirectas", "Anclajes narrativos"]
        )
    
    elif content_type == "Historia verídica":
        dynamic_fields['category'] = st.selectbox(
            "🏛️ Categoría histórica",
            ["", "Imperio Incaico", "Civilizaciones precolombinas", "Historia indígena", 
             "Personajes reales", "Eventos históricos", "Movimientos sociales",
             "Cosmovisión andina", "Prácticas ancestrales", "Sabiduría indígena"]
        )
        dynamic_fields['topic'] = st.text_input("📜 Tema específico", placeholder="Ej: El sistema del Ayllu, La Mit'a")
        st.write("✅ Elementos a incluir:")
        dynamic_fields['elements'] = st.multiselect(
            "Elementos:",
            ["Contexto histórico", "Organización social", "Valores comunitarios", "Lección para hoy"],
            default=["Contexto histórico", "Lección para hoy"]
        )
    
    elif content_type == "Relato histórico":
        dynamic_fields['civilization'] = st.text_input("🌍 Civilización/Época", placeholder="Ej: Imperio Romano, Edad Media")
        dynamic_fields['event'] = st.text_input("📅 Evento/Período", placeholder="Ej: La caída de Constantinopla")
    
    elif content_type == "Biografía/Testimonio":
        col_bio1, col_bio2 = st.columns([4, 1])
        with col_bio1:
            dynamic_fields['person'] = st.text_input("👤 Personaje", placeholder="Ej: Henry Ford, Marie Curie")
        with col_bio2:
            if st.button("🔍", help="Buscar información"):
                if dynamic_fields.get('person') and api_key:
                    with st.spinner("Buscando..."):
                        # Aquí iría la búsqueda con Groq
                        st.info(f"Buscando información sobre {dynamic_fields['person']}...")
        
        dynamic_fields['bio_focus'] = st.selectbox(
            "🎯 Enfoque biográfico",
            ["Vida completa", "Momento/logro específico", "Filosofía/pensamiento", "Desafíos superados"]
        )
        dynamic_fields['aspect'] = st.text_input("💡 Aspecto a destacar", placeholder="Ej: Modelo T y producción en línea")
        st.write("📚 Lecciones a destacar:")
        dynamic_fields['lessons'] = st.multiselect(
            "Lecciones:",
            ["Innovación", "Perseverancia", "Liderazgo", "Visión de futuro", "Resiliencia", "Creatividad"]
        )
    
    elif content_type == "Leyenda/Mito cultural":
        dynamic_fields['culture'] = st.text_input("🌟 Cultura de origen", placeholder="Ej: Andina, Griega, Nórdica")
        dynamic_fields['myth_name'] = st.text_input("📖 Leyenda/Mito", placeholder="Ej: La Pachamama, El origen del maíz")
    
    st.divider()
    
    # Estados emocionales
    st.subheader("💫 Estados Emocionales")
    emotions = st.multiselect(
        "Selecciona tono(s):",
        ["Inspirador", "Reflexivo", "Motivador", "Sanador", "Transformador", "Educativo"]
    )
    
    # Público objetivo
    st.subheader("👥 Público Objetivo")
    audience = st.radio(
        "Dirigido a:",
        ["Niños", "Jóvenes", "Adultos"],
        horizontal=True,
        index=1
    )
    
    st.divider()
    
    # Prompt generado
    st.subheader("📝 Prompt Generado")
    
    def build_prompt(content_type, emotions, audience, fields):
        emotion_text = ", ".join(emotions) if emotions else "neutral"
        prompt = ""
        
        if content_type == "Cuento ficticio":
            theme = fields.get('theme', '[tema]')
            characters = fields.get('characters', 'personajes')
            prompt = f"Narra un cuento ficticio sobre {theme} con {characters} como protagonistas. El tono debe ser {emotion_text}. Texto de 7-8 páginas para {audience}. Incluye una narrativa envolvente con inicio, desarrollo y conclusión clara."
        
        elif content_type == "Fábula con moraleja":
            moral = fields.get('moral', '[moraleja]')
            animals = fields.get('animals', 'animales')
            prompt = f"Escribe una fábula protagonizada por {animals}. La moraleja debe ser: '{moral}'. Tono {emotion_text}. 7-8 páginas para {audience}. Finaliza con la moraleja explícita y clara."
        
        elif content_type == "Metáfora de PNL":
            therapeutic = fields.get('therapeutic', '[objetivo terapéutico]')
            patterns = fields.get('pnl_patterns', [])
            patterns_text = f". Incluye: {', '.join(patterns)}" if patterns else ""
            prompt = f"Crea una metáfora terapéutica de PNL para {therapeutic}. Tono {emotion_text}{patterns_text}. Historia de 7-8 páginas para {audience} con lenguaje indirecto y sugestiones transformadoras."
        
        elif content_type == "Historia verídica":
            category = fields.get('category', '')
            topic = fields.get('topic', '[tema]')
            elements = fields.get('elements', [])
            elements_text = f". Incluye: {', '.join(elements)}" if elements else ""
            prompt = f"Narra la historia verídica sobre {topic}{' (categoría: ' + category + ')' if category else ''}. Tono {emotion_text}{elements_text}. Texto de 7-8 páginas para {audience} con datos históricos precisos."
        
        elif content_type == "Relato histórico":
            civilization = fields.get('civilization', '[civilización]')
            event = fields.get('event', '[evento]')
            prompt = f"Relata la historia de {event} en {civilization}. Tono {emotion_text}. 7-8 páginas para {audience}. Incluye contexto histórico, personajes clave y consecuencias."
        
        elif content_type == "Biografía/Testimonio":
            person = fields.get('person', '[personaje]')
            focus = fields.get('bio_focus', 'Vida completa')
            aspect = fields.get('aspect', '')
            lessons = fields.get('lessons', [])
            lessons_text = f" Destaca lecciones sobre: {', '.join(lessons)}." if lessons else ""
            focus_map = {
                'Vida completa': 'su vida completa',
                'Momento/logro específico': aspect or 'sus logros principales',
                'Filosofía/pensamiento': 'su filosofía y pensamiento',
                'Desafíos superados': 'los desafíos que superó'
            }
            prompt = f"Narra la biografía de {person}, enfocándote en {focus_map[focus]}. Tono {emotion_text}.{lessons_text} 7-8 páginas para {audience}. Finaliza con el legado y aplicaciones actuales."
        
        elif content_type == "Leyenda/Mito cultural":
            culture = fields.get('culture', '[cultura]')
            myth_name = fields.get('myth_name', '[leyenda/mito]')
            prompt = f"Cuenta la leyenda/mito de {myth_name} de la cultura {culture}. Tono {emotion_text}. 7-8 páginas para {audience}. Mantén el espíritu original pero hazlo accesible y significativo."
        
        return prompt
    
    generated_prompt = build_prompt(content_type, emotions, audience, dynamic_fields)
    
    st.markdown(f"""
        <div class='prompt-box'>
            {generated_prompt}
        </div>
    """, unsafe_allow_html=True)
    
    # Botón generar
    if st.button("🎯 GENERAR HISTORIA", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ Por favor ingresa tu API key de Groq")
        else:
            with st.spinner("⏳ Groq está creando tu historia..."):
                try:
                    import requests
                    
                    response = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {api_key}"
                        },
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "messages": [{
                                "role": "system",
                                "content": "Escribe siempre en prosa narrativa fluida, en párrafos. NUNCA uses formato markdown: nada de asteriscos, negritas, viñetas, listas con guiones, numeraciones ni encabezados con #. Todo debe ser texto corrido natural, como un libro impreso."
                            }, {
                                "role": "user",
                                "content": generated_prompt
                            }],
                            "max_tokens": 8000,
                            "temperature": 0.8
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.generated_story = data['choices'][0]['message']['content']
                        st.session_state.audio_generated = False
                        st.success("✅ ¡Historia generada exitosamente!")
                        st.rerun()
                    else:
                        error_data = response.json()
                        st.error(f"❌ Error: {error_data.get('error', {}).get('message', 'Error desconocido')}")
                
                except Exception as e:
                    st.error(f"❌ Error al generar: {str(e)}")

# RIGHT COLUMN - Generated Story
with col2:
    st.header("📖 Historia Generada")
    
    if st.session_state.generated_story:
        # Mostrar historia
        st.markdown(f"""
            <div style='background: white; padding: 1.5rem; border-radius: 0.5rem; 
                        border: 1px solid #e0e0e0; max-height: 500px; overflow-y: auto; color: #000000;'>
                <div style='white-space: pre-wrap; line-height: 1.6; color: #000000;'>
{st.session_state.generated_story}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Opciones de audio
        st.subheader("🎙️ Opciones de Audio")
        
        col_audio1, col_audio2 = st.columns(2)
        
        with col_audio1:
            voice_gender = st.selectbox(
                "🔊 Voz",
                ["Femenina", "Masculina"]
            )
        
        with col_audio2:
            speed = st.slider(
                "⚡ Velocidad",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1
            )
        
        # Seleccionar voz específica de Edge TTS
        voice_map = {
            "Femenina": "es-ES-ElviraNeural",  # Voz femenina española
            "Masculina": "es-ES-AlvaroNeural"   # Voz masculina española
        }
        
        selected_voice = voice_map[voice_gender]
        
        # Botones de acción
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            # Copiar texto
            if st.button("📋 Copiar", use_container_width=True):
                st.code(st.session_state.generated_story, language=None)
                st.success("✅ Texto listo para copiar")
        
        with col_btn2:
            # Descargar TXT
            st.download_button(
                label="💾 TXT",
                data=st.session_state.generated_story,
                file_name=f"historia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_btn3:
            # Generar audio
            async def generate_audio(text, voice, rate):
                """Genera audio con Edge TTS"""
                output_file = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                
                # Ajustar rate según velocidad
                rate_str = f"{int((rate - 1.0) * 100):+d}%"
                
                communicate = edge_tts.Communicate(text, voice, rate=rate_str)
                await communicate.save(output_file)
                
                return output_file
            
            if st.button("🔊 Generar Audio", use_container_width=True, type="primary"):
                with st.spinner("🎙️ Generando audio con Edge TTS..."):
                    try:
                        # Ejecutar función async
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        # Limpiar texto de formato markdown antes de generar audio
                        clean_story = clean_text_for_audio(st.session_state.generated_story)
                        audio_file = loop.run_until_complete(
                            generate_audio(clean_story, selected_voice, speed)
                        )
                        loop.close()
                        
                        st.session_state.audio_generated = True
                        st.session_state.audio_file = audio_file
                        
                        st.success("✅ ¡Audio generado!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error al generar audio: {str(e)}")
        
        # Mostrar audio si fue generado
        if st.session_state.audio_generated and hasattr(st.session_state, 'audio_file'):
            st.divider()
            st.subheader("🎧 Reproducir Audio")
            
            if os.path.exists(st.session_state.audio_file):
                with open(st.session_state.audio_file, 'rb') as audio:
                    audio_bytes = audio.read()
                    st.audio(audio_bytes, format='audio/mp3')
                
                # Botón de descarga de audio
                st.download_button(
                    label="💾 Descargar MP3",
                    data=audio_bytes,
                    file_name=os.path.basename(st.session_state.audio_file),
                    mime="audio/mp3",
                    use_container_width=True
                )
                
                # Info del archivo
                file_size = os.path.getsize(st.session_state.audio_file) / (1024 * 1024)
                st.info(f"📊 Tamaño del audio: {file_size:.2f} MB")
    
    else:
        # Placeholder cuando no hay historia
        st.markdown("""
            <div style='text-align: center; padding: 4rem; color: #999;'>
                <svg style='width: 100px; height: 100px; margin: 0 auto;' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                    <path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' 
                          d='M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253'>
                    </path>
                </svg>
                <p style='margin-top: 1rem; font-size: 1.2rem;'>
                    Presiona "Generar Historia" para crear tu contenido
                </p>
            </div>
        """, unsafe_allow_html=True)

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>🎙️ <strong>StoryForge Audio Builder</strong> - Powered by Groq + Edge TTS</p>
        <p style='font-size: 0.9rem;'>
            Groq API (ultra-rápido) + Microsoft Edge TTS (gratis ilimitado) = Audiolibros profesionales
        </p>
    </div>
""", unsafe_allow_html=True)
