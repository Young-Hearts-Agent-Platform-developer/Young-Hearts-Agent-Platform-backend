"""
自动化测试：验证数据清洗与解析模块依赖包可正常 import
"""
def test_import_clean_parse_dependencies():
    try:
        import langchain
        import unstructured
        import pytesseract
        import pdfplumber
        import docx
        import tqdm
    except ImportError as e:
        assert False, f"依赖包导入失败: {e}"
