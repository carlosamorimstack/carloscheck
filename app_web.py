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
# Chave da API do ImgBB
IMGBB_API_KEY = "4442bc1aad6732d530eb03a31f258f3b"

def carregar_db():
    # Isso armazena os dados na memória da sessão do navegador para evitar erro de permissão no servidor
    if 'historico' not in st.session_state:
        st.session_state.historico = {}
    return st.session_state.historico

def salvar_db(db):
    # Salva na memória temporária da sessão
    st.session_state.historico = db

def upload_para_nuvem(imagem_pil):
    """Envia a foto para o ImgBB para gerar um link que os buscadores consigam ler."""
    try:
        buffered = io.BytesIO()
        imagem_pil.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue())
        
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBB_API_KEY,
            "image": img_str,
            "expiration": 600 # O link apaga-se em 10 minutos por segurança
        }
        response = requests.post(url, payload)
        if response.status_code == 200:
            return response.json()['data']['url']
        return None
    except Exception as e:
        return None

# --- INTERFACE DO SITE ---
st.set_page_config(page_title="ID Checker Profissional", page_icon="🕵️")
st.title("🕵️ FaceCheck do Eduardo")
st.subheader("Investigação Multimotor")

arquivo = st.file_uploader("Arraste a foto aqui para encontrar o perfil", type=["jpg", "png", "jpeg"])

if arquivo:
    img = Image.open(arquivo)
    # Converter para RGB para evitar erro com arquivos PNG/RGBA no upload
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
        
    st.image(img, width=300, caption="Imagem carregada")
    
    # Lógica de Duplicata (Histórico na Sessão)
    hash_atual = imagehash.phash(img)
    db = carregar_db()
    hash_str = str(hash_atual)
    
    similar = None
    for h in db:
        if (imagehash.hex_to_hash(h) - hash_atual) <= 5:
            similar = h
            break

    if similar:
        st.warning(f"⚠️ FOTO REPETIDA! Já vista {db[similar].get('contagem', 1)} vezes nesta sessão.")
        db[similar]['contagem'] = db[similar].get('contagem', 1) + 1
    else:
        st.success("✅ FOTO NOVA! Registrada no histórico temporário.")
        db[hash_str] = {"contagem": 1}
    
    salvar_db(db)

    # SEÇÃO DE BUSCA AVANÇADA
    st.divider()
    if st.button("🚀 LOCALIZAR PERFIL EM TODOS OS MOTORES"):
        with st.spinner("Gerando rastro digital e enviando para nuvem..."):
            link_publico = upload_para_nuvem(img)
            
            if link_publico:
                foto_enc = urllib.parse.quote(link_publico)
                
                # Links de busca configurados
                yandex = f"https://yandex.com/images/search?rpt=imageview&url={foto_enc}"
                google = f"https://lens.google.com/uploadbyurl?url={foto_enc}"
                bing = f"https://www.bing.com/images/searchbyimage?cbir=sbi&imgurl={foto_enc}"
                
                st.subheader("🎉 Investigação Concluída!")
                st.write("Selecione um motor de busca para ver os resultados:")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.link_button("🇷🇺 Yandex", yandex)
                with col2:
                    st.link_button("🇺🇸 Google Lens", google)
                with col3:
                    st.link_button("💻 Bing", bing)
                
                st.info("💡 **Dica**: O Yandex é o melhor para redes sociais (Instagram/Facebook).")
            else:
                st.error("Erro ao gerar link na nuvem. Verifique sua conexão ou a chave da API.")
