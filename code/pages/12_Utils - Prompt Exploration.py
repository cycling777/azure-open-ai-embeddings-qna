import streamlit as st
import os
import traceback
from utilities.helper import LLMHelper

def get_prompt():
    return f"{st.session_state['doc_text']}\n{st.session_state['input_prompt']}"

def customcompletion():
    response = llm_helper.get_completion(get_prompt())
    st.session_state['prompt_result'] = response.encode().decode()

def process_all(data):
    llm_helper.vector_store.delete_prompt_results('prompt*')
    data_to_process = data[data.filename.isin(st.session_state['selected_docs'])]
    for doc in data_to_process.to_dict('records'):
        prompt = f"{doc['content']}\n{st.session_state['input_prompt']}\n\n"
        response = llm_helper.get_completion(prompt)
        llm_helper.vector_store.add_prompt_result(doc['key'], response.encode().decode(), doc['filename'], st.session_state['input_prompt'])
    st.session_state['data_processed'] = llm_helper.vector_store.get_prompt_results().to_csv(index=False)

try:
    # 画面レイアウトとメニューアイテムの設定
    menu_items = {
        'ヘルプを得る': None,
        'バグを報告': None,
        'このアプリについて': '''
         ## 埋め込みアプリ
         埋め込みテストアプリケーション。
        '''
    }
    st.set_page_config(layout="wide", menu_items=menu_items)

    if not 'data_processed' in st.session_state:
        st.session_state['data_processed'] = None

    llm_helper = LLMHelper()

    # RediSearchからすべての埋め込みを取得
    data = llm_helper.get_all_documents(k=1000)

    if len(data) == 0:
        st.warning("埋め込みが見つかりません。'文書を追加'タブで文書を挿入してください。")
    else:
        st.dataframe(data, use_container_width=True)

        # カスタムプロンプト用のテキストエリアを表示
        st.text_area(label="文書", height=400, key="doc_text")
        st.text_area(label="プロンプト", height=100, key="input_prompt")
        st.button(label="タスクを実行", on_click=customcompletion)

        result = ""
        if 'prompt_result' in st.session_state:
            result = st.session_state['prompt_result']
            st.text_area(label="結果", value=result, height=400)

        cols = st.columns([1,1,1,2])
        with cols[1]:
            st.multiselect("文書を選択", sorted(set(data.filename.tolist())), key="selected_docs")
        with cols[2]:
            st.text("-")
            st.button("文書でタスクを実行", on_click=process_all, args=(data,)) 
        with cols[3]:
            st.text("-")
            download_data = st.session_state['data_processed'] if st.session_state['data_processed'] is not None else ""
            st.download_button(label="結果をダウンロード", data=download_data, file_name="results.csv", mime="text/csv", disabled=st.session_state['data_processed'] is None)

except Exception as e:
    st.error(traceback.format_exc())
