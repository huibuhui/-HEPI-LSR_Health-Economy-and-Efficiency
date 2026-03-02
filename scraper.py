import os
import smtplib
from email.mime.text import MIMEText
from Bio import Entrez
import google.generativeai as genai
from supabase import create_client # 安裝：pip install supabase

# --- 1. 環境配置 ---
# 從 GitHub Secrets 自動讀取變數
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SENDER_EMAIL = "bitesize00004@gmail.com"  # <--- 請修改為你的 Gmail
RECEIVER_EMAIL = "bitesize00004@gmail.com"     # <--- 請修改為收件信箱

# 設定 Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# 設定 PubMed (Entrez 要求提供 Email 以利追蹤)
Entrez.email = SENDER_EMAIL

def fetch_pubmed_abstracts(query, max_results=3):
    """從 PubMed 搜尋關鍵字並抓取摘要"""
    print(f"正在搜尋 PubMed: {query}...")
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    ids = record["IdList"]
    
    results = []
    if not ids:
        return "今日無相關新論文。"

    fetch_handle = Entrez.efetch(db="pubmed", id=ids, rettype="abstract", retmode="text")
    abstracts = fetch_handle.read()
    return abstracts

def analyze_with_ai(content):
    """使用 Gemini 分析內容並摘要"""
    print("正在使用 Gemini AI 進行分析...")
    prompt = f"你是一名醫療經濟專家。請將以下論文摘要整理成繁體中文簡報要點，包含研究目的、核心結論與對健康效率的啟示：\n\n{content}"
    response = model.generate_content(prompt)
    return response.text

def send_email(subject, body):
    """透過 SMTP 發送郵件"""
    print("正在發送郵件...")
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print("郵件發送成功！")
    except Exception as e:
        print(f"郵件發送失敗: {e}")

# --- 主流程 ---
if __name__ == "__main__":
    # 搜尋關鍵字 (可根據你的儲存庫主題修改)
    search_query = "Health Economy Efficiency AND 2026[Date - Publication]"
    
    # 1. 抓取資料
    raw_data = fetch_pubmed_abstracts(search_query)
    
    # 2. AI 分析
    ai_report = analyze_with_ai(raw_data)
    
    # 3. 發送報告
    email_title = f"【自動報表】今日 PubMed 醫療經濟論文分析"
    send_email(email_title, ai_report)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# --- SQL 自動化，加入資料庫寫入邏輯： ---
def save_to_sql(paper_list):
    for paper in paper_list:
        # 使用 upsert：如果 PMID 已存在則更新，不存在則插入
        data = {
            "pmid": paper['PMID'],
            "title": paper['Title'],
            "abstract": paper['Abstract'],
            "efficiency_score": paper['AI_Score'],
            "ai_summary": paper['AI_Summary']
        }
        supabase.table("health_econ_papers").upsert(data).execute()
