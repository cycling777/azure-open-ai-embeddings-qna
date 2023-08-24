import streamlit as st
import os
import traceback
from utilities.helper import LLMHelper
import streamlit.components.v1 as components
from urllib import parse

def delete_embeddings_of_file(file_to_delete):
    # RediSearchをクエリしてすべての埋め込みを取得 - 遅延ロード
    if 'data_files_embeddings' not in st.session_state:
        st.session_state['data_files_embeddings'] = llm_helper.get_all_documents(k=1000)

    if st.session_state['data_files_embeddings'].shape[0] == 0:
        return

    for converted_file_extension in ['.txt']:
        file_to_delete = 'converted/' + file_to_delete + converted_file_extension

        # 削除する埋め込みを取得
        embeddings_to_delete = st.session_state['data_files_embeddings'][st.session_state['data_files_embeddings']['filename'] == file_to_delete]['key'].tolist()
        embeddings_to_delete = list(map(lambda x: f"{x}", embeddings_to_delete))
        if len(embeddings_to_delete) > 0:
            llm_helper.vector_store.delete_keys(embeddings_to_delete)
            # セッションステートから削除
            st.session_state['data_files_embeddings'] = st.session_state['data_files_embeddings'].drop(st.session_state['data_files_embeddings'][st.session_state['data_files_embeddings']['filename'] == file_to_delete].index)

def delete_file_and_embeddings(filename=''):
    # RediSearchをクエリしてすべての埋め込みを取得 - 遅延ロード
    if 'data_files_embeddings' not in st.session_state:
        st.session_state['data_files_embeddings'] = llm_helper.get_all_documents(k=1000)

    if filename == '':
        filename = st.session_state['file_and_embeddings_to_drop']
    
    file_dict = next((d for d in st.session_state['data_files'] if d['filename'] == filename), None)

    if len(file_dict) > 0:
        # 元のファイルを削除
        source_file = file_dict['filename']
        try:
            llm_helper.blob_client.delete_file(source_file)
        except Exception as e:
            st.error(f"ファイルの削除エラー: {source_file} - {e}")

        # 変換済みファイルを削除
        if file_dict['converted']:
            converted_file = 'converted/' + file_dict['filename'] + '.txt'
            try:
                llm_helper.blob_client.delete_file(converted_file)
            except Exception as e:
                st.error(f"ファイルの削除エラー: {converted_file} - {e}")

        # 埋め込みを削除
        if file_dict['embeddings_added']:
            delete_embeddings_of_file(parse.quote(filename))
    
    # ファイル名リストを更新
    st.session_state['data_files'] = [d for d in st.session_state['data_files'] if d['filename'] != '{filename}']


def delete_all_files_and_embeddings():
    files_list = st.session_state['data_files']
    for filename_dict in files_list:
        delete_file_and_embeddings(filename_dict['filename'])

try:
    st.set_page_config(layout="wide", menu_items={
        'ヘルプを得る': None,
        'バグを報告する': None,
        'アバウト': '''
         ## 埋め込みアプリ

        ドキュメントリーダーサンプルデモ。
        '''
    })

    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

    llm_helper = LLMHelper()

    st.session_state['data_files'] = llm_helper.blob_client.get_all_files()
    st.session_state['data_files_embeddings'] = llm_helper.get_all_documents(k=1000)

    if len(st.session_state['data_files']) == 0:
        st.warning("ファイルが見つかりません。'ドキュメントを追加'タブでドキュメントを追加してください。")

    else:
        st.dataframe(st.session_state['data_files'], use_container_width=True)

        st.text("")
        st.text("")
        st.text("")

        filenames_list = [d['filename'] for d in st.session_state['data_files']]
        st.selectbox("削除するファイル名を選択", filenames_list, key="file_and_embeddings_to_drop")
         
        st.text("")
        st.button("ファイルとその埋め込みを削除", on_click=delete_file_and_embeddings)
        st.text("")
        st.text("")

        if len(st.session_state['data_files']) > 1:
            st.button("すべてのファイルを削除（埋め込みも含む）", type="secondary", on_click=delete_all_files_and_embeddings, args=None, kwargs=None)

except Exception as e:
    st.error(traceback.format_exc())
