import sys
import io
# 修复控制台输出编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


from openai import OpenAI

# 初始化客户端
# 注意：千万不要把 Key 直接写死在代码里上传到 GitHub，会被秒封！
# 建议通过环境变量获取，或者在本地测试时小心使用
client = OpenAI(
    api_key="sk-vN1JPLmnkjp740WRDyDQBWEOqagOpVL14ZPG0kAWF1HRISsW" ,
    # 如果你在国内，可能需要配置 base_url，通常是中转服务的地址
    base_url="https://sg.uiuiapi.com/v1" 
)

def chat_with_ai():
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 性价比之王，适合测试
            messages=[
                {"role": "system", "content": "你是一个资深的Python代码优化助手。"},
                {"role": "user", "content": "帮我写一个快速排序算法。"}
            ]
        )
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"哎呀，出错了：{e}")

if __name__ == "__main__":
    chat_with_ai()