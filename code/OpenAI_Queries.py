from dotenv import load_dotenv
load_dotenv()

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import traceback
from utilities.helper import LLMHelper
import regex as re

import logging
logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)

# 部署が正しく動作しているかチェックする関数
def check_deployment():
    try:
        llm_helper = LLMHelper()
        llm_helper.get_completion("ジョークを作成してください！")
        st.success("LLMは正常に動作しています！")
    except Exception as e:
        st.error(f"""LLMが動作していません。
            Azure OpenAIリソースの{llm_helper.api_base}にデプロイメント名{llm_helper.deployment_name}が存在することを確認してください。
            環境変数OPENAI_DEPLOYMENT_TYPEが正しいかどうかも確認してください。
            アプリケーションを再起動してください。
            """)
        st.error(traceback.format_exc())
    #\ 2. Check if the embedding is working
    try:
        llm_helper = LLMHelper()
        llm_helper.embeddings.embed_documents(texts=["これはテストです"])
        st.success("埋め込みモデルは正常に動作しています！")
    except Exception as e:
        st.error(f"""埋め込みモデルが動作していません。
            Azure OpenAIリソースの{llm_helper.api_base}にデプロイメント名"text-embedding-ada-002"が存在するか確認してください。
            その後、アプリケーションを再起動してください。
            """)
        st.error(traceback.format_exc())

    #\ 3. Check if the translation is working
    try:
        llm_helper = LLMHelper()
        llm_helper.translator.translate("これはテストです", "it")
        st.success("翻訳が正常に動作しています！")
    except Exception as e:
        st.error(f"""翻訳モデルが動作していません。
            アプリ設定でAzure Translatorのキーが正しく設定されているか確認してください。
            その後、アプリケーションを再起動してください。
            """)
        st.error(traceback.format_exc())
    #\ 4. Check if the Redis is working with previous version of data
    try:
        llm_helper = LLMHelper()
        if llm_helper.vector_store_type != "AzureSearch":
            if llm_helper.vector_store.check_existing_index("embeddings-index"):
                st.warning("""Redisが旧バージョンのデータ構造を使用しているようです。
                            新しいデータ構造を使用したい場合は、アプリを起動し、「ドキュメントを追加」->「一括でドキュメントを追加」に進み、「すべてのファイルを変換して埋め込みを追加」をクリックしてドキュメントを再処理してください。
                            この警告を消すには、Redisから「embeddings-index」というインデックスを削除してください。
                            旧バージョンのデータ構造を使用する場合は、Webアプリのコンテナイメージをfruocco/oai-embeddings:2023-03-27_25に変更してください。
                            """)
            else:
                st.success("Redisは正常に動作しています！")
        else:
            try:
                llm_helper.vector_store.index_exists()
                st.success("Azure Cognitive Searchが正常に動作しています！")
            except Exception as e:
                st.error("""Azure Cognitive Searchが動作していません。
                            アプリ設定でAzure Cognitive Searchのサービス名とサービスキーが正しく設定されているか確認してください。
                            その後、アプリケーションを再起動してください。
                            """)
                st.error(traceback.format_exc())
    except Exception as e:
        st.error(f"""Redisが動作していません。
                    アプリ設定でRedisの接続文字列が正しく設定されているか確認してください。
                    その後、アプリケーションを再起動してください。
                    """)
        st.error(traceback.format_exc())


def check_variables_in_prompt():
    # "summaries" が custom_prompt 文字列に含まれているか確認
    if "{summaries}" not in st.session_state.custom_prompt:
        st.warning("""あなたのカスタムプロンプトには変数 "{summaries}" が含まれていません。
        この変数は、VectorStoreから取得した文書の内容をプロンプトに追加するために使用されます。
        アプリを使用するには、カスタムプロンプトにこれを追加してください。
        デフォルトのプロンプトに戻します。
        """)
        st.session_state.custom_prompt = ""
    if "{question}" not in st.session_state.custom_prompt:
        st.warning("""あなたのカスタムプロンプトには変数 "{question}" が含まれていません。
        この変数は、ユーザーの質問をプロンプトに追加するために使用されます。
        アプリを使用するには、カスタムプロンプトにこれを追加してください。
        デフォルトのプロンプトに戻します。
        """)
        st.session_state.custom_prompt = ""

    

 # Callback to assign the follow-up question is selected by the user
def ask_followup_question(followup_question):
    st.session_state.askedquestion = followup_question
    st.session_state['input_message_key'] = st.session_state['input_message_key'] + 1

def questionAsked():
    st.session_state.askedquestion = st.session_state["input"+str(st.session_state ['input_message_key'])]

@st.cache_data()
def get_languages():
    return llm_helper.translator.get_available_languages()

try:

    default_prompt = "" 
    default_question = "" 
    default_answer = ""

    if 'question' not in st.session_state:
        st.session_state['question'] = default_question
    if 'response' not in st.session_state:
        st.session_state['response'] = default_answer
    if 'context' not in st.session_state:
        st.session_state['context'] = ""
    if 'custom_prompt' not in st.session_state:
        st.session_state['custom_prompt'] = ""
    if 'custom_temperature' not in st.session_state:
        st.session_state['custom_temperature'] = float(os.getenv("OPENAI_TEMPERATURE", 0.7))

    if 'sources' not in st.session_state:
        st.session_state['sources'] = ""
    if 'followup_questions' not in st.session_state:
        st.session_state['followup_questions'] = []
    if 'input_message_key' not in st.session_state:
        st.session_state ['input_message_key'] = 1
    if 'askedquestion' not in st.session_state:
        st.session_state.askedquestion = default_question

    # ページレイアウトをワイドスクリーンに設定し、メニューアイテムを追加
    menu_items = {
        'ヘルプを得る': None,
        'バグを報告': None,
        'このアプリについて': '''
        ## エンベディングアプリ
        エンベディングテストアプリケーション。
        '''
    }
    st.set_page_config(layout="wide", menu_items=menu_items)

    llm_helper = LLMHelper(custom_prompt=st.session_state.custom_prompt, temperature=st.session_state.custom_temperature)

    # 翻訳のための利用可能な言語を取得
    available_languages = get_languages()

    # カスタムプロンプト変数
    custom_prompt_placeholder = """{summaries}
    上記のテキストのみを使用して、質問に回答してください。
    質問：{question}
    回答："""
    custom_prompt_help = """{summaries}と{question}という変数をプロンプトに追加することで、カスタムプロンプトを設定できます。
    {summaries}は、VectorStoreから取得した文書の内容に置き換えられます。
    {question}は、ユーザーの質問に置き換えられます。
    """

    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        st.image(os.path.join('images','microsoft.png'))

    col1, col2, col3 = st.columns([2,2,2])
    with col1:
        st.button("デプロイメントを確認", on_click=check_deployment)
    with col3:
        with st.expander("設定"):
            st.slider("temperature", min_value=0.0, max_value=1.0, step=0.1, key='custom_temperature')
            st.text_area("カスタムプロンプト", key='custom_prompt', on_change=check_variables_in_prompt, placeholder=custom_prompt_placeholder, help=custom_prompt_help, height=150)
            st.selectbox("言語", [None] + list(available_languages.keys()), key='translation_language')

    question = st.text_input("Azure OpenAI Semantic Answer", value=st.session_state['askedquestion'], key="input"+str(st.session_state['input_message_key']), on_change=questionAsked)

    # Answer the question if any
    if st.session_state.askedquestion != '':
        st.session_state['question'] = st.session_state.askedquestion
        st.session_state.askedquestion = ""
        st.session_state['question'], \
        st.session_state['response'], \
        st.session_state['context'], \
        st.session_state['sources'] = llm_helper.get_semantic_answer_lang_chain(st.session_state['question'], [])
        st.session_state['response'], followup_questions_list = llm_helper.extract_followupquestions(st.session_state['response'])
        st.session_state['followup_questions'] = followup_questions_list

    sourceList = []

    # Display the sources and context - even if the page is reloaded
    if st.session_state['sources'] or st.session_state['context']:
        st.session_state['response'], sourceList, matchedSourcesList, linkList, filenameList = llm_helper.get_links_filenames(st.session_state['response'], st.session_state['sources'])
        st.write("<br>", unsafe_allow_html=True)
        st.markdown("Answer: " + st.session_state['response'])
 
    # Display proposed follow-up questions which can be clicked on to ask that question automatically
    if len(st.session_state['followup_questions']) > 0:
        st.write("<br>", unsafe_allow_html=True)
        st.markdown('**Proposed follow-up questions:**')
    with st.container():
        for questionId, followup_question in enumerate(st.session_state['followup_questions']):
            if followup_question:
                str_followup_question = re.sub(r"(^|[^\\\\])'", r"\1\\'", followup_question)
                st.button(str_followup_question, key=1000+questionId, on_click=ask_followup_question, args=(followup_question, ))

    if st.session_state['sources'] or st.session_state['context']:
        # Buttons to display the context used to answer
        st.write("<br>", unsafe_allow_html=True)
        st.markdown('**Document sources:**')
        for id in range(len(sourceList)):
            st.markdown(f"[{id+1}] {sourceList[id]}")

        # Details on the question and answer context
        st.write("<br><br>", unsafe_allow_html=True)
        with st.expander("Question and Answer Context"):
            if not st.session_state['context'] is None and st.session_state['context'] != []:
                for content_source in st.session_state['context'].keys():
                    st.markdown(f"#### {content_source}")
                    for context_text in st.session_state['context'][content_source]:
                        st.markdown(f"{context_text}")

            st.markdown(f"SOURCES: {st.session_state['sources']}") 

    for questionId, followup_question in enumerate(st.session_state['followup_questions']):
        if followup_question:
            str_followup_question = re.sub(r"(^|[^\\\\])'", r"\1\\'", followup_question)

    if st.session_state['translation_language'] and st.session_state['translation_language'] != '':
        st.write(f"Translation to other languages, 翻译成其他语言, النص باللغة العربية")
        st.write(f"{llm_helper.translator.translate(st.session_state['response'], available_languages[st.session_state['translation_language']])}")		
		
except Exception:
    st.error(traceback.format_exc())
