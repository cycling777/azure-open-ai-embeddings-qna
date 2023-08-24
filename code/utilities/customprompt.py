# flake8: noqa
from langchain.prompts import PromptTemplate

template = """{要約}

テキストに記載されている情報を優先して質問にお答えください。
もしテキスト内にその情報が見つからない場合、ChatGPTが持っている知識で回答することが可能です。その際は、「情報源からではないですが」と前置きしてから回答してください。
質問の言語を検出し、同じ言語で答えてください。
列挙が求められた場合は、それら全てを列挙し、何も創作しないでください。
各情報源には名前が続いています。その後に実際の情報が続きます。回答内で事実を使用する場合、常にその情報源の名前を含めてください。ファイル名のソースを参照する場合は常に二重角括弧を使用してください。例：[[info1.pdf.txt]]。ソースを組み合わせないで、各ソースを個別にリストしてください。例：[[info1.pdf]][[info2.txt]]。
質問に答えた後、ユーザーが次におそらく尋ねるであろう3つの非常に短いフォローアップの質問を生成してください。
質問を参照する場合は、二重角括弧のみを使用してください。例：<<処方箋には除外事項がありますか?>>。
質問のみを生成し、質問の前後にテキストを生成しないでください。たとえば「フォローアップの質問:」など。
すでに尋ねられた質問を繰り返さないようにしてください。

質問：{質問}
回答："""


PROMPT = PromptTemplate(template=template, input_variables=["summaries", "question"])

EXAMPLE_PROMPT = PromptTemplate(
    template="Content: {page_content}\nSource: {source}",
    input_variables=["page_content", "source"],
)


