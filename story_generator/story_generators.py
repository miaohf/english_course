"""
故事生成模块

包含故事框架、详细故事、开场白、结束语、总结的生成方法
"""

from langchain_core.prompts import ChatPromptTemplate

from .internal_schemas import (
    TranslatedTopic,
    GeneratedStoryFramework,
    GeneratedDetailedStory,
    GeneratedOpening,
    GeneratedClosing,
    GeneratedSummary
)
from logger_config import get_logger

logger = get_logger()


class StoryGenerators:
    """故事生成器 - 包含所有故事生成相关方法"""
    
    def __init__(self, llm):
        """
        初始化故事生成器
        
        Args:
            llm: LangChain LLM 实例
        """
        self.llm = llm
    
    def translate_topic(self, chinese_topic: str) -> str:
        """
        将中文主题翻译成英文（使用结构化输出确保结果简洁）
        
        Args:
            chinese_topic: 中文主题
            
        Returns:
            英文主题（简洁版本）
        """
        logger.info(f"Translating topic from Chinese: {chinese_topic}")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a professional translator. Translate the given Chinese topic to natural English. The translation should be concise (less than 50 characters)."),
            ("user", "Translate this Chinese topic to English: {topic}")
        ])
        
        # 使用结构化输出确保返回简洁的翻译结果
        structured_llm = self.llm.with_structured_output(TranslatedTopic)
        chain = prompt | structured_llm
        
        result = chain.invoke({"topic": chinese_topic})
        english_topic = result.english_topic.strip().strip('"').strip("'")
        
        logger.info(f"Topic translated to English: {english_topic}")
        return english_topic
    
    def generate_story_framework(self, topic: str, english_topic: str = None) -> str:
        """
        生成故事框架（英文）
        
        Args:
            topic: 原始主题（可能是中文）
            english_topic: 英文主题（如果已翻译）
            
        Returns:
            故事框架文本
        """
        # 如果没有提供英文主题，先翻译
        if not english_topic:
            english_topic = self.translate_topic(topic)
        
        logger.info(f"Generating story framework for topic: {english_topic}")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a creative writer creating realistic, everyday life scenarios.
Generate a story framework for a real-life scenario story.

IMPORTANT: This is a REAL-LIFE SCENARIO, NOT an English learning lesson. The story should depict normal, everyday situations where people have natural conversations. Do NOT include any references to learning English, practicing English, or educational contexts.

The story should be:
- Engaging and realistic
- Depicting everyday life situations
- With natural conversations between characters
- Suitable for video production

CRITICAL: For key_expressions, you MUST select the MOST CLASSIC, POPULAR, and COMMONLY USED English expressions that native speakers actually use in daily life. These expressions should be:
- High-frequency phrases that appear in real conversations for the given scenario
- Practical expressions that learners will encounter most often in similar situations
- Natural, idiomatic expressions (not overly formal or academic)
- Expressions that are versatile and useful in multiple contexts
- Contextually appropriate for the specific scenario/topic (e.g., restaurant scenarios need ordering expressions, airport scenarios need travel-related expressions)
- The expressions should match the scenario naturally - select the most relevant classic phrases for THIS specific topic

Avoid:
- Overly specific or context-limited expressions that only work in one situation
- Rare or outdated phrases
- Expressions that are too formal for casual conversations
- Made-up or non-standard phrases
- Generic expressions that don't fit the scenario context"""),
            ("user", "Create a story framework for a real-life scenario about: {topic}")
        ])
        
        # 使用结构化输出
        structured_llm = self.llm.with_structured_output(GeneratedStoryFramework)
        chain = prompt | structured_llm
        
        result = chain.invoke({"topic": english_topic})
        framework = result.to_text()
        
        logger.info("Story framework generation completed")
        return framework
    
    def refine_story(self, framework: str) -> str:
        """
        细化故事情节（英文）
        
        Args:
            framework: 故事框架
            
        Returns:
            细化后的完整故事
        """
        logger.info("Refining story with detailed dialogues")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a creative writer creating a realistic, everyday life scenario story.
Expand the given story framework into a complete, detailed story.

IMPORTANT: This is a REAL-LIFE SCENARIO story, NOT an English learning lesson. The characters are having normal, everyday conversations in their natural context. Do NOT include any references to:
- "learning English" or "practicing English"
- "English lesson" or "English class"
- "I'm trying to improve my English"
- Any educational or learning context

Requirements:
1. Write entirely in English
2. Include rich, natural dialogues between characters as they would speak in real life
3. Use practical, everyday English expressions that people actually use
4. Include detailed scene descriptions suitable for video production
5. Target length: 2500-3500 words (make it engaging, detailed, and well-developed)
6. Make dialogues feel authentic and natural, like real conversations
7. Develop the story with MULTIPLE scenes (at least 4-5 distinct scenes) showing different moments and interactions
8. Expand the plot naturally - include:
   - Initial encounter/setting the scene
   - Character introductions and getting to know each other
   - Multiple conversation topics and exchanges
   - Natural progression of the relationship/interaction
   - Meaningful moments and connections
   - Resolution or conclusion
9. Include detailed descriptions of:
   - Physical surroundings and atmosphere
   - Character actions, gestures, and body language
   - Emotional nuances and reactions
   - Environmental details that enhance the scene
10. Make conversations flow naturally with:
    - Multiple back-and-forth exchanges
    - Topic shifts and natural transitions
    - Personal stories and anecdotes
    - Questions and responses that build rapport
11. The story should feel like a complete, engaging slice of everyday life, not a lesson"""),
            ("user", "Expand this story framework into a complete, realistic everyday life story. Remember: This is a normal life scenario, not an English learning context:\n\n{framework}")
        ])
        
        # 使用结构化输出
        structured_llm = self.llm.with_structured_output(GeneratedDetailedStory)
        chain = prompt | structured_llm
        
        result = chain.invoke({"framework": framework})
        detailed_story = result.story
        
        logger.info("<green>Story refinement completed</green>")
        return detailed_story
    
    def generate_opening(self, topic: str, story_summary: str) -> str:
        """
        生成视频开场白（英文）
        
        Args:
            topic: 场景主题
            story_summary: 故事概要
            
        Returns:
            开场白文本
        """
        logger.info("<cyan>Generating video opening script</cyan>")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly English teacher creating a video introduction.
Generate an engaging opening script in simple, clear English.
Requirements:
1. Greet viewers warmly
2. Introduce the topic clearly
3. Preview what learners will learn
4. Keep it concise (50-100 words)
5. Use simple vocabulary suitable for English learners"""),
            ("user", "Create an opening script for a lesson about: {topic}\n\nStory preview: {summary}")
        ])
        
        # 使用结构化输出
        structured_llm = self.llm.with_structured_output(GeneratedOpening)
        chain = prompt | structured_llm
        
        result = chain.invoke({
            "topic": topic,
            "summary": story_summary[:300]
        })
        opening = result.opening_script
        
        logger.info("<green>Video opening generation completed</green>")
        return opening
    
    def generate_closing(self, topic: str, story_summary: str) -> str:
        """
        生成视频结束语（英文）
        
        Args:
            topic: 场景主题
            story_summary: 故事概要
            
        Returns:
            结束语文本
        """
        logger.info("<cyan>Generating video closing script</cyan>")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly English teacher wrapping up a video lesson.
Generate an encouraging closing script in simple, clear English.
Requirements:
1. Summarize key learning points
2. Encourage practice and application
3. End with a positive, motivating message
4. Keep it concise (50-100 words)
5. Use simple vocabulary suitable for English learners"""),
            ("user", "Create a closing script for a lesson about: {topic}\n\nLesson content: {summary}")
        ])
        
        # 使用结构化输出
        structured_llm = self.llm.with_structured_output(GeneratedClosing)
        chain = prompt | structured_llm
        
        result = chain.invoke({
            "topic": topic,
            "summary": story_summary[:300]
        })
        closing = result.closing_script
        
        logger.info("<green>Video closing generation completed</green>")
        return closing
    
    def generate_summary(self, topic: str, story: str) -> str:
        """
        生成课程总结（英文）
        
        Args:
            topic: 场景主题
            story: 完整故事
            
        Returns:
            课程总结文本
        """
        logger.info("<cyan>Generating lesson summary</cyan>")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an English teaching expert creating a lesson summary.
Generate a comprehensive summary in English that includes:
1. Key English expressions from the story
2. Important grammar points demonstrated
3. Useful vocabulary highlighted
4. Practical study tips for learners
Keep the summary focused and helpful (150-200 words)."""),
            ("user", "Create a lesson summary for this story about {topic}:\n\n{story}")
        ])
        
        # 使用结构化输出
        structured_llm = self.llm.with_structured_output(GeneratedSummary)
        chain = prompt | structured_llm
        
        result = chain.invoke({
            "topic": topic,
            "story": story
        })
        summary = result.summary
        
        logger.info("<green>Lesson summary generation completed</green>")
        return summary

