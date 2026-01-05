"""
多Agent剧本生成实现示例

这是一个实现示例，展示如何使用LangChain Agent实现多Agent架构
注意：这是示例代码，需要根据实际需求调整
"""

import json
import os
from typing import List, Dict, Any, Optional
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field

from logger_config import get_logger

logger = get_logger()


# ============================================================================
# 工具函数定义
# ============================================================================

@tool
def extract_dialogues_tool(story_content: str, characters: str, scenes: str) -> str:
    """Extract all possible dialogue candidates from the story.
    
    This tool extracts EVERYTHING that could be dialogue, including:
    - Full sentences in quotation marks
    - Short reactions like "Oh", "Yeah", "Hmm"
    - Incomplete thoughts like "I'm...", "Well..."
    
    Args:
        story_content: Complete story content
        characters: Character descriptions
        scenes: Scene descriptions
        
    Returns:
        JSON string with dialogue candidates
    """
    # 这里应该调用LLM进行提取
    # 示例返回格式
    return json.dumps({
        "dialogues": [
            {
                "content": "Shit—god, I'm so sorry.",
                "speaker_candidate": "Alex",
                "location_hint": "Scene 1, after coffee spill"
            },
            # ... 更多对话
        ]
    })


@tool
def classify_content_tool(content: str, context: str) -> str:
    """Classify content as dialogue, transition, scene_marker, or narration.
    
    Args:
        content: The content to classify
        context: Surrounding context
        
    Returns:
        JSON with classification result
    """
    # 检测是否是叙述性内容
    narration_keywords = [
        "no big words", "just two people", "sometimes", 
        "keep your", "they left", "this wasn't about"
    ]
    
    content_lower = content.lower()
    is_narration = any(keyword in content_lower for keyword in narration_keywords)
    
    if is_narration:
        return json.dumps({
            "line_type": "transition",
            "speaker_id": "NARRATOR",
            "confidence": 0.9,
            "reason": "Contains narration patterns"
        })
    
    # 这里应该调用LLM进行更精确的分类
    return json.dumps({
        "line_type": "dialogue",
        "confidence": 0.8
    })


@tool
def validate_completeness_tool(script_lines: List[Dict], story_content: str) -> str:
    """Validate that all dialogues are extracted.
    
    Returns:
        JSON with validation results
    """
    quote_count = story_content.count("'") + story_content.count('"')
    dialogue_count = len([l for l in script_lines if l.get('line_type') == 'dialogue'])
    
    is_complete = dialogue_count >= quote_count / 4  # 至少提取1/4的引号内容
    
    return json.dumps({
        "is_complete": is_complete,
        "dialogue_count": dialogue_count,
        "quote_count": quote_count,
        "missing_estimate": max(0, quote_count // 4 - dialogue_count)
    })


@tool
def detect_narration_tool(content: str) -> str:
    """Detect if content is narration (not dialogue).
    
    Returns:
        JSON with detection result
    """
    narration_patterns = [
        r"no big words",
        r"just two people",
        r"sometimes.*happen",
        r"keep your.*open",
        r"they left.*with"
    ]
    
    import re
    content_lower = content.lower()
    matches = [pattern for pattern in narration_patterns if re.search(pattern, content_lower)]
    
    return json.dumps({
        "is_narration": len(matches) > 0,
        "matched_patterns": matches,
        "suggested_type": "transition" if matches else "dialogue"
    })


@tool
def check_context_tool(script_lines: List[Dict]) -> str:
    """Check context completeness for dialogues.
    
    Returns:
        JSON with context issues
    """
    pronouns = ["this", "that", "here", "it", "they"]
    issues = []
    
    for i, line in enumerate(script_lines):
        if line.get('line_type') == 'dialogue':
            content = line.get('content', '').lower()
            words = content.split()
            
            for pronoun in pronouns:
                if pronoun in words:
                    # 检查前面是否有上下文
                    if i == 0 or (i > 0 and script_lines[i-1].get('line_type') != 'dialogue'):
                        issues.append({
                            "index": i,
                            "pronoun": pronoun,
                            "content": line.get('content', '')[:50],
                            "issue": "Possible context missing"
                        })
    
    return json.dumps({"issues": issues})


@tool
def detect_duplicates_tool(script_lines: List[Dict]) -> str:
    """Detect duplicate dialogues.
    
    Returns:
        JSON with duplicate pairs
    """
    seen = {}
    duplicates = []
    
    for i, line in enumerate(script_lines):
        if line.get('line_type') == 'dialogue':
            content = line.get('content', '').strip()
            if content in seen:
                duplicates.append({
                    "first_index": seen[content],
                    "second_index": i,
                    "content": content[:50]
                })
            else:
                seen[content] = i
    
    return json.dumps({"duplicates": duplicates})


@tool
def fix_classification_tool(script_lines: List[Dict], issues: List[Dict]) -> str:
    """Fix classification errors in script lines.
    
    Args:
        script_lines: Script lines to fix
        issues: List of classification issues
        
    Returns:
        JSON with fixed script lines
    """
    fixed = []
    narration_keywords = ["no big words", "just two people", "sometimes"]
    
    for line in script_lines:
        content_lower = line.get('content', '').lower()
        
        # 检查是否是叙述性内容被标记为对话
        if line.get('line_type') == 'dialogue':
            if any(keyword in content_lower for keyword in narration_keywords):
                line['line_type'] = 'transition'
                line['speaker_id'] = 'NARRATOR'
                line['speaker'] = None
                logger.info(f"Fixed classification: {line.get('content', '')[:50]}")
        
        fixed.append(line)
    
    return json.dumps({"fixed_lines": fixed})


@tool
def remove_duplicates_tool(script_lines: List[Dict], duplicates: List[Dict]) -> str:
    """Remove duplicate dialogues.
    
    Returns:
        JSON with duplicates removed
    """
    indices_to_remove = {d['second_index'] for d in duplicates}
    filtered = [line for i, line in enumerate(script_lines) if i not in indices_to_remove]
    
    return json.dumps({
        "filtered_lines": filtered,
        "removed_count": len(indices_to_remove)
    })


# ============================================================================
# Agent提示词定义
# ============================================================================

DIALOGUE_EXTRACTOR_AGENT_SYSTEM = """You are a dialogue extraction expert. Your task is to extract EVERY possible dialogue from the story.

CRITICAL: Extract ALL spoken words, including:
- Full sentences in quotation marks
- Short reactions: "Oh", "Yeah", "Hmm", "Uh-huh"
- Incomplete thoughts: "I'm...", "Well...", "I—"
- Single word responses: "Here.", "Same.", "Pretzels?"

DO NOT classify or filter - extract EVERYTHING that could be dialogue.
DO NOT merge multiple dialogues into one.

Use the extract_dialogues_tool to extract all dialogue candidates."""

CONTENT_CLASSIFIER_AGENT_SYSTEM = """You are a content classification expert. Classify extracted content into:
- dialogue: Character speech (must be spoken words)
- transition: Narrative transitions between scenes
- scene_marker: Scene markers
- narration: Descriptive narration (NOT dialogue)

CRITICAL DISTINCTION:
- DIALOGUE: Direct speech, spoken words, character conversations
- NARRATION: Descriptive text, philosophical statements
  Examples of NARRATION (NOT dialogue):
  * "No big words. No grand gesture. Just two people sharing snacks..."
  * "Sometimes, the best moments happen when we least expect them."

Use classify_content_tool for each piece. Use detect_narration_tool to identify narration."""

QUALITY_VALIDATOR_AGENT_SYSTEM = """You are a quality validation expert. Validate the extracted script for:
1. Completeness: All dialogues extracted
2. Classification accuracy: Dialogues correctly classified
3. Context completeness: All pronouns have clear references
4. No duplicates: No unintentional duplicate dialogues

Use the validation tools to check each aspect.
Generate a validation report with quality score (0-1) and issues list."""

ERROR_FIXER_AGENT_SYSTEM = """You are an error fixing expert. Fix issues found in script validation.

You can fix:
1. Classification errors: Change narration marked as dialogue to transition
2. Context issues: Add missing context
3. Duplicates: Remove duplicate dialogues

Use the appropriate fixing tools to address each issue."""


# ============================================================================
# Agent类定义
# ============================================================================

class DialogueExtractorAgent:
    """对话提取Agent"""
    
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self._setup_agent()
    
    def _setup_agent(self):
        """设置Agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", DIALOGUE_EXTRACTOR_AGENT_SYSTEM),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        agent = create_react_agent(self.llm, self.tools, prompt)
        self.executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def extract(self, story_content: str, characters: str, scenes: str) -> List[Dict]:
        """提取对话"""
        result = self.executor.invoke({
            "input": f"Extract all dialogues from this story:\n\n{story_content}\n\nCharacters: {characters}\nScenes: {scenes}"
        })
        # 解析结果
        dialogues = json.loads(result.get('output', '{}')).get('dialogues', [])
        return dialogues


class ContentClassifierAgent:
    """内容分类Agent"""
    
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self._setup_agent()
    
    def _setup_agent(self):
        """设置Agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", CONTENT_CLASSIFIER_AGENT_SYSTEM),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        agent = create_react_agent(self.llm, self.tools, prompt)
        self.executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def classify(self, raw_dialogues: List[Dict], story_content: str) -> List[Dict]:
        """分类内容"""
        dialogues_json = json.dumps(raw_dialogues)
        result = self.executor.invoke({
            "input": f"Classify these dialogue candidates:\n\n{dialogues_json}\n\nStory context: {story_content[:500]}"
        })
        # 解析结果
        classified = json.loads(result.get('output', '{}')).get('classified_lines', [])
        return classified


class QualityValidatorAgent:
    """质量验证Agent"""
    
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self._setup_agent()
    
    def _setup_agent(self):
        """设置Agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", QUALITY_VALIDATOR_AGENT_SYSTEM),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        agent = create_react_agent(self.llm, self.tools, prompt)
        self.executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def validate(self, script_lines: List[Dict], story_content: str, scenes: List[Dict]) -> Dict:
        """验证质量"""
        script_json = json.dumps(script_lines)
        scenes_json = json.dumps(scenes)
        
        result = self.executor.invoke({
            "input": f"Validate this script:\n\nScript: {script_json}\n\nStory: {story_content[:500]}\n\nScenes: {scenes_json}"
        })
        
        # 解析验证报告
        report = json.loads(result.get('output', '{}'))
        return report


class ErrorFixerAgent:
    """错误修正Agent"""
    
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self._setup_agent()
    
    def _setup_agent(self):
        """设置Agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", ERROR_FIXER_AGENT_SYSTEM),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        agent = create_react_agent(self.llm, self.tools, prompt)
        self.executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def fix(self, script_lines: List[Dict], validation_report: Dict) -> List[Dict]:
        """修正错误"""
        script_json = json.dumps(script_lines)
        report_json = json.dumps(validation_report)
        
        result = self.executor.invoke({
            "input": f"Fix these issues:\n\nIssues: {report_json}\n\nScript: {script_json}"
        })
        
        # 解析修正后的结果
        fixed = json.loads(result.get('output', '{}')).get('fixed_lines', script_lines)
        return fixed


# ============================================================================
# Orchestrator实现
# ============================================================================

class ScriptGenerationOrchestrator:
    """多Agent剧本生成协调器"""
    
    def __init__(self, llm):
        self.llm = llm
        self._setup_tools()
        self._setup_agents()
    
    def _setup_tools(self):
        """设置所有工具"""
        self.extraction_tools = [
            extract_dialogues_tool,
        ]
        
        self.classification_tools = [
            classify_content_tool,
            detect_narration_tool,
        ]
        
        self.validation_tools = [
            validate_completeness_tool,
            check_context_tool,
            detect_duplicates_tool,
        ]
        
        self.fixing_tools = [
            fix_classification_tool,
            remove_duplicates_tool,
        ]
    
    def _setup_agents(self):
        """初始化各个Agent"""
        self.dialogue_extractor = DialogueExtractorAgent(
            self.llm, 
            self.extraction_tools
        )
        
        self.classifier = ContentClassifierAgent(
            self.llm,
            self.classification_tools
        )
        
        self.validator = QualityValidatorAgent(
            self.llm,
            self.validation_tools
        )
        
        self.fixer = ErrorFixerAgent(
            self.llm,
            self.fixing_tools
        )
    
    def generate_script(
        self, 
        story_content: str,
        scene_details=None,
        story_summary=None
    ):
        """生成剧本（主流程）"""
        logger.info("<cyan>Starting multi-agent script generation</cyan>")
        
        # 准备输入
        if scene_details and story_summary:
            scenes_text = "\n\n".join([
                f"=== {scene.scene_id} ===\n{scene.detailed_content}"
                for scene in scene_details.scenes
            ])
            full_content = f"""Story Summary:
{story_summary['summary']}

Characters:
{story_summary['characters']}

Detailed Scene Contents:
{scenes_text}"""
        else:
            full_content = story_content
        
        characters = story_summary.get('characters', '') if story_summary else ''
        scenes = scenes_text if scene_details else ''
        
        # 步骤1: 提取对话
        logger.info("Step 1: Extracting dialogues...")
        raw_dialogues = self.dialogue_extractor.extract(
            full_content, 
            characters, 
            scenes
        )
        logger.info(f"Extracted {len(raw_dialogues)} dialogue candidates")
        
        # 步骤2: 分类内容
        logger.info("Step 2: Classifying content...")
        classified_lines = self.classifier.classify(raw_dialogues, full_content)
        logger.info(f"Classified {len(classified_lines)} script lines")
        
        # 步骤3-5: 验证和修正循环
        script_lines = classified_lines
        max_iterations = 3
        scenes_list = scene_details.scenes if scene_details else []
        
        for iteration in range(max_iterations):
            logger.info(f"Iteration {iteration + 1}/{max_iterations}: Validating...")
            
            # 验证
            validation_report = self.validator.validate(
                script_lines,
                full_content,
                scenes_list
            )
            
            # 检查质量
            quality_score = validation_report.get('quality_score', 0)
            issues = validation_report.get('issues', [])
            
            logger.info(f"Quality score: {quality_score:.2f}, Issues: {len(issues)}")
            
            if quality_score >= 0.9 and len(issues) == 0:
                logger.info("Quality acceptable, proceeding...")
                break
            
            # 修正
            if issues:
                logger.info(f"Fixing {len(issues)} issues...")
                script_lines = self.fixer.fix(script_lines, validation_report)
                logger.info("Issues fixed")
            else:
                break
        
        # 返回结果（需要转换为VideoScript格式）
        return {
            "script_lines": script_lines,
            "validation_report": validation_report
        }
    
    def _is_quality_acceptable(self, validation_report: Dict) -> bool:
        """检查质量是否可接受"""
        quality_score = validation_report.get('quality_score', 0)
        issues = validation_report.get('issues', [])
        return quality_score >= 0.9 and len(issues) == 0


# ============================================================================
# 使用示例
# ============================================================================

def example_usage():
    """使用示例"""
    from langchain_openai import ChatOpenAI
    
    # 初始化LLM
    llm = ChatOpenAI(
        base_url=os.getenv("VLLM_API_URL", "http://localhost:8000/v1"),
        api_key=os.getenv("VLLM_API_KEY", "sk-placeholder"),
        model=os.getenv("VLLM_MODEL", "default"),
        temperature=0.7
    )
    
    # 创建Orchestrator
    orchestrator = ScriptGenerationOrchestrator(llm)
    
    # 生成剧本
    story_content = "..."  # 故事内容
    result = orchestrator.generate_script(
        story_content=story_content,
        scene_details=None,
        story_summary=None
    )
    
    print(f"Generated {len(result['script_lines'])} script lines")
    print(f"Quality score: {result['validation_report'].get('quality_score', 0)}")


if __name__ == "__main__":
    example_usage()

