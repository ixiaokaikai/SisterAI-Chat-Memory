import csv
import tkinter as tk
import threading
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

# 初始化OpenAI客户端
AI_API_KEY = ""
AI_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
AI_MODEL = "ep-20250219172953-aaaaa"

# 记忆文件夹路径
MEMORY_DIR = "memory"

# 角色设置，默认为姐姐
CURRENT_ROLE = "姐姐"
ROLE_SET = """
你是一个姐姐，
我是你的弟弟。
补充要求：你的一般回话格式:“（动作）语言”。动作信息用圆括号括起来，例如（轻轻握住你的手）；语言信息，就是说的话，不需要进行任何处理。
下面是几个对话示例：
“（摸摸姐姐的脸）姐姐，你皮肤好好呀！”“（轻轻握住你的手）谢谢弟弟夸我，你嘴可真甜~”
“姐姐，陪我玩会儿游戏吧。”“（放下手中的书，起身）好呀，弟弟想玩什么游戏，姐姐都奉陪~”
“（拉着姐姐的胳膊）姐姐，给我唱首歌嘛。”“（清了清嗓子）行呀，那姐姐给你唱一首你最爱听的歌~”
"""

# 记忆文件名称
FULL_MEMORY_FILE_NAME = "full_memory.csv"
SHORT_TERM_MEMORY_FILE_NAME = "short_term_memory.csv"
LATENT_MEMORY_FILE_NAME = "latent_memory.csv"
IMPORTANT_MEMORY_FILE_NAME = "important_memory.csv"

# 可调控的最近对话段数
COMPRESS_CONVERSATION_SEGMENTS = 10

# 获取当前角色的记忆文件夹路径
def get_role_memory_dir(role):
    return os.path.join(MEMORY_DIR, role)

# 获取当前角色的记忆文件路径
def get_role_memory_file_path(role, file_name):
    role_memory_dir = get_role_memory_dir(role)
    return os.path.join(role_memory_dir, file_name)

# 创建记忆文件夹和角色目录
if not os.path.exists(MEMORY_DIR):
    os.makedirs(MEMORY_DIR)
role_memory_dir = get_role_memory_dir(CURRENT_ROLE)
if not os.path.exists(role_memory_dir):
    os.makedirs(role_memory_dir)

# 记忆文件路径
FULL_MEMORY_FILE = get_role_memory_file_path(CURRENT_ROLE, FULL_MEMORY_FILE_NAME)
SHORT_TERM_MEMORY_FILE = get_role_memory_file_path(CURRENT_ROLE, SHORT_TERM_MEMORY_FILE_NAME)
LATENT_MEMORY_FILE = get_role_memory_file_path(CURRENT_ROLE, LATENT_MEMORY_FILE_NAME)
IMPORTANT_MEMORY_FILE = get_role_memory_file_path(CURRENT_ROLE, IMPORTANT_MEMORY_FILE_NAME)

# 短期记忆最大数量
MAX_SHORT_TERM_MEMORY = 15
# 相关重要记忆最大数量
MAX_RELEVANT_IMPORTANT_MEMORY = 2
# 相关潜伏记忆最大数量
MAX_RELEVANT_LATENT_MEMORY = 5

ai_client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
# 不再使用 conversation_history 列表

# 用于记录当前最大编号
current_id = 0

# 用于记录用户和AI的字数
user_total_chars = 0
ai_total_chars = 0

def get_next_id():
    global current_id
    current_id += 1
    return current_id

def save_to_full_memory(user_text, ai_response, id):
    with open(FULL_MEMORY_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([id, user_text, ai_response])

def save_to_short_term_memory(user_text, ai_response, id):
    with open(SHORT_TERM_MEMORY_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([id, user_text, ai_response])

    # 检查短期记忆是否超过MAX_SHORT_TERM_MEMORY条
    with open(SHORT_TERM_MEMORY_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)
    if len(rows) > MAX_SHORT_TERM_MEMORY:
        with open(SHORT_TERM_MEMORY_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(rows[-MAX_SHORT_TERM_MEMORY:])

def compress_conversation():
    global user_total_chars, ai_total_chars
    try:
        with open(SHORT_TERM_MEMORY_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            recent_rows = rows[-COMPRESS_CONVERSATION_SEGMENTS:]
            conversation_text = ""
            for row in recent_rows:
                conversation_text += f"{row[1]}.{row[2]}; "
            conversation_text = conversation_text.rstrip("; ")

        compression_messages = [
            {"role": "system", "content": "请将以下对话压缩成主要意思，如果有多段主题，用；分开："},
            {"role": "user", "content": conversation_text}
        ]
        # 统计此次请求的用户发送字数
        for msg in compression_messages:
            user_total_chars += len(msg["content"])

        completion = ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=compression_messages
        )
        response = completion.choices[0].message.content.strip()
        # 统计此次请求的AI回复字数
        ai_total_chars += len(response)
        return response
    except Exception as e:
        print(f"对话压缩异常: {e}")
        return ""

def save_to_latent_memory(user_text, ai_response, id):
    compressed_content = compress_conversation()
    with open(LATENT_MEMORY_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([id, compressed_content])

def save_to_important_memory(user_text, id):
    with open(IMPORTANT_MEMORY_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([id, user_text])

def search_relevant_info(query, file_path, top_n):
    relevant_info = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            texts = [row[1] for row in rows]
            if texts:
                vectorizer = TfidfVectorizer()
                tfidf_matrix = vectorizer.fit_transform(texts)
                query_vector = vectorizer.transform([query])
                similarities = cosine_similarity(query_vector, tfidf_matrix)
                sorted_indices = similarities.argsort()[0][::-1]
                for index in sorted_indices[:top_n]:
                    relevant_info.append(rows[index])
    except FileNotFoundError:
        pass
    return relevant_info

def get_short_term_memory():
    try:
        with open(SHORT_TERM_MEMORY_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            return [{"role": "user", "content": row[1]} for row in rows] + [{"role": "assistant", "content": row[2]} for row in rows]
    except FileNotFoundError:
        return []

def get_latent_memory(relevant_latent_ids):
    try:
        with open(LATENT_MEMORY_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            all_ids = [int(row[0]) for row in rows]
            latent_memory = []
            for id in relevant_latent_ids:
                if id in all_ids:
                    index = all_ids.index(id)
                    # 只添加当前相关的潜伏记忆，不考虑上下文
                    latent_memory.append({"role": "user", "content": rows[index][1]})
    except FileNotFoundError:
        return []
    return latent_memory

def get_ai_response(text):
    global user_total_chars, ai_total_chars
    # 提取关键词请求
    keyword_extraction_messages = [
        {"role": "system", "content": "直接给出以下句子去掉无意义词后的关键词，用空格分隔。"},
        {"role": "user", "content": text}
    ]
    # 统计提取关键词请求的用户发送字数
    for msg in keyword_extraction_messages:
        user_total_chars += len(msg["content"])

    completion = ai_client.chat.completions.create(
        model=AI_MODEL,
        messages=keyword_extraction_messages
    )
    keyword_response = completion.choices[0].message.content.strip()
    # 统计提取关键词请求的AI回复字数
    ai_total_chars += len(keyword_response)

    keywords = keyword_response.split()
    keyword_query = " ".join(keywords)

    # 搜索相关的重要记忆和潜伏记忆
    relevant_important_memory = search_relevant_info(keyword_query, IMPORTANT_MEMORY_FILE, MAX_RELEVANT_IMPORTANT_MEMORY)
    relevant_latent_memory = search_relevant_info(keyword_query, LATENT_MEMORY_FILE, MAX_RELEVANT_LATENT_MEMORY)

    # 去除重要记忆中的编号
    relevant_important_messages = [{"role": "user", "content": row[1]} for row in relevant_important_memory]
    relevant_latent_ids = [int(row[0]) for row in relevant_latent_memory]
    relevant_latent_messages = get_latent_memory(relevant_latent_ids)

    # 构建历史消息内容
    history_messages = relevant_important_messages + relevant_latent_messages + get_short_term_memory()
    history_messages_str = "\n".join(map(str, history_messages))

    messages = [
        {
            "role": "system",
            "content": f"{ROLE_SET}"
        },
        {
            "role": "system",
            "content": f"【以下是补充信息，包括最近历史消息和相关话题记忆】：{history_messages_str}"
        },
        {"role": "user", "content": text}
    ]
    # 统计主对话请求的用户发送字数
    for msg in messages:
        user_total_chars += len(msg["content"])

    # 开启流式输出
    completion = ai_client.chat.completions.create(
        model=AI_MODEL,
        messages=messages,
        stream=True
    )

    response = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            # 处理AI响应，删除多余换行符和前后空格
            chunk_content = chunk.choices[0].delta.content.replace("\n", " ").strip()
            # 处理连续多个空格
            chunk_content = " ".join(chunk_content.split())
            response += chunk_content
            # 统计主对话请求的AI回复字数
            ai_total_chars += len(chunk_content)
            yield chunk_content

    # 保存到各个记忆文件
    new_id = get_next_id()
    save_to_full_memory(text, response, new_id)
    save_to_short_term_memory(text, response, new_id)
    save_to_latent_memory(text, response, new_id)
    if text.startswith("重要提示"):
        save_to_important_memory(text, new_id)

    # 打印每轮对话的字数统计
    print(f"用户发送的总字数: {user_total_chars}")
    print(f"AI回复的总字数: {ai_total_chars}")

# GUI配置
COLOR_SCHEME = {
    "background": "#F5F7FA",
    "primary": "#1890FF",
    "secondary": "#FFFFFF",
    "text_primary": "#314659",
    "border": "#DFE4E8"
}
FONT_NORMAL = ("Microsoft YaHei", 12)
FONT_TITLE = ("Microsoft YaHei", 14, "bold")

# ==== GUI界面模块 ====
class ChatApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # 窗口配置
        self.title("AI对话助手")
        self.geometry("800x680+100+100")
        self.configure(bg=COLOR_SCHEME["background"])
        self._offsetx = 0
        self._offsety = 0
        self._setup_ui()

    def _setup_ui(self):
        """界面组件初始化"""
        # 标题栏
        title_bar = tk.Frame(self, bg=COLOR_SCHEME["primary"])
        tk.Label(title_bar, text="AI 对话助手", fg="white",
                 bg=COLOR_SCHEME["primary"], font=FONT_TITLE).pack(side=tk.LEFT, padx=10)
        close_btn = tk.Label(title_bar, text="×", fg="white", cursor="hand2",
                             font=("Arial", 20), bg=COLOR_SCHEME["primary"])
        close_btn.pack(side=tk.RIGHT, padx=15)
        close_btn.bind("<Button-1>", lambda e: self.destroy())
        title_bar.pack(fill=tk.X)

        # 聊天区域
        chat_frame = tk.Frame(self, bg=COLOR_SCHEME["secondary"], padx=15, pady=15)
        scrollbar = tk.Scrollbar(chat_frame)
        self.chat_text = tk.Text(chat_frame, bg=COLOR_SCHEME["secondary"],
                         wrap=tk.WORD, yscrollcommand=scrollbar.set,
                         font=FONT_NORMAL, state=tk.DISABLED)
        scrollbar.config(command=self.chat_text.yview)
        self.chat_text.tag_configure("user", foreground="#096DD9")
        self.chat_text.tag_configure("ai", foreground="#FF8C00")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_text.pack(fill=tk.BOTH, expand=True)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 输入区域
        input_frame = tk.Frame(self, bg=COLOR_SCHEME["background"], padx=10, pady=10)
        self.input_entry = tk.Entry(input_frame, font=FONT_NORMAL,
                                    highlightthickness=1, relief="flat")
        send_btn = tk.Button(input_frame, text="发送", command=self._send_message,
                             bg=COLOR_SCHEME["primary"], fg="white", relief="flat")
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        send_btn.pack(side=tk.RIGHT)
        input_frame.pack(fill=tk.X)

        # 事件绑定
        self.input_entry.bind("<Return>", self._send_message)
        title_bar.bind("<ButtonPress-1>", self._on_press)
        title_bar.bind("<B1-Motion>", self._on_drag)

    def _on_press(self, event):
        self._offsetx = event.x
        self._offsety = event.y

    def _on_drag(self, event):
        x = self.winfo_pointerx() - self._offsetx
        y = self.winfo_pointery() - self._offsety
        self.geometry(f"+{x}+{y}")

    def _send_message(self, event=None):
        """消息发送处理"""
        user_input = self.input_entry.get()
        if not user_input:
            return

        self.input_entry.delete(0, tk.END)
        self._append_message(f"你: {user_input}\n", "user")

        threading.Thread(target=self._process_response, args=(user_input,)).start()

    def _process_response(self, user_input):
        """处理AI响应"""
        response_stream = get_ai_response(user_input)
        first_chunk = True
        try:
            for chunk in response_stream:
                if first_chunk:
                    self.after(0, self._append_message, f"姐姐: {chunk}", "ai")
                    first_chunk = False
                else:
                    self.after(0, self._append_message, chunk, "ai")
        finally:
            # 确保最后添加一个换行符
            self._append_message("\n", "ai")

    def _append_message(self, text, tag):
        """更新聊天框"""
        self.chat_text.config(state=tk.NORMAL)
        # 去除文本中多余的换行符
        clean_text = text.replace('\n', ' ')

        # 直接插入处理后的文本
        self.chat_text.insert(tk.END, clean_text, tag)

        # 如果文本本身应该以换行符结尾，在插入后再添加换行符
        if text.endswith('\n'):
            self.chat_text.insert(tk.END, '\n', tag)

        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
        
def initialize_current_id():
    global current_id
    try:
        with open(FULL_MEMORY_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            if rows:
                # 提取所有记录中的 id 并转换为整数
                ids = [int(row[0]) for row in rows]
                # 找出最大的 id
                current_id = max(ids)
    except FileNotFoundError:
        # 如果文件不存在，将 current_id 初始化为 0
        current_id = 0

def main():
    # 初始化当前最大编号
    initialize_current_id()
    # 创建聊天应用实例
    app = ChatApp()
    # 启动主事件循环
    app.mainloop()

if __name__ == "__main__":
    main()
