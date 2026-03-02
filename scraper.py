# 安裝：pip install supabase
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

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
