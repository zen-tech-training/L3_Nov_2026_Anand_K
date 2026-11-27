from langchain_ollama import ChatOllama
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

prompt1 = PromptTemplate(
    template='Generate a detailed report on {topic}',
    input_variables=['topic']
)

prompt2 = PromptTemplate(
    template='Generate a 5 pointer summary from the following text \n {text}',
    input_variables=['text']
)

model = ChatOllama(model="llama3.2")

parser = StrOutputParser()

chain = prompt1 | model | parser | prompt2 | model | parser

config = {
    "run_name": "sequential_chains",
    "tags": ["llm app", "summarization"],
    "metadata": {"model1": "llama3.2", "model1_temp": 0.7}
}
result = chain.invoke({'topic': 'Generative AI'}, config=config)

print(result)
