import streamlit as st
import traceback
from utilities.helper import LLMHelper

def clear_summary():
    st.session_state['summary'] = ""

def get_custom_prompt():
    customtext = st.session_state['customtext']
    customprompt = "{}".format(customtext)
    return customprompt

def customcompletion():
    response = llm_helper.get_completion(get_custom_prompt(), max_tokens=500)
    st.session_state['result'] = response.encode().decode()

try:
    st.set_page_config(layout="wide", menu_items={
        'ヘルプを得る': None,
        'バグを報告する': None,
        'アバウト': '''
         ## 埋め込みアプリ
         埋め込みテストアプリケーション。
        '''
    })

    st.markdown("## カスタムプロンプトを持ってくる")

    llm_helper = LLMHelper()

    st.session_state['customtext'] = st.text_area(label="プロンプト", value='（こちらにプロンプトのデフォルトテキストを入力）', height=400)
    st.button(label="あなた自身のプロンプトでテストする", on_click=customcompletion)

    result = ""
    if 'result' in st.session_state:
        result = st.session_state['result']
    st.text_area(label="OpenAIの結果", value=result, height=200)

except Exception as e:
    st.error(traceback.format_exc())
