# TTS 生成阶段优化分析

## 当前流程分析

### 现有流程（3步）

```
详细故事 (story.md)
    ↓
步骤1: 提取角色和场景
    ↓
步骤2: 提取对话、转场、场景标记 → 生成 VideoScript 对象
    ↓ (转换)
步骤3: to_tts_format() → 生成 tts.txt
```

### 数据结构

**VideoScript 对象：**
```python
{
    characters: [Character(name="Mia"), Character(name="David")],
    scenes: [Scene(scene_id="scene_1"), ...],
    script_lines: [
        ScriptLine(
            line_type="dialogue",
            speaker="Mia",
            speaker_id="Mia",  # 角色名称
            content="...",
            scene_id="scene_1"
        ),
        ...
    ]
}
```

**转换过程 (to_tts_format)：**
```python
# 建立映射：Mia → SPEAKER0, David → SPEAKER1
# 遍历 script_lines，将角色名称替换为 SPEAKER ID
# 添加场景切换标记 [SILENCE]
# 格式化输出
```

---

## 问题根源分析

### 主要问题：对话提取阶段丢失内容

**问题位置：** 步骤2（提取对话）
- Prompt 可能不够强调"提取所有对话"
- 模型可能合并或简化对话
- 缺少完整性验证

**转换阶段（步骤3）：**
- 转换逻辑简单，是机械映射
- **不会丢失信息**（如果输入完整，输出就完整）
- 不是瓶颈

### 结论

**TTS 格式转换不是问题根源**，问题在于**对话提取不完整**。

---

## 方案对比

### 方案A：在提取阶段直接生成 TTS 格式

**实现方式：**
- 修改 `GENERATE_DIALOGUES_SYSTEM`，要求直接输出 `SPEAKER0`, `SPEAKER1` 格式
- 修改 `GeneratedDialogues` schema，`speaker_id` 直接使用 `SPEAKER0/1/2`
- 跳过 `to_tts_format()` 转换

**优点：**
- ✅ 减少一步转换
- ✅ 一步到位

**缺点：**
- ❌ **不能解决内容丢失问题**（问题在提取，不在转换）
- ❌ 失去灵活性（VideoScript 对象需要同时支持两种格式）
- ❌ 如果以后需要其他格式（如 JSON、XML），需要重新设计
- ❌ 转换逻辑很简单（~50行代码），不是性能瓶颈
- ❌ 角色顺序需要在提取时确定，可能不够灵活

**评估：** ⚠️ **不推荐** - 治标不治本，且降低灵活性

---

### 方案B：改进对话提取，确保完整性（推荐）

**实现方式：**
1. **改进 Prompt：**
   - 强调提取**所有**对话，包括单音节反应词
   - 明确要求保留思考过程、内心独白
   - 要求区分背景对话（电话、广播等）

2. **添加验证机制：**
   - 检查每个场景的对话数量
   - 验证对话的完整性和逻辑性
   - 对比原始故事，确保没有遗漏

3. **保持现有转换流程：**
   - 继续使用 `to_tts_format()` 转换
   - 转换逻辑简单可靠

**优点：**
- ✅ **解决根本问题**（确保提取完整）
- ✅ 保持架构清晰（职责分离）
- ✅ 保持灵活性（VideoScript 可用于多种用途）
- ✅ 转换逻辑简单，维护成本低

**缺点：**
- ⚠️ 需要改进 Prompt 和验证逻辑
- ⚠️ 可能需要多次迭代优化

**评估：** ✅ **强烈推荐** - 解决根本问题

---

### 方案C：提取时同时生成两种格式

**实现方式：**
- 修改 `GeneratedDialogues`，同时包含：
  - `script_lines`: 标准格式（角色名称）
  - `tts_lines`: TTS 格式（SPEAKER0/1/2）

**优点：**
- ✅ 保留灵活性
- ✅ 一步生成两种格式

**缺点：**
- ❌ 增加数据结构复杂度
- ❌ 仍然不能解决内容丢失问题
- ❌ 需要维护两套数据，容易不一致

**评估：** ⚠️ **不推荐** - 增加复杂度，收益有限

---

### 方案D：在细化场景阶段直接生成 TTS 格式

**实现方式：**
- 在生成详细场景内容时，同时生成 TTS 格式的对话
- 跳过对话提取步骤

**优点：**
- ✅ 减少步骤
- ✅ 直接从源内容生成，可能更完整

**缺点：**
- ❌ 场景详细内容（story.md）是叙述性文本，不是对话格式
- ❌ 需要从叙述文本中提取对话，难度更大
- ❌ 破坏职责分离（场景生成 vs 剧本生成）

**评估：** ❌ **不推荐** - 架构不合理

---

## 推荐方案：方案B（改进对话提取）

### 实施步骤

#### 1. 改进对话提取 Prompt

**修改 `GENERATE_DIALOGUES_SYSTEM`：**

```python
GENERATE_DIALOGUES_SYSTEM = """You are a video production script expert. Extract dialogues, transitions, and scene markers from the given story.

CRITICAL REQUIREMENTS:
1. This is a REAL-LIFE scenario, NOT an English learning lesson. Characters have normal everyday conversations.

2. Extract **ALL** dialogues - DO NOT MISS ANY:
   - Extract EVERY spoken word, including:
     * Single-syllable reactions: "Oh", "Yeah", "Hmm", "Uh-huh"
     * Incomplete thoughts: "I'm...", "Make it...", "Well..."
     * Interjections and filler words
     * Background dialogue (phone calls, announcements, etc.)
   - line_type: "dialogue" for character speech
   - speaker: character's real name (e.g., Mia, David)
   - speaker_id: same as speaker name
   - content: the EXACT dialogue text - PRESERVE word-for-word from the story
   - scene_id: which scene this belongs to
   - DO NOT merge or simplify dialogues
   - DO NOT skip short responses or reactions

3. Preserve dialogue context:
   - Include thinking processes: "Make it...", "I'm supposed to..."
   - Include emotional reactions: "Oh," (surprise), "Yeah. Guess so." (agreement)
   - Include interruptions and pauses
   - Mark background dialogue separately (e.g., phone voice, announcement)

4. Add scene transitions:
   - line_type: "transition"
   - speaker_id: "NARRATOR"
   - content: natural transition text

5. Mark scene starts:
   - line_type: "scene_marker"
   - content: brief scene description

6. Preserve chronological order
7. Distribute dialogues across ALL scenes

Output format:
- script_lines: Array of script lines in chronological order
- MUST include ALL dialogues from the story - completeness is critical"""
```

#### 2. 添加对话完整性验证

**在 `video_script_generator.py` 中添加验证函数：**

```python
def _validate_dialogue_completeness(self, script_lines, story_content):
    """验证对话提取的完整性"""
    # 统计每个场景的对话数量
    scene_dialogue_count = {}
    for line in script_lines:
        if line.get('line_type') == 'dialogue':
            scene_id = line.get('scene_id', 'unknown')
            scene_dialogue_count[scene_id] = scene_dialogue_count.get(scene_id, 0) + 1
    
    # 检查是否有场景缺少对话
    # 检查是否有单音节反应词
    # 检查对话逻辑完整性
    
    logger.info(f"Dialogue validation: {scene_dialogue_count}")
    return True
```

#### 3. 保持现有转换流程

- 继续使用 `to_tts_format()` 方法
- 转换逻辑简单可靠，不需要修改

---

## 结论

### 核心观点

1. **TTS 格式转换不是问题** - 转换逻辑简单，不会丢失信息
2. **问题在于对话提取不完整** - 需要在提取阶段解决
3. **不应该在生成阶段直接生成 TTS 格式** - 这会降低灵活性，且不能解决根本问题

### 推荐行动

1. ✅ **改进对话提取 Prompt** - 强调提取所有对话，包括短反应词
2. ✅ **添加完整性验证** - 确保没有遗漏
3. ✅ **保持现有转换流程** - `to_tts_format()` 方法简单可靠

### 预期效果

- 对话提取更完整
- TTS 输出包含所有对话
- 保持架构清晰和灵活性

