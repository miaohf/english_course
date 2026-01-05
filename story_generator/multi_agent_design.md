# 多Agent剧本生成架构设计

## 一、架构概览

### 1.1 整体架构

```
ScriptGenerationOrchestrator (协调器)
    │
    ├─→ CharacterSceneExtractorAgent (角色和场景提取Agent)
    │
    ├─→ DialogueExtractorAgent (对话提取Agent)
    │   └─→ 使用工具: extract_dialogues_tool
    │
    ├─→ ContentClassifierAgent (内容分类Agent)
    │   └─→ 使用工具: classify_content_tool, detect_narration_tool
    │
    ├─→ QualityValidatorAgent (质量验证Agent)
    │   └─→ 使用工具: validate_completeness_tool, check_context_tool, 
    │                detect_duplicates_tool, verify_coherence_tool
    │
    └─→ ErrorFixerAgent (错误修正Agent)
        └─→ 使用工具: fix_classification_tool, fix_positioning_tool,
                     add_context_tool, remove_duplicates_tool
```

### 1.2 工作流程

```
1. Orchestrator 接收输入（故事内容、场景详情等）
   ↓
2. 调用 CharacterSceneExtractorAgent 提取角色和场景
   ↓
3. 调用 DialogueExtractorAgent 提取所有对话片段
   ↓
4. 调用 ContentClassifierAgent 分类内容（对话/叙述/转场）
   ↓
5. 调用 QualityValidatorAgent 验证质量
   ↓
6. 如果发现问题，调用 ErrorFixerAgent 修正
   ↓
7. 重复步骤5-6直到质量达标（最多3次迭代）
   ↓
8. 生成开场和结束（使用现有方法）
   ↓
9. 组装最终结果
```

## 二、各Agent详细设计

### 2.1 CharacterSceneExtractorAgent

**职责**：提取角色和场景信息

**输入**：
- story_content: 完整故事内容

**输出**：
- characters: 角色列表
- scenes: 场景列表

**实现方式**：
- 使用现有的 `GENERATE_CHARACTERS_AND_SCENES_SYSTEM` 提示词
- 使用结构化输出 `GeneratedCharactersAndScenes`
- 可以保持现有实现，或包装为Agent

**Agent Prompt**：
```python
CHARACTER_SCENE_EXTRACTOR_AGENT_SYSTEM = """You are a video production expert specializing in character and scene extraction.

Your task is to extract ALL characters and create detailed scene descriptions from the given story.

You have access to a tool that can extract characters and scenes. Use it to analyze the story content and extract:
1. All characters who speak (with detailed descriptions for image generation)
2. 5-8 distinct scenes with EXTREMELY DETAILED visual descriptions (200-300 words each)

Use the extract_characters_and_scenes tool to complete this task."""
```

### 2.2 DialogueExtractorAgent

**职责**：从故事中提取所有对话片段（不分类）

**输入**：
- story_content: 完整故事内容
- characters: 角色列表
- scenes: 场景列表

**输出**：
- raw_dialogues: 原始对话片段列表（包含所有可能的对话，未分类）

**工具**：
- `extract_dialogues_tool`: 提取所有可能的对话片段

**Agent Prompt**：
```python
DIALOGUE_EXTRACTOR_AGENT_SYSTEM = """You are a dialogue extraction expert. Your task is to extract EVERY possible dialogue from the story.

CRITICAL: Extract ALL spoken words, including:
- Full sentences in quotation marks
- Short reactions: "Oh", "Yeah", "Hmm", "Uh-huh"
- Incomplete thoughts: "I'm...", "Well...", "I—"
- Single word responses: "Here.", "Same.", "Pretzels?"

DO NOT classify or filter - extract EVERYTHING that could be dialogue.
DO NOT merge multiple dialogues into one.

Use the extract_dialogues_tool to extract all dialogue candidates from the story."""
```

### 2.3 ContentClassifierAgent

**职责**：分类提取的内容（对话/叙述/转场/场景标记）

**输入**：
- raw_dialogues: 原始对话片段列表
- story_content: 完整故事内容（用于上下文）

**输出**：
- classified_lines: 分类后的剧本行列表

**工具**：
- `classify_content_tool`: 分类单个内容片段
- `detect_narration_tool`: 检测叙述性内容

**Agent Prompt**：
```python
CONTENT_CLASSIFIER_AGENT_SYSTEM = """You are a content classification expert. Your task is to classify extracted content into:
- dialogue: Character speech (must be spoken words)
- transition: Narrative transitions between scenes
- scene_marker: Scene markers
- narration: Descriptive narration (not dialogue)

CRITICAL DISTINCTION:
- DIALOGUE: Direct speech, spoken words, character conversations
- NARRATION: Descriptive text, internal thoughts, philosophical statements
  Examples of NARRATION (NOT dialogue):
  * "No big words. No grand gesture. Just two people sharing snacks..."
  * "Sometimes, the best moments happen when we least expect them."
  * "They left the airport with more than just a story..."

Use the classify_content_tool to classify each extracted content piece.
Use the detect_narration_tool to identify narration that might be misclassified as dialogue."""
```

### 2.4 QualityValidatorAgent

**职责**：验证提取结果的质量和完整性

**输入**：
- script_lines: 分类后的剧本行列表
- story_content: 原始故事内容
- scenes: 场景列表

**输出**：
- validation_report: 验证报告（包含问题列表）

**工具**：
- `validate_completeness_tool`: 验证完整性
- `check_context_tool`: 检查上下文
- `detect_duplicates_tool`: 检测重复
- `verify_coherence_tool`: 验证连贯性

**Agent Prompt**：
```python
QUALITY_VALIDATOR_AGENT_SYSTEM = """You are a quality validation expert. Your task is to validate the extracted script for:
1. Completeness: All dialogues extracted, no missing content
2. Classification accuracy: Dialogues correctly classified, narration not marked as dialogue
3. Context completeness: All pronouns have clear references
4. No duplicates: No unintentional duplicate dialogues
5. Scene coherence: Dialogues properly distributed across scenes

Use the available validation tools to check each aspect.
Generate a detailed validation report with:
- Overall quality score (0-1)
- List of issues found
- Recommendations for fixes"""
```

### 2.5 ErrorFixerAgent

**职责**：根据验证报告修正错误

**输入**：
- script_lines: 需要修正的剧本行列表
- validation_report: 验证报告

**输出**：
- fixed_script_lines: 修正后的剧本行列表

**工具**：
- `fix_classification_tool`: 修正分类错误
- `fix_positioning_tool`: 修正位置错误
- `add_context_tool`: 添加上下文
- `remove_duplicates_tool`: 移除重复

**Agent Prompt**：
```python
ERROR_FIXER_AGENT_SYSTEM = """You are an error fixing expert. Your task is to fix issues found in the script validation.

You can fix:
1. Classification errors: Change narration marked as dialogue to transition/narration
2. Positioning errors: Move dialogues to correct scenes
3. Context issues: Add missing context or clarify references
4. Duplicates: Remove unintentional duplicate dialogues

Use the appropriate fixing tools to address each issue in the validation report.
After fixing, verify that the fixes are correct."""
```

## 三、工具函数设计

### 3.1 提取工具

```python
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate

@tool
def extract_dialogues_tool(story_content: str, characters: str, scenes: str) -> str:
    """Extract all possible dialogue candidates from the story.
    
    Args:
        story_content: Complete story content
        characters: Character descriptions
        scenes: Scene descriptions
        
    Returns:
        JSON string containing list of dialogue candidates with:
        - content: The dialogue text
        - speaker_candidate: Possible speaker name
        - location_hint: Where it appears in the story
    """
    # 使用LLM提取所有可能的对话
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract ALL possible dialogue candidates from the story. Include everything that could be spoken."),
        ("user", "Story: {story}\nCharacters: {characters}\nScenes: {scenes}")
    ])
    # ... 实现提取逻辑
    pass

@tool
def extract_characters_and_scenes_tool(story_content: str) -> str:
    """Extract characters and scenes from the story.
    
    Returns:
        JSON string with characters and scenes
    """
    # 使用现有的提取逻辑
    pass
```

### 3.2 分类工具

```python
@tool
def classify_content_tool(content: str, context: str, story_content: str) -> str:
    """Classify a content piece as dialogue, transition, scene_marker, or narration.
    
    Args:
        content: The content to classify
        context: Surrounding context
        story_content: Full story for reference
        
    Returns:
        JSON with: line_type, speaker (if dialogue), confidence
    """
    # 使用LLM分类
    pass

@tool
def detect_narration_tool(content: str) -> str:
    """Detect if content is narration (not dialogue).
    
    Returns:
        JSON with: is_narration (bool), reason, suggested_type
    """
    # 检测叙述性内容
    narration_patterns = [
        r"no big words",
        r"just two people",
        r"sometimes.*happen",
        r"keep your.*open"
    ]
    # ... 实现检测逻辑
    pass
```

### 3.3 验证工具

```python
@tool
def validate_completeness_tool(script_lines: list, story_content: str) -> str:
    """Validate that all dialogues are extracted.
    
    Returns:
        JSON with: is_complete (bool), missing_count, issues
    """
    # 检查完整性
    quote_count = story_content.count("'") + story_content.count('"')
    dialogue_count = len([l for l in script_lines if l.get('line_type') == 'dialogue'])
    # ... 实现验证逻辑
    pass

@tool
def check_context_tool(script_lines: list) -> str:
    """Check context completeness for dialogues.
    
    Returns:
        JSON with: issues (list of context problems)
    """
    # 检查上下文
    pronouns = ["this", "that", "here", "it", "they"]
    issues = []
    for i, line in enumerate(script_lines):
        if line.get('line_type') == 'dialogue':
            content = line.get('content', '').lower()
            for pronoun in pronouns:
                if pronoun in content.split() and i == 0:
                    issues.append(f"Possible context missing for '{pronoun}' in: {line.get('content', '')[:50]}")
    return json.dumps({"issues": issues})

@tool
def detect_duplicates_tool(script_lines: list) -> str:
    """Detect duplicate dialogues.
    
    Returns:
        JSON with: duplicates (list of duplicate pairs)
    """
    # 检测重复
    seen = {}
    duplicates = []
    for i, line in enumerate(script_lines):
        if line.get('line_type') == 'dialogue':
            content = line.get('content', '')
            if content in seen:
                duplicates.append({
                    "first_index": seen[content],
                    "second_index": i,
                    "content": content[:50]
                })
            seen[content] = i
    return json.dumps({"duplicates": duplicates})

@tool
def verify_coherence_tool(script_lines: list, scenes: list) -> str:
    """Verify scene coherence.
    
    Returns:
        JSON with: scene_issues (dict of scene_id -> issues)
    """
    # 验证场景连贯性
    scene_dialogues = {}
    for line in script_lines:
        if line.get('line_type') == 'dialogue':
            scene_id = line.get('scene_id')
            if scene_id:
                if scene_id not in scene_dialogues:
                    scene_dialogues[scene_id] = []
                scene_dialogues[scene_id].append(line)
    
    issues = {}
    for scene_id, dialogues in scene_dialogues.items():
        if len(dialogues) < 2:
            issues[scene_id] = f"Too few dialogues: {len(dialogues)}"
        speakers = [d.get('speaker_id') for d in dialogues]
        if len(set(speakers)) == 1:
            issues[scene_id] = "Only one speaker in scene"
    
    return json.dumps({"scene_issues": issues})
```

### 3.4 修正工具

```python
@tool
def fix_classification_tool(script_lines: list, issues: list) -> str:
    """Fix classification errors.
    
    Args:
        script_lines: Script lines to fix
        issues: List of classification issues from validator
        
    Returns:
        JSON with fixed script_lines
    """
    # 修正分类错误
    fixed = []
    for line in script_lines:
        content_lower = line.get('content', '').lower()
        # 检查是否是叙述性内容
        if any(keyword in content_lower for keyword in ["no big words", "just two people", "sometimes"]):
            if line.get('line_type') == 'dialogue':
                line['line_type'] = 'transition'
                line['speaker_id'] = 'NARRATOR'
                line['speaker'] = None
        fixed.append(line)
    return json.dumps({"fixed_lines": fixed})

@tool
def fix_positioning_tool(script_lines: list, issues: list) -> str:
    """Fix dialogue positioning errors.
    
    Returns:
        JSON with repositioned script_lines
    """
    # 修正位置错误
    # 例如："No worries at all" 应该在 Scene 1
    pass

@tool
def add_context_tool(script_lines: list, issues: list) -> str:
    """Add missing context to dialogues.
    
    Returns:
        JSON with context-added script_lines
    """
    # 添加上下文
    pass

@tool
def remove_duplicates_tool(script_lines: list, duplicates: list) -> str:
    """Remove duplicate dialogues.
    
    Returns:
        JSON with duplicates removed
    """
    # 移除重复
    indices_to_remove = {d['second_index'] for d in duplicates}
    filtered = [line for i, line in enumerate(script_lines) if i not in indices_to_remove]
    return json.dumps({"filtered_lines": filtered})
```

## 四、Orchestrator实现

### 4.1 基本结构

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

class ScriptGenerationOrchestrator:
    """多Agent剧本生成协调器"""
    
    def __init__(self, llm):
        self.llm = llm
        self._setup_agents()
        self._setup_tools()
    
    def _setup_tools(self):
        """设置所有工具"""
        self.tools = [
            extract_dialogues_tool,
            extract_characters_and_scenes_tool,
            classify_content_tool,
            detect_narration_tool,
            validate_completeness_tool,
            check_context_tool,
            detect_duplicates_tool,
            verify_coherence_tool,
            fix_classification_tool,
            fix_positioning_tool,
            add_context_tool,
            remove_duplicates_tool,
        ]
    
    def _setup_agents(self):
        """初始化各个Agent"""
        # CharacterSceneExtractorAgent
        self.character_scene_agent = self._create_agent(
            CHARACTER_SCENE_EXTRACTOR_AGENT_SYSTEM,
            [extract_characters_and_scenes_tool]
        )
        
        # DialogueExtractorAgent
        self.dialogue_extractor_agent = self._create_agent(
            DIALOGUE_EXTRACTOR_AGENT_SYSTEM,
            [extract_dialogues_tool]
        )
        
        # ContentClassifierAgent
        self.classifier_agent = self._create_agent(
            CONTENT_CLASSIFIER_AGENT_SYSTEM,
            [classify_content_tool, detect_narration_tool]
        )
        
        # QualityValidatorAgent
        self.validator_agent = self._create_agent(
            QUALITY_VALIDATOR_AGENT_SYSTEM,
            [validate_completeness_tool, check_context_tool, 
             detect_duplicates_tool, verify_coherence_tool]
        )
        
        # ErrorFixerAgent
        self.fixer_agent = self._create_agent(
            ERROR_FIXER_AGENT_SYSTEM,
            [fix_classification_tool, fix_positioning_tool,
             add_context_tool, remove_duplicates_tool]
        )
    
    def _create_agent(self, system_prompt: str, tools: list):
        """创建ReAct Agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        agent = create_react_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    def generate_script(self, story_content, scene_details=None, story_summary=None):
        """生成剧本（主流程）"""
        # 步骤1: 提取角色和场景
        char_scene_result = self.character_scene_agent.invoke({
            "input": f"Extract characters and scenes from: {story_content}"
        })
        
        # 步骤2: 提取对话
        dialogue_result = self.dialogue_extractor_agent.invoke({
            "input": f"Extract all dialogues from: {story_content}"
        })
        
        # 步骤3: 分类内容
        classified_result = self.classifier_agent.invoke({
            "input": f"Classify these dialogue candidates: {dialogue_result}"
        })
        
        # 步骤4-6: 验证和修正循环
        script_lines = classified_result
        max_iterations = 3
        
        for iteration in range(max_iterations):
            # 验证
            validation_result = self.validator_agent.invoke({
                "input": f"Validate this script: {script_lines}"
            })
            
            # 检查质量
            if self._is_quality_acceptable(validation_result):
                break
            
            # 修正
            fixed_result = self.fixer_agent.invoke({
                "input": f"Fix these issues: {validation_result}. Script: {script_lines}"
            })
            script_lines = fixed_result
        
        # 步骤7: 生成开场和结束（使用现有方法）
        # ...
        
        # 步骤8: 组装结果
        return self._assemble_result(char_scene_result, script_lines)
    
    def _is_quality_acceptable(self, validation_result: dict) -> bool:
        """检查质量是否可接受"""
        quality_score = validation_result.get('quality_score', 0)
        return quality_score >= 0.9
```

## 五、集成到现有代码

### 5.1 修改VideoScriptGenerator

```python
class VideoScriptGenerator:
    def __init__(self, llm):
        self.llm = llm
        # 可以选择使用多Agent或现有方法
        self.use_multi_agent = os.getenv("USE_MULTI_AGENT", "false").lower() == "true"
        
        if self.use_multi_agent:
            from .multi_agent_orchestrator import ScriptGenerationOrchestrator
            self.orchestrator = ScriptGenerationOrchestrator(llm)
        else:
            # 保持现有实现
            pass
    
    def generate_video_script(self, ...):
        if self.use_multi_agent:
            return self.orchestrator.generate_script(...)
        else:
            return self._generate_video_script_stepwise(...)
```

### 5.2 文件结构

```
story_generator/
├── video_script_generator.py (修改，添加多Agent选项)
├── multi_agent_orchestrator.py (新建)
├── agents/
│   ├── __init__.py
│   ├── character_scene_extractor.py
│   ├── dialogue_extractor.py
│   ├── content_classifier.py
│   ├── quality_validator.py
│   └── error_fixer.py
├── tools/
│   ├── __init__.py
│   ├── extraction_tools.py
│   ├── classification_tools.py
│   ├── validation_tools.py
│   └── fixing_tools.py
└── prompts/
    └── agent_prompts.py (新建，包含所有Agent提示词)
```

## 六、优势总结

1. **职责清晰**：每个Agent专注于特定任务
2. **易于调试**：可以单独测试每个Agent
3. **可扩展性**：容易添加新的Agent或工具
4. **质量保证**：通过验证和修正循环确保质量
5. **灵活性**：可以并行执行某些任务
6. **可维护性**：代码结构清晰，易于维护

## 七、实施建议

### 阶段1：基础实现（1-2周）
1. 实现Orchestrator基础框架
2. 实现CharacterSceneExtractorAgent（可以复用现有代码）
3. 实现DialogueExtractorAgent
4. 实现基础工具函数

### 阶段2：分类和验证（1周）
1. 实现ContentClassifierAgent
2. 实现QualityValidatorAgent
3. 实现验证工具

### 阶段3：修正机制（1周）
1. 实现ErrorFixerAgent
2. 实现修正工具
3. 实现迭代改进机制

### 阶段4：优化和测试（1周）
1. 性能优化
2. 全面测试
3. 与现有代码集成

## 八、注意事项

1. **性能考虑**：多Agent会增加API调用次数，需要监控成本
2. **错误处理**：每个Agent都需要完善的错误处理
3. **日志记录**：详细记录每个Agent的执行过程
4. **向后兼容**：保持现有接口不变，通过配置开关选择实现方式
5. **测试策略**：为每个Agent编写单元测试

