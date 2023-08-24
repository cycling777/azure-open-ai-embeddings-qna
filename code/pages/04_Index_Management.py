import streamlit as st
import os
import traceback
from utilities.helper import LLMHelper

def delete_embedding():
    llm_helper.vector_store.delete_keys([f"{st.session_state['embedding_to_drop']}"])
    if 'data_embeddings' in st.session_state:
        del st.session_state['data_embeddings']

def delete_file_embeddings():
    if st.session_state['data_embeddings'].shape[0] != 0:
        file_to_delete = st.session_state['file_to_drop']
        embeddings_to_delete = st.session_state['data_embeddings'][st.session_state['data_embeddings']['filename'] == file_to_delete]['key'].tolist()
        embeddings_to_delete = list(map(lambda x: f"{x}", embeddings_to_delete))
        if len(embeddings_to_delete) > 0:
            llm_helper.vector_store.delete_keys(embeddings_to_delete)
            st.session_state['data_embeddings'] = st.session_state['data_embeddings'].drop(st.session_state['data_embeddings'][st.session_state['data_embeddings']['filename'] == file_to_delete].index)

def delete_all():
    embeddings_to_delete = st.session_state['data_embeddings'].key.tolist()
    embeddings_to_delete = list(map(lambda x: f"{x}", embeddings_to_delete))
    llm_helper.vector_store.delete_keys(embeddings_to_delete)

try:
    st.set_page_config(layout="wide", menu_items={
        'ヘルプを得る': None,
        'バグを報告する': None,
        'アバウト': '''
         ## 埋め込みアプリ
         埋め込みテストアプリケーション。
        '''
    })

    llm_helper = LLMHelper()

    st.session_state['data_embeddings'] = llm_helper.get_all_documents(k=1000)

    nb_embeddings = len(st.session_state['data_embeddings'])

    if nb_embeddings == 0:
        st.warning("埋め込みが見つかりません。「ドキュメントを追加」タブでドキュメントを追加してください。")
    else:
        st.dataframe(st.session_state['data_embeddings'], use_container_width=True)
        st.text("")
        st.text("")
        st.download_button("データをダウンロード", st.session_state['data_embeddings'].to_csv(index=False).encode('utf-8'), "embeddings.csv", "text/csv", key='download-embeddings')

        st.text("")
        st.text("")
        col1, col2, col3 = st.columns([3,1,3])
        with col1:
            st.selectbox("削除する埋め込みID", st.session_state['data_embeddings'].get('key',[]), key="embedding_to_drop")
            st.text("")
            st.button("埋め込みを削除", on_click=delete_embedding)
        with col2:
            st.text("")
        with col3:
            st.selectbox("埋め込みを削除するファイル名", set(st.session_state['data_embeddings'].get('filename',[])), key="file_to_drop")
            st.text("")
            st.button("ファイルの埋め込みを削除", on_click=delete_file_embeddings)

        st.text("")
        st.text("")
        st.button("すべての埋め込みを削除", type="secondary", on_click=delete_all)

except Exception as e:
    st.error(traceback.format_exc())
