from operator import itemgetter

from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableLambda
from langchain.schema.runnable.config import RunnableConfig
from langchain.memory import ConversationBufferMemory
from chainlit.input_widget import Select, Switch, Slider

from chainlit.types import ThreadDict
import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
import json
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text
import json
from sqlalchemy import create_engine, text
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.fernet import Fernet

engine = create_engine("sqlite:///chainlit_db.db")
NUM_BYTES_FOR_LEN = 4

async def export_all_chat_history():
    # 1. Retrieve chat history from the database.
    # Adjust this query as needed (you may join with threads or filter by user, etc.)
    # 0. Get the current user id (adjust this as needed)
    user_id = cl.user_session.get("user").id

    # 1. Run one query that joins threads and steps for the given user.
    query = text("""
    SELECT
      t.id AS thread_id,
      t.createdAt AS thread_createdAt,
      t.name AS thread_name,
      t.userId AS thread_userId,
      t.userIdentifier AS thread_userIdentifier,
      t.tags AS thread_tags,
      t.metadata AS thread_metadata,
      s.id AS step_id,
      s.name AS step_name,
      s.type AS step_type,
      s.threadId AS step_threadId,
      s.parentId AS step_parentId,
      s.command AS step_command,
      s.streaming AS step_streaming,
      s.waitForAnswer AS step_waitForAnswer,
      s.isError AS step_isError,
      s.metadata AS step_metadata,
      s.tags AS step_tags,
      s.input AS step_input,
      s.output AS step_output,
      s.createdAt AS step_createdAt,
      s.start AS step_start,
      s.end AS step_end,
      s.generation AS step_generation,
      s.showInput AS step_showInput,
      s.language AS step_language,
      s.indent AS step_indent
    FROM threads t
    LEFT JOIN steps s ON t.id = s.threadId
    WHERE t.userId = :uid
    ORDER BY t.createdAt, s.createdAt
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"uid": user_id})
        # Group rows by thread_id
        threads_by_id = {}
        for row in result:
            r = dict(row._mapping)
            thread_id = r["thread_id"]
            if thread_id not in threads_by_id:
                # Build the thread info from keys prefixed with "thread_"
                thread_info = {}
                for k, v in r.items():
                    if k.startswith("thread_"):
                        # Remove the prefix for clarity in the JSON output
                        thread_info[k[len("thread_"):]] = v
                thread_info["steps"] = []
                threads_by_id[thread_id] = thread_info

            # If there's a step (step_id is not None), then build a step dictionary
            if r.get("step_id") is not None:
                step_info = {}
                for k, v in r.items():
                    if k.startswith("step_"):
                        step_info[k[len("step_"):]] = v
                threads_by_id[thread_id]["steps"].append(step_info)

        # Build the final structure
        data = {
            "user_Id": user_id,
            "threads": list(threads_by_id.values())
        }

    # 2. Serialize the data into JSON bytes.
    serialized_history = json.dumps(data, indent=2).encode("utf-8")


    # 3. Load the RSA public key from a PEM file.
    # Ensure that this file (e.g. "public_key.pem") is available on the user device.
    with open("public_key.pem", "rb") as key_file:
        public_key = serialization.load_pem_public_key(key_file.read())

    # 4. Generate a symmetric key (Fernet key) and encrypt the serialized history.
    symmetric_key = Fernet.generate_key()
    fernet = Fernet(symmetric_key)
    encrypted_data = fernet.encrypt(serialized_history)

    # 5. Encrypt the symmetric key using the RSA public key with OAEP padding.
    encrypted_symmetric_key = public_key.encrypt(
        symmetric_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # 6. Combine the encrypted symmetric key and encrypted data.
    # First, encode the length of the encrypted symmetric key in NUM_BYTES_FOR_LEN bytes,
    # then append the encrypted symmetric key and the encrypted data.
    output_bytes = (
        len(encrypted_symmetric_key).to_bytes(NUM_BYTES_FOR_LEN, byteorder="big") +
        encrypted_symmetric_key +
        encrypted_data
    )

    # 7. Create and return a Chainlit File element for download.
    file_element = cl.File(
        name="chat_history.enc",
        content=output_bytes,
        display="inline",  # Use "download" if you prefer a download button
    )

    return file_element


def setup_runnable():
    memory = cl.user_session.get("memory")  # type: ConversationBufferMemory
    model = ChatOpenAI(
        openai_api_base="http://localhost:11434/v1",  # Adjust if your Ollama endpoint is different
         # Ollama doesn’t require an API key
        model_name="llama3.1:8b",  # Replace with the exact model name as configured in Ollama
        streaming=True,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful chatbot"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    runnable = (
        RunnablePassthrough.assign(
            history=RunnableLambda(memory.load_memory_variables) | itemgetter("history")
        )
        | prompt
        | model
        | StrOutputParser()
    )
    cl.user_session.set("runnable", runnable)


@cl.password_auth_callback
def auth():
    return cl.User(identifier="test")


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("memory", ConversationBufferMemory(return_messages=True))
        # Other initialization...
    commands = [
        {"id": "export_all_chat_history", "icon": "download", "description": "Export All Chat History"},
    ]
    await cl.context.emitter.set_commands(commands)
    settings = await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="OpenAI - Model",
                values=["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-32k"],
                initial_index=0,
            ),
            Switch(id="Streaming", label="OpenAI - Stream Tokens", initial=True),
            Slider(
                id="Temperature",
                label="OpenAI - Temperature",
                initial=1,
                min=0,
                max=2,
                step=0.1,
            ),
            Slider(
                id="SAI_Steps",
                label="Stability AI - Steps",
                initial=30,
                min=10,
                max=150,
                step=1,
                description="Amount of inference steps performed on image generation.",
            ),
            Slider(
                id="SAI_Cfg_Scale",
                label="Stability AI - Cfg_Scale",
                initial=7,
                min=1,
                max=35,
                step=0.1,
                description="Influences how strongly your generation is guided to match your prompt.",
            ),
            Slider(
                id="SAI_Width",
                label="Stability AI - Image Width",
                initial=512,
                min=256,
                max=2048,
                step=64,
                tooltip="Measured in pixels",
            ),
            Slider(
                id="SAI_Height",
                label="Stability AI - Image Height",
                initial=512,
                min=256,
                max=2048,
                step=64,
                tooltip="Measured in pixels",
            ),
        ]
    ).send()

    setup_runnable()


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Morning routine ideation",
            message="Can you help me create a personalized morning routine that would help increase my productivity throughout the day? Start by asking me about my current habits and what activities energize me in the morning.",
            icon="/public/idea.svg",
            ),

        cl.Starter(
            label="Explain superconductors",
            message="Explain superconductors like I'm five years old.",
            icon="/public/learn.svg",
            ),
        cl.Starter(
            label="Python script for daily email reports",
            message="Write a script to automate sending daily email reports in Python, and walk me through how I would set it up.",
            icon="/public/terminal.svg",
            ),
        cl.Starter(
            label="Text inviting friend to wedding",
            message="Write a text asking a friend to be my plus-one at a wedding next month. I want to keep it super short and casual, and offer an out.",
            icon="/public/write.svg",
            )
    ]

@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    memory = ConversationBufferMemory(return_messages=True)
    root_messages = [m for m in thread["steps"] if m["parentId"] == None]
    for message in root_messages:
        if message["type"] == "user_message":
            memory.chat_memory.add_user_message(message["output"])
        else:
            memory.chat_memory.add_ai_message(message["output"])

    cl.user_session.set("memory", memory)

    setup_runnable()


@cl.on_message
async def on_message(message: cl.Message):
    if message.command == "export_all_chat_history":
        file_element = await export_all_chat_history()
        await cl.Message(
            content="Here is your encrypted chat history.",
            elements=[file_element],
        ).send() 
        return
    else:
        memory = cl.user_session.get("memory")  # type: ConversationBufferMemory

        runnable = cl.user_session.get("runnable")  # type: Runnable

        res = cl.Message(content="")

        async for chunk in runnable.astream(
            {"question": message.content},
            config=RunnableConfig(),
        ):
            await res.stream_token(chunk)

        await res.send()

    memory.chat_memory.add_user_message(message.content)
    memory.chat_memory.add_ai_message(res.content)



# Only needed if you plan to store large elements (images, PDFs, etc.) in a cloud bucket:
# from chainlit.data.storage_clients import AzureStorageClient, S3StorageClient

"""
Set up your data layer. This will ensure that Chainlit uses the specified
DB for persisting users, threads, messages, etc.
"""

@cl.data_layer
def get_data_layer():
    # For a local SQLite database using an async driver (aiosqlite):
    return SQLAlchemyDataLayer(conninfo="sqlite+aiosqlite:///chainlit_db.db")

    # Example for PostgreSQL with asyncpg:
    # return SQLAlchemyDataLayer(conninfo="postgresql+asyncpg://user:password@localhost:5432/mydb")

    # If you also want to store chainlit Elements (images, PDFs, etc.) in Azure:
    # storage_client = AzureStorageClient(account_url="<your_account_url>", container="<your_container>")
    # return SQLAlchemyDataLayer(conninfo="<postgres_connection_string>", storage_provider=storage_client)



