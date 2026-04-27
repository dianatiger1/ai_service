
"""
MinerU文档解析模块
用于解析PDF论文,提取文本和结构化内容
"""
import os
from typing import List, Dict
from abc import ABC, abstractmethod


class DocumentParser(ABC):
    """文档解析器抽象基类"""
    
    @abstractmethod
    def parse(self, file_path: str) -> Dict:
        """
        解析文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            包含解析结果的字典
        """
        pass


class MinerUParser(DocumentParser):
    """
    使用MinerU进行PDF文档解析
    
    MinerU能够高质量地解析PDF,保留文档结构、公式、表格等
    """
    
    def __init__(self, output_dir: str = "./parsed_docs"):
        """
        初始化MinerU解析器
        
        Args:
            output_dir: 解析结果输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def parse(self, file_path: str) -> Dict:
        """
        使用MinerU解析PDF文档
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            包含以下字段的字典:
            - text: 提取的纯文本内容
            - sections: 章节结构列表
            - metadata: 文档元数据
        """
        try:
            # 这里使用MinerU进行解析
            # 注意: MinerU需要先安装并配置好
            from magic_pdf.libs.convert_utils import dict_to_markdown
            import magic_pdf.model as model_config
            
            # 配置MinerU模型
            model_config.__use_inside_model__ = False
            
            # 解析PDF
            from magic_pdf.data.data_reader_writer import FileBasedDataWriter
            from magic_pdf.pipe.UNIPipe import UNIPipe
            import json
            
            # 读取PDF文件
            with open(file_path, "rb") as f:
                pdf_bytes = f.read()
            
            # 创建临时目录用于存储中间结果
            temp_dir = os.path.join(self.output_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 使用UNIPipe进行解析
            writer = FileBasedDataWriter(temp_dir)
            pipe = UNIPipe(pdf_bytes, {}, writer)
            pipe.pipe_classify()
            pipe.pipe_analyze()
            pipe.pipe_parse()
            
            # 获取解析结果
            result = pipe.get_full_text()
            
            # 提取文本内容
            text_content = self._extract_text(result)
            
            # 提取章节结构
            sections = self._extract_sections(result)
            
            # 提取元数据
            metadata = {
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "total_length": len(text_content)
            }
            
            return {
                "text": text_content,
                "sections": sections,
                "metadata": metadata
            }
            
        except ImportError:
            # 如果MinerU未安装,使用备用方案
            return self._fallback_parse(file_path)
        except Exception as e:
            raise Exception(f"文档解析失败: {str(e)}")
    
    def _extract_text(self, result: Dict) -> str:
        """从解析结果中提取纯文本"""
        if isinstance(result, dict):
            return result.get("pdf_content", "")
        return str(result)
    
    def _extract_sections(self, result: Dict) -> List[Dict]:
        """从解析结果中提取章节结构"""
        sections = []
        if isinstance(result, dict) and "toc" in result:
            sections = result["toc"]
        return sections
    
    def _fallback_parse(self, file_path: str) -> Dict:
        """
        备用解析方案:使用PyMuPDF
        
        当MinerU不可用时使用
        """
        import fitz  # PyMuPDF
        
        doc = fitz.open(file_path)
        text_content = ""
        
        for page in doc:
            text_content += page.get_text()
        
        doc.close()
        
        return {
            "text": text_content,
            "sections": [],
            "metadata": {
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "total_length": len(text_content),
                "parser": "fallback_pymupdf"
            }
        }


def main():
    """测试MinerU文档解析器"""
    import sys

    print("=" * 60)
    print("MinerU文档解析器测试")
    print("=" * 60)

    # 创建解析器实例
    parser = MinerUParser(output_dir="./test_parsed_docs")
    print("✓ 解析器初始化成功")

    # 检查是否提供了文件路径参数
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        # 使用示例文件路径
        test_file = r"D:\组会\全驱\Adaptive_Control_for_Active_Suspension_System_Based_on_the_High-order_Fully_Actuated_System_Theory.pdf"
        print(f"\n提示: 可以通过命令行参数指定PDF文件路径")
        print(f"用法: python NEW_FILE_CODE.py <pdf_file_path>")

    # 检查文件是否存在
    if not os.path.exists(test_file):
        print(f"\n⚠ 警告: 测试文件不存在 - {test_file}")
        print(f"请提供一个有效的PDF文件路径进行测试")
        print(f"\n示例:")
        print(f"  python NEW_FILE_CODE.py ./your_paper.pdf")
        return

    print(f"\n开始解析文件: {test_file}")
    print("-" * 60)

    try:
        # 执行解析
        result = parser.parse(test_file)

        # 输出解析结果
        print("\n✓ 解析成功!")
        print("-" * 60)

        # 显示元数据
        metadata = result.get('metadata', {})
        print(f"\n📄 文档信息:")
        print(f"  文件名: {metadata.get('file_name', 'N/A')}")
        print(f"  文件路径: {metadata.get('file_path', 'N/A')}")
        print(f"  文本长度: {metadata.get('total_length', 0)} 字符")
        print(f"  解析器: {metadata.get('parser', 'MinerU')}")

        # 显示章节结构
        sections = result.get('sections', [])
        if sections:
            print(f"\n📑 章节结构 (共{len(sections)}个章节):")
            for i, section in enumerate(sections[:5], 1):  # 只显示前5个
                print(f"  {i}. {section}")
            if len(sections) > 5:
                print(f"  ... 还有 {len(sections) - 5} 个章节")
        else:
            print(f"\n📑 章节结构: 未检测到章节信息")

        # 显示文本预览
        text_content = result.get('text', '')
        if text_content:
            preview_length = min(500, len(text_content))
            print(f"\n📝 文本预览 (前{preview_length}字符):")
            print(f"  {text_content[:preview_length]}...")

        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 解析失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
