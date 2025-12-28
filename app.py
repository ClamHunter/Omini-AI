import streamlit as st 
from openai import OpenAI
import threading
# --- 核心修复：兼容性导入 ---
try:
    # 尝试路径 A (较新版本常用)
    from streamlit.runtime.scriptrunner.script_run_context import add_script_run_ctx
except ImportError:
    try:
        # 尝试路径 B (部分旧版本)
        from streamlit.runtime.scriptrunner import add_script_run_ctx
    except ImportError:
        # 如果都找不到，定义一个空函数防止崩溃
        def add_script_run_ctx(thread):
            pass

#页面标题和布局
st.set_page_config(page_title="AI 对比助手", layout="wide")
st.title("DeepSeeK vs 豆包：全能对比面板")

#侧边栏：填写你的api信息
with st.sidebar:
    st.header("api key配置")
    ds_key = st.text_input("DeepSeeK API Key", type="password")
    db_key = st.text_input("豆包 API Key", type="password")
    db_endpoint = st.text_input("豆包接入点ID (Endpoint ID)", placeholder= "接入代码:ep-xxxxxx")
    st.info("key仅用于本次会话，不会被存储。")

#主区域：输入对比内容
user_prompt = st.text_area("请输入你的指令或问题，用于对比两款AI的回答效果。", placeholder="例如：请帮我写一段Python代码，实现冒泡排序算法。")

#4.定义调用API的逻辑
def get_ai_response(client,model_name,prompt,container):
    try:
        #使用流式响应
        client = OpenAI(api_key=client.api_key, base_url=client.base_url)
        response = client.chat.completions.create(
            model= model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=True  #启用流式响应
        )
        #在指定的容器中实时渲染文字
        container.write_stream(response)
    except Exception as e:
        st.error(f"调用AI模型时出错: {e}")
        return None
    
#5.按钮：点击后同时出发
if st.button("开始对比"):
    if not ds_key or not db_key or not db_endpoint:
        st.warning("请确保已填写所有API Key和接入点ID。")
    elif not user_prompt:
        st.warning("请输入指令内容。")
    else:
        #创建两列布局,再给每一个AI模型分配一列
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("DeepSeeK")
            box1 = st.empty()  #用于DeepSeeK的回答显示容器
        with col2:
            st.subheader("豆包")
            box2 = st.empty()  #用于豆包的回答显示容器
            
        #----------DeepSeeK----------
            ds_client = OpenAI(api_key = ds_key,base_url="https://api.deepseek.com")
        #----------豆包----------
            db_client = OpenAI(api_key = db_key,base_url="https://ark.cn-beijing.volces.com/api/v3")

        #使用多线程同时调用两个API
        t1 = threading.Thread(target=get_ai_response, args=(ds_client,"deepseek-chat",user_prompt,box1))
        t2 = threading.Thread(target=get_ai_response, args=(db_client,db_endpoint,user_prompt,box2))

        #确保线程可以在Streamlit环境中运行
        add_script_run_ctx(t1)
        add_script_run_ctx(t2)

        #启动线程
        t1.start()
        t2.start()

        #等待线程完成
        t1.join()
        t2.join()