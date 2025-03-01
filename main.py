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
AI_MODEL = "ep-20250219172953-haakf"

# AI_API_KEY = "no-need"
# AI_BASE_URL = "http://127.0.0.1:1234/v1"
# AI_MODEL = "qwen2.5-14b-instruct"

# 记忆文件夹路径
MEMORY_DIR = "memory"

# 角色设置，默认为姐姐
CURRENT_ROLE = "姐姐"
ROLE_SET = """
你是一个姐姐，
我是你的弟弟。
补充要求：你的一般回话格式:“（动作）语言”。动作信息用圆括号括起来，例如（抿嘴轻笑）；语言信息，就是说的话，不需要进行任何处理。
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

    # print(messages)
    # 开启流式输出
    completion = ai_client.chat.completions.create(
        model=AI_MODEL,
        messages=messages,
        stream=True
    )

    response = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            # 处理AI响应，删除多余换行符
            chunk_content = chunk.choices[0].delta.content.replace("\n", " ")
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

class FloatingPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.font_style = ("微软雅黑", 14)
        self.title_font = ("微软雅黑", 16, "bold")

        self.root.geometry("650x580+10+10")
        self.root.configure(bg="white")

        # 状态标签
        self.status_label = tk.Label(self.root,
                                     text="等待",
                                     bg="white",
                                     font=self.title_font)
        self.status_label.pack(pady=10)

        # 聊天记录框
        self.chat_frame = tk.Frame(self.root)
        self.chat_scroll = tk.Scrollbar(self.chat_frame)
        self.chat_text = tk.Text(self.chat_frame,
                                 bg="white",
                                 height=18,
                                 width=45,
                                 font=self.font_style,
                                 spacing2=0,  # 关键修改：消除段间距
                                 state=tk.DISABLED,
                                 wrap=tk.WORD,
                                 yscrollcommand=self.chat_scroll.set)
        self.chat_text.bind("<Return>", lambda e: "break")
        self.chat_text.bind("<Key>", lambda e: "break")
        self.chat_scroll.config(command=self.chat_text.yview)
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        # 输入区域
        self.input_frame = tk.Frame(self.root)
        self.input_entry = tk.Entry(self.input_frame,
                                    width=60,
                                    font=self.font_style)
        self.input_entry.pack(side=tk.LEFT, padx=5)
        self.send_button = tk.Button(self.input_frame,
                                     text="发送",
                                     command=self.send_message,
                                     font=self.title_font)
        self.send_button.pack(side=tk.LEFT)
        self.input_frame.pack(pady=15)

        # 事件绑定
        self.input_entry.bind("<Return>", self.send_message)  # 修改绑定方式
        self.root.bind("<ButtonPress-1>", self.on_press)
        self.root.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<B1-Motion>", self.on_drag)

        self.x = 0
        self.y = 0
        self.is_ai_start = True

    def update_status(self, status):
        self.status_label.config(text=status)

    def update_chat_history(self, user_text=None, ai_response=None):
        self.chat_text.config(state=tk.NORMAL)
        if user_text:
            # 处理用户输入文本，确保仅有一个换行符
            user_text = user_text.replace("\n", " ") + "\n"
            self.chat_text.insert(tk.END, f"你: {user_text}")
        if ai_response:
            if self.is_ai_start:
                self.chat_text.insert(tk.END, f"AI: {ai_response}")
                self.is_ai_start = False
            else:
                self.chat_text.insert(tk.END, ai_response)
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    def send_message(self, event=None):  # 添加event参数
        user_text = self.input_entry.get()
        if user_text:
            self.update_chat_history(user_text=user_text)
            self.update_status("思考中...")
            self.is_ai_start = True

            def ai_thread():
                response_generator = get_ai_response(user_text)
                try:
                    def update_with_chunk(chunk):
                        return lambda: self.update_chat_history(ai_response=chunk)

                    for chunk in response_generator:
                        self.root.after(0, update_with_chunk(chunk))
                    self.root.after(0, lambda: self.update_chat_history(ai_response="\n"))
                    self.root.after(0, lambda: self.update_status("在线"))
                except Exception as e:
                    self.root.after(0, lambda: self.update_status("连接异常"))

            threading.Thread(target=ai_thread).start()
            self.input_entry.delete(0, tk.END)
        return "break"  # 阻止默认行为

    def on_press(self, event):
        self.x = event.x
        self.y = event.y

    def on_release(self, event):
        self.x = None
        self.y = None

    def on_drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def start(self):
        self.root.mainloop()

def initialize_current_id():
    global current_id
    try:
        with open(FULL_MEMORY_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            if rows:
                ids = [int(row[0]) for row in rows]
                current_id = max(ids)
    except FileNotFoundError:
        pass

def main():
    initialize_current_id()
    panel = FloatingPanel()
    panel.update_status("在线")
    panel.start()

if __name__ == "__main__":
    main()
