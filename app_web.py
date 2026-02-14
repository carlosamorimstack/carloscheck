import streamlit as st
import os
import json
import urllib.parse
import requests
import base64
import io
from PIL import Image
import imagehash

# --- CONFIGURAÇÃO ---
IMGBB_API_KEY = "4442bc1aad6732d530eb03a31f258f3b"

def carregar_db():
    if 'historico' not in st.session_state:
        st.session_state.historico = {}
    return st.session_state.historico

def salvar_db(db):
    st.session_state.historico = db

def upload_para_nuvem(imagem_pil):
    try:
        buffered = io.BytesIO()
        imagem_pil.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue())
        
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBB_API_KEY,
            "image": img_str,
            "expiration": 600 
        }
        response = requests.post(url, payload)
        if response.status_code == 200:
            return response.json()['data']['url']
        return None
    except Exception:
        return None

# --- INTERFACE DO SITE ---
st.set_page_config(page_title="ID Checker Pro", page_icon="🕵️", layout="wide")
st.title("🕵️ FaceCheck - Investigação Avançada")

arquivo = st.file_uploader("Arraste a foto do alvo aqui", type=["jpg", "png", "jpeg"])

if arquivo:
    img = Image.open(arquivo)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
        
    col_img, col_info = st.columns([1, 2])
    
    with col_img:
        st.image(img, width=300, caption="Alvo Carregado")
    
    with col_info:
        hash_atual = imagehash.phash(img)
        db = carregar_db()
        hash_str = str(hash_atual)
        
        similar = None
        for h in db:
            if (imagehash.hex_to_hash(h) - hash_atual) <= 5:
                similar = h
                break

        if similar:
            st.warning(f"⚠️ ALVO REPETIDO! Visto {db[similar].get('contagem', 1)} vezes nesta sessão.")
            db[similar]['contagem'] = db[similar].get('contagem', 1) + 1
        else:
            st.success("✅ NOVO ALVO IDENTIFICADO! Criando rastro digital...")
            db[hash_str] = {"contagem": 1}
        salvar_db(db)

    st.divider()
    
    if st.button("🚀 EXECUTAR BUSCA MULTIMOTOR"):
        with st.spinner("Enviando para servidores e gerando links de busca..."):
            link_publico = upload_para_nuvem(img)
            
            if link_publico:
                foto_enc = urllib.parse.quote(link_publico)
                
                # LISTA EXPANDIDA DE BUSCADORES
                motores = {
                    "🇷🇺 Yandex (Melhor para Redes Sociais)": f"https://yandex.com/images/search?rpt=imageview&url={foto_enc}",
                    "🇺🇸 Google Lens": f"https://lens.google.com/uploadbyurl?url={foto_enc}",
                    "🕵️ PimEyes (Reconhecimento Facial)": f"https://pimeyes.com/en/query?url={foto_enc}",
                    "💻 Bing Visual Search": f"https://www.bing.com/images/searchbyimage?cbir=sbi&imgurl={foto_enc}",
                    "🔍 TinEye (Forense)": f"https://tineye.com/search?url={foto_enc}",
                    "🇨🇳 Baidu (Busca Asiática/Global)": f"https://image.baidu.com/n/pc_search?queryImageUrl={foto_enc}"
                }
                
                st.subheader("🎉 Resultados da Varredura")
                
                # Organizando em grades (2 colunas)
                m_cols = st.columns(2)
                for i, (nome, link) in enumerate(motores.items()):
                    with m_cols[i % 2]:
                        st.link_button(nome, link, use_container_width=True)
                
                st.info("💡 **Dica de Especialista**: Use o **Yandex** e o **PimEyes** para encontrar perfis de pessoas. Use o **Google** e o **Bing** para descobrir onde a foto foi tirada ou quem é a personalidade.")
            else:
                st.error("Falha na comunicação com a nuvem. Verifique o sinal da internet.")
