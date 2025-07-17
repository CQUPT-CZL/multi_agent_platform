from tavily import TavilyClient
from mcp.server.fastmcp import FastMCP
import os
import dotenv
import re

dotenv.load_dotenv()

mcp = FastMCP(
    host="0.0.0.0",  # Host address (0.0.0.0 allows connections from any IP)
    port=8006,  # Port number for the server
    )

def clean_text(text):
    """清理文本中的乱码和特殊字符"""
    if not text:
        return text
    
    # 移除十六进制编码的乱码
    text = re.sub(r'\\x[0-9a-fA-F]{2}', '', text)
    # 移除其他特殊字符
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    # 清理多余的空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

@mcp.tool()
async def get_result(query: str):
    """
    当你遇到不知道一些不知道的问题时（比如一些实时问题），使用搜索工具并返回结果
    """
    try:
        tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        response = tavily_client.search(query=query)
        
        # 清理和格式化返回结果
        cleaned_results = []
        for result in response.get('results', []):
            cleaned_result = {
                'title': clean_text(result.get('title', '')),
                'content': clean_text(result.get('content', '')),
                'url': result.get('url', ''),
                'score': result.get('score', 0)
            }
            # 只保留有效内容的结果
            if cleaned_result['title'] and cleaned_result['content']:
                cleaned_results.append(cleaned_result)
        
        # 返回清理后的结果
        cleaned_response = {
            'query': query,
            'results': cleaned_results[:5],  # 只返回前5个最相关的结果
            'total_results': len(cleaned_results)
        }
        
        print(f"搜索查询: {query}")
        print(f"返回结果数量: {len(cleaned_results)}")
        
        return cleaned_response
        
    except Exception as e:
        print(f"搜索出错: {str(e)}")
        return {
            'query': query,
            'error': f"搜索失败: {str(e)}",
            'results': [],
            'total_results': 0
        }

if __name__ == "__main__":
    mcp.run(transport="streamable-http")