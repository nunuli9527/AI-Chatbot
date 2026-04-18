import streamlit  as st
import os
from openai import OpenAI
from datetime import datetime
import json

from streamlit.runtime.state import session_state

# 设置页面的配置项
st.set_page_config(
    # 标签名
    page_title="AI智能伴侣",
    page_icon="🤖",
    # 布局
    layout="wide",
    # 控制侧边栏的状态
    initial_sidebar_state="expanded",
)

# 生成会话名称函数
def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# 保存会话信息函数
def save_session():
    if st.session_state.current_session:
        # 构建会话数据
        session_data = {
            "nick_name": st.session_state.nick_name,
            "nature": st.session_state.nature,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }

        # 如果sessions文件夹不存在，则创建
        if not os.path.exists("sessions"):
            os.mkdir("sessions")

        # 保存会话数据
        with open(f"./sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=4)

# 加载所有的会话列表信息
def sessions_list():
    session_list = []
    # 加载session目录下所有文件
    if os.path.exists("sessions"):
        session = os.listdir("sessions")
        for filename in session:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    session_list.sort(reverse=True)
    return session_list

# 加载指定会话信息
def load_session(session_name):
    try:
        if os.path.exists(f"./sessions/{session_name}.json"):
            with open(f"./sessions/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.nature = session_data["nature"]
                st.session_state.current_session = session_name
                st.session_state.messages = session_data["messages"]
    except Exception:
        st.error("读取会话信息失败")

def delete_session(session_name):
    try:
        if os.path.exists(f"./sessions/{session_name}.json"):
            os.remove(f"./sessions/{session_name}.json")    #删除文件
            # 如果删除的是当前会话，则需要更新当前消息列表
            if session_name == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
    except Exception:
        st.error("删除会话信息失败")

# 大标题
st.title("AI智能伴侣")

# logo
st.logo("./resource/logo.png")

# 提示词
system_prompt = """
        你叫 %s ，现在是用户的真实伴侣，请完全代入伴侣角色。：
        规则：
            1. 每次只回1条消息
            2. 禁止任何场景或状态描述性文字
            3. 匹配用户的语言
            4. 回复简短，像微信聊天一样
            5. 有需要的话可以用❤️🌸等emoji表情
            6. 用符合伴侣性格的方式对话
            7. 回复的内容, 要充分体现伴侣的性格特征
        伴侣性格：
            - %s
        你必须严格遵守上述规则来回复用户。
    """

# 创建与AI大模型交互的客户端对象(DEEPSEEK_API_KEY 环境变量的名字, 值就是DeepSeek的API_KEY的值)
client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

# 创建会话
if "messages" not in st.session_state:
    st.session_state.messages = []   # {"role": "user", "content": "你好"}

if "nick_name" not in st.session_state:
    st.session_state.nick_name = "小甜心"

if "nature" not in st.session_state:
    st.session_state.nature = "性格开朗活泼的东北女孩"

if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()

# 显示会话
st.text(f"会话名称: {st.session_state.current_session}")
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

# 创建侧边栏
with st.sidebar:
    # 会话信息
    st.sidebar.subheader("AI控制面板")

    # 新建会话
    if st.button("新建对话", width="stretch", icon="🪶"):
        # 1. 保存当前会话信息
        save_session()

        # 2. 创建新的会话
        if st.session_state.messages:   # 如果有会话信息，则创建新的会话
            st.session_state.messages = []
            st.session_state.current_session = generate_session_name()
            save_session()
            st.rerun()  # 重新运行当前页面

    # 历史会话
    st.text("历史会话")
    session_list = sessions_list()
    for session in session_list:
        col1, col2 = st.columns([4, 1])
        with col1:
            # 加载会话信息
            if st.button(session, width="stretch", icon="📑", key=f"load_{session}", type=f"primary" if session == st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()
        with col2:
            # 删除会话信息
            if st.button("", width="stretch", icon="❌️", key=f"defo_{session}"):
                delete_session(session)
                st.rerun()

    # 分割线
    st.divider()

    # 下半部分
    st.sidebar.subheader("伴侣信息")

    nick_name = st.text_input("昵称", placeholder= "请输入昵称", value=st.session_state.nick_name)
    if nick_name:
        st.session_state["nick_name"] = nick_name

    nature = st.text_area("性格", placeholder= "请输入性格", value=st.session_state.nature)
    if nature:
        st.session_state["nature"] = nature

# 消息输入框
prompt = st.chat_input("请输入你的问题")
if prompt:
    st.chat_message("user").write(prompt)
    print("---------------------->调用AI大模型, 提示词: ",  prompt)
    # 保存用户输入的提示词
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 与AI大模型进行交互(参数)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system","content": system_prompt % (st.session_state.nick_name, st.session_state.nature)},
            *st.session_state.messages
            # *[{"role": message["role"], "content": message["content"]} for message in st.session_state.messages if message["role"] != "system"]
        ],
        stream=True
    )

    # 输出大模型返回的结果(非流式输出的解析方式)
    # print("<---------------------响应结果: ", response.choices[0].message.content)
    # st.chat_message("assistant").write(response.choices[0].message.content)

    # 输出大模型返回的结果(流式输出的解析方式)
    response_message = st.empty()   # 创建一个空的组件

    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            full_response += chunk.choices[0].delta.content
            response_message.chat_message("assistant").write(full_response)
            #不使用st，而是用那个空组件，这样再显示就会更新空组件，而不是使用st多次输出

    # 保存大模型返回的提示词
    # st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # 保存会话信息
    save_session()
