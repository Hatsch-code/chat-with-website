import os

import streamlit as st
from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import WebBaseLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts.chat import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate,
                                    SystemMessagePromptTemplate)
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.vectorstores.azuresearch import AzureSearch

# Load environment variables from .env file (Optional)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
vector_store_address: str = os.getenv("YOUR_AZURE_SEARCH_ENDPOINT")
vector_store_password: str = os.getenv("YOUR_AZURE_SEARCH_ADMIN_KEY")

system_template = """Use the following pieces of context to answer the users question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
"""

messages = [
    SystemMessagePromptTemplate.from_template(system_template),
    HumanMessagePromptTemplate.from_template("{question}"),
]
prompt = ChatPromptTemplate.from_messages(messages)
chain_type_kwargs = {"prompt": prompt}


def main():
    if "messages" not in st.session_state.keys():  # Initialize the chat message history
        st.session_state.messages = [
            {"role": "assistant", "content": "Ask me a question about Streamlit's open-source Python library!"}
        ]

    # Set the title and subtitle of the app
    st.title('🦜🔗 Chat With Website')
    st.subheader('Input your website URL, ask questions, and receive answers directly from the website.')

    url = st.text_input("Insert The website URL")

    prompt = st.text_input("Ask a question (query/prompt)")
    if st.button("Submit Query", type="primary"):
        ABS_PATH: str = os.path.dirname(os.path.abspath(__file__))
        DB_DIR: str = os.path.join(ABS_PATH, "db")

        # Load data from the specified URL
        loader = WebBaseLoader(url)
        data = loader.load()

        # Split the loaded data
        text_splitter = CharacterTextSplitter(separator='\n',
                                              chunk_size=500,
                                              chunk_overlap=40)

        docs = text_splitter.split_documents(data)

        # Create OpenAI embeddings
        openai_embeddings = OpenAIEmbeddings()

        index_name: str = "langchain-vector-demo"
        vector_store: AzureSearch = AzureSearch(
            azure_search_endpoint=vector_store_address,
            azure_search_key=vector_store_password,
            index_name=index_name,
            embedding_function=openai_embeddings.embed_query,
        )
        vector_store.add_documents(documents=docs)

        docs = vector_store.similarity_search(
            query="What does Senacor do?",
            k=3,
            search_type="similarity",
        )
        print(docs[0].page_content)

        # Create a retriever from the Chroma vector database
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        # Use a ChatOpenAI model
        llm = ChatOpenAI(model_name='gpt-3.5-turbo')

        # Create a RetrievalQA from the model and retriever
        qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

        # Run the prompt and return the response
        response = qa(prompt)
        st.write(response)


if __name__ == '__main__':
    main()