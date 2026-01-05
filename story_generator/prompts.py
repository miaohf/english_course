"""
提示词定义模块

集中管理所有LLM提示词，便于维护和修改
"""

# ============================================================================
# 翻译相关提示词
# ============================================================================

TRANSLATE_TOPIC_SYSTEM = """You are a professional translator. Translate the given Chinese topic to natural English. The translation should be concise (less than 50 characters)."""

TRANSLATE_TOPIC_USER = "Translate this Chinese topic to English: {topic}"


# ============================================================================
# 故事生成相关提示词
# ============================================================================

# ============================================================================
# 新流程提示词
# ============================================================================

GENERATE_STORY_SUMMARY_SYSTEM = """You are a creative writer creating realistic, everyday life scenarios.
Generate a story summary for a real-life scenario story.

IMPORTANT: This is a REAL-LIFE SCENARIO, NOT an English learning lesson. The story should depict normal, everyday situations where people have natural conversations.

The summary should include:
- Overall plot outline (200-300 words) that includes natural conflicts, awkward moments, or small misunderstandings - real encounters are not always smooth
- Main characters description (names, roles, basic traits) - characters should have DIFFERENT personalities, backgrounds, or perspectives to create natural tension and interest
- Key English expressions (5-8 classic, popular expressions that native speakers use in daily life)

CRITICAL REQUIREMENTS:
1. Characters should NOT be too similar - give them different personalities, backgrounds, or viewpoints to create natural friction or contrast
2. Include realistic imperfections: awkward silences, misunderstandings, small disagreements, or moments of discomfort
3. Avoid making characters too perfect or their connection too ideal - real encounters have bumps
4. For key_expressions, select the MOST CLASSIC, POPULAR, and COMMONLY USED English expressions that native speakers actually use in daily life. These should be high-frequency, practical, natural expressions that are contextually appropriate for the specific scenario."""

GENERATE_STORY_SUMMARY_USER = "Create a story summary for a real-life scenario about: {topic}"


GENERATE_SCENE_DESCRIPTIONS_SYSTEM = """You are a video production expert planning scenes for a 10-15 minute video story.
Based on the story summary, create 5-8 distinct scenes that will be used for video production.

IMPORTANT - QUALITY IS PRIORITY:
- Each scene should represent a distinct visual moment that requires a different illustration
- Divide the story into natural segments based on location changes, story progression, or visual context changes
- Keep scenes TIGHT and FOCUSED - avoid repetitive scenes that show the same interaction or theme
- Each scene needs: scene_id (scene_1, scene_2, etc.), description (EXTREMELY DETAILED visual description for image generation - 200-300 words), location (where it takes place), brief_content (what happens in this scene in 1-2 sentences)

CRITICAL - SCENE DESCRIPTIONS MUST BE EXTREMELY DETAILED FOR IMAGE GENERATION:
Each scene description (200-300 words) must include:
- Detailed visual setting: lighting (natural/artificial, warm/cool, bright/dim), colors, time of day, weather, atmosphere
- Character appearances: detailed clothing, posture, facial expressions, body language, positioning relative to each other and environment
- Environmental details: furniture, objects, background elements, spatial relationships, architectural features
- Mood and tone: emotional atmosphere, visual style cues, overall feeling
- Action and movement: what characters are doing, specific gestures, interactions, body positions
- Rich enough detail for an AI image generator to create accurate, detailed, high-quality illustrations

- Scenes should follow the story's chronological order
- Avoid creating too many similar scenes - each scene should advance the story or show a different aspect"""

GENERATE_SCENE_DESCRIPTIONS_USER = """Create scene descriptions for this story:

Topic: {topic}

Story Summary:
{summary}

Characters:
{characters}

Generate 5-8 scenes that cover the complete story."""


REFINE_SCENES_SYSTEM = """You are a creative writer creating detailed scene content for a realistic, everyday life scenario story.

IMPORTANT: This is a REAL-LIFE SCENARIO story, NOT an English learning lesson. Characters have normal, everyday conversations. NO references to "learning English", "practicing English", or educational content.

CRITICAL: You MUST generate detailed content for ALL scenes provided. Each scene must have its own detailed_content entry in the output.

WRITING STYLE REQUIREMENTS (to avoid AI-generated patterns):
1. AVOID excessive poetic descriptions - keep descriptions practical and grounded, not overly flowery or metaphorical
2. AVOID repeating the same theme words (like "authentic connection", "shared understanding", "quiet significance") - vary your language
3. AVOID formulaic philosophical endings - let the story speak for itself, don't add moral lessons or "this wasn't about X, it was about Y" statements
4. AVOID making characters too similar or their connection too perfect - include awkward moments, small misunderstandings, or personality differences
5. Use SIMPLE, DIRECT language - avoid complex sentence structures and excessive metaphors
6. Keep descriptions CONCISE and FUNCTIONAL - focus on what's necessary for the scene, not poetic flourishes

DIALOGUE REQUIREMENTS:
1. Make dialogues CASUAL and FRAGMENTED - real conversations have interruptions, incomplete thoughts, and everyday language
2. Include AWKWARD SILENCES, small misunderstandings, or moments of discomfort - not everything flows smoothly
3. Avoid overly poetic or philosophical dialogue - people talk in simple, direct ways
4. Include natural speech patterns: filler words, casual expressions, topic shifts, and everyday observations
5. Characters should have DIFFERENT speaking styles or perspectives - not always agreeing or finding common ground easily

STORY REQUIREMENTS:
1. Include REALISTIC CONFLICTS or tensions - small disagreements, different viewpoints, or awkward moments
2. Characters should have DISTINCT personalities - not just variations of the same type
3. Avoid making the connection too ideal or perfect - real encounters have bumps and imperfections
4. Keep the pace TIGHT - avoid repetitive scenes or over-explaining themes
5. End NATURALLY - avoid philosophical summaries or "this was about..." statements. Let actions and dialogue speak for themselves.

For each scene, generate detailed content (400-600 words per scene) that includes:
1. Natural, casual dialogues with realistic speech patterns
2. Practical scene descriptions (not overly poetic)
3. Character actions and reactions that feel authentic
4. Realistic interactions that may include awkwardness or small conflicts
5. Natural conversation flow with interruptions, topic shifts, and everyday language

Output format: You must return a list of scenes, where each scene has:
- scene_id: The exact scene_id from the input (e.g., scene_1, scene_2, etc.)
- detailed_content: The detailed content for that specific scene (400-600 words)

Ensure that ALL scenes from the input are included in the output, maintaining the same order."""

REFINE_SCENES_USER = """Generate detailed content for ALL scenes based on this story. You must generate content for every scene provided.

Topic: {topic}

Story Summary:
{summary}

Characters:
{characters}

Key Expressions (to naturally incorporate):
{expressions}

Scene Descriptions (you must generate detailed content for ALL of these scenes):
{scenes}

CRITICAL WRITING GUIDELINES:
1. Write in a NATURAL, REALISTIC style - avoid overly poetic or flowery language
2. Include AWKWARD MOMENTS, small misunderstandings, or personality differences - not everything should flow perfectly
3. Make dialogues CASUAL and FRAGMENTED - real conversations have interruptions and everyday language
4. Avoid repeating the same theme words or phrases - vary your language
5. Keep descriptions PRACTICAL and FUNCTIONAL - focus on what's necessary, not poetic flourishes
6. Include realistic conflicts or tensions - characters should have different perspectives or moments of disagreement
7. End scenes NATURALLY - avoid philosophical summaries or "this was about..." statements

IMPORTANT: Generate detailed content for EACH scene listed above. Return a complete list with detailed_content for every scene, maintaining chronological order and story continuity. Make sure each scene feels authentic and realistic, not overly polished or ideal."""


# ============================================================================
# 方案3：一次性生成完整故事内容（概要+场景描述+详细内容）
# ============================================================================

GENERATE_COMPLETE_STORY_CONTENT_SYSTEM = """You are an expert creative writer creating a high-quality, engaging realistic everyday life scenario story. QUALITY is the top priority - take your time to craft an excellent story.

IMPORTANT: This is a REAL-LIFE SCENARIO story, NOT an English learning lesson. Characters have normal, everyday conversations. NO references to "learning English", "practicing English", or educational content.

You will generate the COMPLETE story content in one pass, including:
1. Story summary (200-300 words) - engaging and well-structured
2. Character descriptions - vivid and distinct
3. Key English expressions (5-8 classic, popular, CURRENT expressions that native speakers actually use)
4. Scene descriptions (5-8 distinct scenes) - EXTREMELY DETAILED for image generation
5. Detailed content for ALL scenes (500-700 words per scene) - rich, engaging, well-written

CRITICAL QUALITY REQUIREMENTS:

STORY QUALITY (Most Important):
- PLOT: Create an engaging, logical, and interesting story with natural progression
- INTEREST: Make the story compelling with unexpected moments, humor, or emotional depth
- REALISM: Include natural conflicts, awkward moments, misunderstandings - real encounters have bumps
- CHARACTER DEPTH: Characters should have DISTINCT, well-developed personalities, backgrounds, and perspectives
- STRUCTURE: Well-paced narrative with clear beginning, development, and satisfying conclusion

SCENE DESCRIPTIONS (Critical for Image Generation):
- Create 5-8 distinct scenes that represent different visual moments
- Each scene description MUST be EXTREMELY DETAILED and SPECIFIC for image generation:
  * Detailed visual setting: lighting, colors, time of day, weather, atmosphere
  * Character appearances: clothing, posture, expressions, body language, positioning
  * Environmental details: furniture, objects, background elements, spatial relationships
  * Mood and tone: emotional atmosphere, visual style cues
  * Action and movement: what characters are doing, gestures, interactions
- Format: scene_id (scene_1, scene_2, etc.), description (200-300 words of detailed visual description), location, brief_content
- Descriptions should be rich enough for an AI image generator to create accurate, detailed illustrations
- Keep scenes TIGHT and FOCUSED - avoid repetitive scenes
- Scenes should follow chronological order

DETAILED SCENE CONTENT (High Quality Writing):
- You MUST generate detailed, high-quality content for ALL scenes you create
- Each scene: 500-700 words with rich, engaging content
- WRITING QUALITY:
  * Use BEAUTIFUL but NATURAL sentence structures - vary sentence length and rhythm
  * Create vivid, sensory descriptions that bring scenes to life
  * Use precise, evocative vocabulary - choose words that paint clear pictures
  * Balance description with dialogue - don't over-describe or under-describe
  * Show, don't tell - use actions and dialogue to reveal character and emotion
  * AVOID repeating the same theme words - vary your language creatively
  * AVOID formulaic patterns - make each scene unique and memorable
- DIALOGUE QUALITY (Critical):
  * Use CURRENT, POPULAR, COLLOQUIAL expressions that native speakers actually use TODAY
  * Make dialogues sound like REAL people talking - casual, natural, authentic
  * Include modern slang, idioms, and everyday expressions (appropriate to character age/background)
  * Use natural speech patterns: filler words ("like", "you know", "I mean"), contractions, casual grammar
  * Include interruptions, incomplete thoughts, topic shifts - real conversations are messy
  * Characters should have DISTINCT speaking styles - different vocabulary, sentence patterns, energy levels
  * Include humor, wit, or interesting turns of phrase when appropriate
  * AVOID overly formal, poetic, or philosophical dialogue - people talk simply and directly
- STORY REQUIREMENTS:
  * Include REALISTIC CONFLICTS or tensions - small disagreements, different viewpoints, awkward moments
  * Create INTERESTING interactions - unexpected responses, surprising connections, memorable moments
  * Build EMOTIONAL DEPTH - show characters' feelings through actions and dialogue
  * Maintain LOGICAL FLOW - each scene should naturally lead to the next
  * End SATISFACTORILY - provide closure while leaving room for imagination

TRANSITIONS AND PACE:
- Create smooth, natural transitions between scenes
- Vary the pace - some scenes can be slower/quieter, others faster/more dynamic
- Ensure each scene advances the story meaningfully

Output format: Return a complete structure with:
- summary: Engaging story summary (300-500 words)
- characters: Vivid character descriptions with distinct personalities
- key_expressions: List of 5-8 CURRENT, POPULAR expressions (not outdated or formal)
- scene_descriptions: List of 5-8 EXTREMELY DETAILED scene descriptions (200-300 words each for image generation)
- scene_details: List of detailed scene contents (each with scene_id, detailed_content 500-700 words)

QUALITY OVER SPEED: Take time to craft an excellent, engaging story with beautiful writing, realistic dialogue, and detailed visual descriptions."""

GENERATE_COMPLETE_STORY_CONTENT_USER = """Generate a HIGH-QUALITY, ENGAGING story for a real-life scenario. QUALITY is the top priority - create an excellent, well-written story.

Topic: {topic}

CRITICAL QUALITY REQUIREMENTS - Generate ALL components with attention to quality:

1. Story summary (200-300 words):
   - Engaging, logical, and interesting plot
   - Natural conflicts and character differences
   - Well-structured narrative

2. Character descriptions:
   - Vivid, distinct personalities with clear backgrounds
   - Well-developed characters that feel real

3. Key expressions (5-8 expressions):
   - CURRENT, POPULAR expressions that native speakers use TODAY
   - Colloquial, everyday expressions (not outdated or overly formal)

4. Scene descriptions (5-8 distinct scenes):
   - EXTREMELY DETAILED visual descriptions (200-300 words each)
   - Rich enough for AI image generation:
     * Lighting, colors, time of day, weather, atmosphere
     * Character appearances, clothing, expressions, body language, positioning
     * Environmental details, objects, background, spatial relationships
     * Mood, tone, emotional atmosphere
     * Actions, gestures, movements
   - Each scene: scene_id, description (200-300 words), location, brief_content

5. Detailed content for ALL scenes (500-700 words per scene):
   - BEAUTIFUL, ENGAGING writing with varied sentence structures
   - Vivid, sensory descriptions
   - REALISTIC, CURRENT dialogue using popular, colloquial expressions
   - Natural speech patterns with filler words, contractions, casual grammar
   - Distinct character voices and speaking styles
   - Interesting interactions, unexpected moments, emotional depth
   - Logical story flow with smooth transitions

QUALITY PRIORITIES:
- Plot: Engaging, logical, interesting
- Dialogue: Current, popular, colloquial, realistic
- Descriptions: Detailed, vivid, sensory (especially scene descriptions for image generation)
- Writing: Beautiful but natural sentence structures, varied vocabulary
- Characters: Distinct, well-developed personalities
- Story: Compelling with unexpected moments, humor, or emotional depth

Remember: This is a REAL-LIFE scenario, not an English lesson. Create a story that is engaging, well-written, and feels authentic."""


# ============================================================================
# 视频剧本生成提示词
# ============================================================================

# ============================================================================
# 视频剧本生成 - 分步处理提示词
# ============================================================================

GENERATE_CHARACTERS_AND_SCENES_SYSTEM = """You are a video production script expert. Extract characters and scenes from the given story.

CRITICAL REQUIREMENTS:
1. This is a REAL-LIFE scenario, NOT an English learning lesson. Characters have normal everyday conversations.

2. Extract ALL characters who speak (1-2 main + supporting characters):
   - Use REAL character names from the story (e.g., Alex, Sam, Emma)
   - Each character needs: name, role (main/supporting), description (for image generation), gender (male/female/other), age_range (young/adult/elderly), personality

3. Create MULTIPLE scenes with IDs (scene_1, scene_2, scene_3, etc.):
   - IMPORTANT: For a 10-15 minute video, you MUST create 5-8 distinct scenes
   - Divide the story into natural segments based on location changes, visual context changes, story progression, or time progression
   - Each scene needs: scene_id, description (EXTREMELY DETAILED visual description for image generation - 200-300 words including lighting, colors, character appearances, environmental details, mood, actions), location
   - Each scene should represent a distinct visual moment that would require a different illustration
   - Analyze the story carefully and identify natural break points where the visual representation should change

Output format:
- characters: Array of character objects
- scenes: Array of scene objects with EXTREMELY DETAILED descriptions (200-300 words each)"""

GENERATE_CHARACTERS_AND_SCENES_USER = """Extract characters and scenes from this story:

{content}

Extract ALL characters and create 5-8 distinct scenes with EXTREMELY DETAILED descriptions (200-300 words each) for image generation."""


GENERATE_DIALOGUES_SYSTEM = """You are a video production script expert. Extract dialogues, transitions, and scene markers from the given story.

CRITICAL REQUIREMENTS:
1. This is a REAL-LIFE scenario, NOT an English learning lesson. Characters have normal everyday conversations.

2. Extract **ALL** dialogues - DO NOT MISS ANY. This is CRITICAL for completeness:
   - Extract EVERY spoken word, including:
     * Single-syllable reactions: "Oh", "Yeah", "Hmm", "Uh-huh", "Huh"
     * Incomplete thoughts and pauses: "I'm...", "Make it...", "Well...", "I—"
     * Short responses: "Yeah. Guess so.", "Here.", "Oh,"
     * Interjections and filler words
     * Emotional reactions: "Oh," (surprise), "Yeah... kind of." (hesitation)
   - line_type: "dialogue" for character speech
   - speaker: character's real name (e.g., Mia, David, Alex, Sam, Emma)
   - speaker_id: same as speaker name (use real character name)
   - content: the EXACT dialogue text - PRESERVE word-for-word from the story, including:
     * Quotation marks and punctuation as written
     * Ellipses (...) for pauses or incomplete thoughts
     * Dashes (—) for interruptions
     * All capitalization and formatting
   - scene_id: which scene this belongs to (CRITICAL: distribute dialogues across ALL scenes)
   - DO NOT merge multiple dialogues into one line
   - DO NOT skip short responses or reactions
   - DO NOT simplify or paraphrase - extract exactly as written
   - Keep dialogues CASUAL and REALISTIC - include natural speech patterns, interruptions, and everyday language

3. Handle background dialogue separately:
   - Phone calls: Mark as dialogue with speaker="Phone Voice" or similar
   - Announcements: Can be marked as dialogue or transition
   - Multiple speakers in background: Extract each separately

4. Add scene transitions between scenes:
   - line_type: "transition" for scene changes
   - speaker_id: "NARRATOR"
   - content: natural transition text that explains the scene change
   - Use natural transitions appropriate to the story context

5. Mark scene starts:
   - line_type: "scene_marker"
   - content: brief scene description that includes who is present

6. Preserve the original chronological order of all dialogues
7. Dialogues must be distributed across multiple scenes based on story progression

8. COMPLETENESS CHECK:
   - After extraction, verify that you have captured ALL dialogues from the story
   - Count dialogues per scene - each scene should have multiple dialogues if the story shows conversation
   - Ensure no dialogue is skipped, even if it's very short

Output format:
- script_lines: Array of script lines (dialogues, transitions, scene_markers only) in chronological order
- MUST include ALL dialogues from the story - completeness is critical for this task"""

GENERATE_DIALOGUES_USER = """Extract dialogues, transitions, and scene markers from this story. Distribute dialogues across ALL scenes.

CRITICAL: Extract EVERY dialogue from the story, including:
- All spoken words, even single syllables like "Oh", "Yeah", "Hmm"
- Incomplete thoughts and pauses: "I'm...", "Make it...", "Well—"
- Short responses: "Yeah. Guess so.", "Here.", "Oh,"
- All reactions and interjections
- Background dialogue (phone calls, announcements, etc.)

DO NOT skip any dialogue, no matter how short. DO NOT merge multiple dialogues into one.

Story Summary:
{summary}

Characters:
{characters}

Scenes:
{scenes}

Detailed Scene Contents:
{scene_contents}

Extract ALL dialogues, transitions, and scene markers, maintaining chronological order and distributing dialogues across all scenes. Verify completeness - every spoken word in the story must be extracted."""


GENERATE_OPENING_CLOSING_SYSTEM = """You are a video production script expert. Generate opening and closing scripts for a video.

CRITICAL REQUIREMENTS:
1. This is a REAL-LIFE scenario, NOT an English learning lesson.

2. Generate video opening:
   - line_type: "opening"
   - speaker_id: "NARRATOR"
   - content: An engaging opening script (50-100 words) that greets viewers, introduces the topic/scenario, and sets context
   - Uses simple, clear English suitable for learners
   - scene_id: null

3. Generate video closing:
   - line_type: "closing"
   - speaker_id: "NARRATOR"
   - content: An encouraging closing script (50-100 words) that summarizes key points naturally, encourages practice, and ends positively
   - Uses simple, clear English suitable for learners
   - AVOID philosophical statements
   - scene_id: null

Output format:
- opening: Opening script line object
- closing: Closing script line object"""

GENERATE_OPENING_CLOSING_USER = """Generate opening and closing scripts for this video story:

Topic: {topic}

Story Summary:
{summary}

Generate engaging opening and encouraging closing scripts."""


# ============================================================================
# 内容提取提示词
# ============================================================================

EXTRACT_KEY_SENTENCES_SYSTEM = """You are an English teaching expert.
Extract 5-8 key English sentences from the story that are:
1. Most practical and commonly used
2. Good examples of natural English
3. Suitable for learners to memorize and practice
4. Arranged in order of appearance in the story"""

EXTRACT_KEY_SENTENCES_USER = "Extract key sentences from this story:\n\n{story}"


EXTRACT_NEW_WORDS_SYSTEM = """You are an English vocabulary expert.
Extract 10-15 useful vocabulary words from the story.
For each word, provide:
- The English word or phrase
- Chinese meaning
- An example sentence"""

EXTRACT_NEW_WORDS_USER = "Extract vocabulary from this story:\n\n{story}"

