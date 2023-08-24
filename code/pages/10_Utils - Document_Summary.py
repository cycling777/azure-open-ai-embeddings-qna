import streamlit as st
from utilities.helper import LLMHelper
import os
import traceback

def summarize():
    response = llm_helper.get_completion(get_prompt())
    st.session_state['summary'] = response

def clear_summary():
    st.session_state['summary'] = ""

def get_prompt():
    text = st.session_state['text']
    if text is None or text == '':
        text = '{}'
    if summary_type == "基本的な要約":
        prompt = "次のテキストを要約してください:\n\n{}\n\n要約:".format(text)
    elif summary_type == "箇条書きの要約":
        prompt = "次のテキストを箇条書きの要約にしてください:\n\n{}\n\n要約:".format(text)
    elif summary_type == "小学2年生に説明":
        prompt = "次のテキストを小学2年生に説明してください:\n\n{}\n\n要約:".format(text)

    return prompt

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

    st.markdown("## 要約")
    summary_type = st.radio(
        "要約のタイプを選択",
        ["基本的な要約", "箇条書きの要約", "小学2年生に説明"],
        key="visibility"
    )
    st.session_state['text'] = st.text_area(label="要約するテキストを入力してください", value='（こちらにテキストを入力）', height=200)
    st.button(label="要約する", on_click=summarize)

    summary = ""
    if 'summary' in st.session_state:
        summary = st.session_state['summary']

    st.text_area(label="要約結果", value=summary, height=200)
    st.button(label="要約をクリア", on_click=clear_summary)

    st.text_area(label="プロンプト", value=get_prompt(), height=400)
    st.button(label="更新したプロンプトで要約する")

except Exception as e:
    st.error(traceback.format_exc())
