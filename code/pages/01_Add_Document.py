import streamlit as st
import os, json, re, io
from os import path
import requests
import mimetypes
import traceback
import chardet
from utilities.helper import LLMHelper
import uuid
from redis.exceptions import ResponseError 
from urllib import parse
    
def upload_text_and_embeddings():
    file_name = f"{uuid.uuid4()}.txt"
    source_url = llm_helper.blob_client.upload_file(st.session_state['doc_text'], file_name=file_name, content_type='text/plain; charset=utf-8')
    llm_helper.add_embeddings_lc(source_url) 
    st.success("埋め込みが正常に追加されました。")

def remote_convert_files_and_add_embeddings(process_all=False):
    url = os.getenv('CONVERT_ADD_EMBEDDINGS_URL')
    if process_all:
        url = f"{url}?process_all=true"
    try:
        response = requests.post(url)
        if response.status_code == 200:
            st.success(f"{response.text}\nこれは非同期プロセスであり、完了までに数分かかる場合があります。")
        else:
            st.error(f"エラー: {response.text}")
    except Exception as e:
        st.error(traceback.format_exc())


def delete_row():
    st.session_state['data_to_drop']
    redisembeddings.delete_document(st.session_state['data_to_drop'])

def add_urls():
    urls = st.session_state['urls'].split('\n')
    for url in urls:
        if url:
            llm_helper.add_embeddings_lc(url)
            st.success(f"{url} の埋め込みが正常に追加されました。")

def upload_file(bytes_data: bytes, file_name: str):
    # 新しいファイルをアップロード
    st.session_state['filename'] = file_name
    content_type = mimetypes.MimeTypes().guess_type(file_name)[0]
    charset = f"; charset={chardet.detect(bytes_data)['encoding']}" if content_type == 'text/plain' else ''
    st.session_state['file_url'] = llm_helper.blob_client.upload_file(bytes_data, st.session_state['filename'], content_type=content_type+charset)

try:
    # ページレイアウトを広画面に設定し、メニューアイテムを設定
    menu_items = {
	'Get help': None,
	'Report a bug': None,
	'About': '''
	 ## 埋め込みアプリ
	 埋め込みテストアプリケーション。
	'''
    }
    st.set_page_config(layout="wide", menu_items=menu_items)

    llm_helper = LLMHelper()

    with st.expander("ナレッジベースに単一のドキュメントを追加", expanded=True):
        st.write("重いまたは長いPDFの場合は、以下の「一括でドキュメントを追加」オプションを使用してください。")
        st.checkbox("ドキュメントを英語に翻訳する", key="translate")
        uploaded_file = st.file_uploader("ナレッジベースに追加するためにドキュメントをアップロード", type=['pdf','jpeg','jpg','png', 'txt'])
  
        if uploaded_file is not None:
            # ファイルをバイトとして読み込む
            bytes_data = uploaded_file.getvalue()

            if st.session_state.get('filename', '') != uploaded_file.name:
                upload_file(bytes_data, uploaded_file.name)
                converted_filename = ''
                if uploaded_file.name.endswith('.txt'):
                    # テキストを埋め込みに追加
                    llm_helper.add_embeddings_lc(st.session_state['file_url'])
                else:
                    # OCRをLayout APIで取得し、その後埋め込みを追加
                    converted_filename = llm_helper.convert_file_and_add_embeddings(st.session_state['file_url'], st.session_state['filename'], st.session_state['translate'])
                
                llm_helper.blob_client.upsert_blob_metadata(uploaded_file.name, {'converted': 'true', 'embeddings_added': 'true', 'converted_filename': parse.quote(converted_filename)})
                st.success(f"ファイル {uploaded_file.name} の埋め込みがナレッジベースに追加されました。")

    with st.expander("ナレッジベースにテキストを追加", expanded=False):
        col1, col2 = st.columns([3,1])
        with col1: 
            st.session_state['doc_text'] = st.text_area("新しいテキストコンテンツを追加してから 'Compute Embeddings' をクリックしてください", height=600)

        with col2:
            st.session_state['embeddings_model'] = st.selectbox('埋め込みモデル', [llm_helper.get_embeddings_model()['doc']], disabled=True)
            st.button("埋め込みを計算", on_click=upload_text_and_embeddings)


    with st.expander("バッチでドキュメントを追加", expanded=False):
        uploaded_files = st.file_uploader("Azure Storage Accountにドキュメントを追加してアップロードしてください", type=['pdf','jpeg','jpg','png', 'txt'], accept_multiple_files=True)
        if uploaded_files is not None:
            for up in uploaded_files:
                # ファイルをバイトとして読み込む
                bytes_data = up.getvalue()

                if st.session_state.get('filename', '') != up.name:
                    # 新しいファイルをアップロード
                    upload_file(bytes_data, up.name)
                    if up.name.endswith('.txt'):
                        # テキストを埋め込みに追加
                        llm_helper.blob_client.upsert_blob_metadata(up.name, {'converted': "true"})

        col1, col2, col3 = st.columns([2,2,2])
        with col1:
            st.button("新しいファイルを変換して埋め込みを追加", on_click=remote_convert_files_and_add_embeddings)
        with col3:
            st.button("すべてのファイルを変換して埋め込みを追加", on_click=remote_convert_files_and_add_embeddings, args=(True,))

    with st.expander("ナレッジベース内のドキュメントを表示", expanded=False):
        # RediSearchをクエリしてすべての埋め込みを取得
        try:
            data = llm_helper.get_all_documents(k=1000)
            if len(data) == 0:
                st.warning("埋め込みが見つかりません。テキスト入力にデータをコピペして'Compute Embeddings'をクリックするか、ドキュメントをドラッグアンドドロップしてください。")
            else:
                st.dataframe(data, use_container_width=True)
        except Exception as e:
            if isinstance(e, ResponseError):
                st.warning("埋め込みが見つかりません。テキスト入力にデータをコピペして'Compute Embeddings'をクリックするか、ドキュメントをドラッグアンドドロップしてください。")
            else:
                st.error(traceback.format_exc())


except Exception as e:
    st.error(traceback.format_exc())

