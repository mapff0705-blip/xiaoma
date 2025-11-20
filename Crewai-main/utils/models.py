from typing import List, Optional
from pydantic import BaseModel, Field


class VlogConceptProposal(BaseModel):
    """Vlog 概念提案模型"""
    title: str = Field(..., description="吸引眼球的标题（含情绪钩子）")
    core_message: str = Field(..., description="一句话核心信息")
    audience_resonance: str = Field(..., description="目标观众共鸣点")
    expected_engagement: str = Field(..., description="预期互动效果（如引发评论/收藏）")


class StoryboardOutline(BaseModel):
    """故事板大纲模型"""
    segments: List["TimeSegment"] = Field(..., description="按时间轴划分的内容段落列表")


class TimeSegment(BaseModel):
    """时间轴段落模型"""
    time_range: str = Field(..., description="时间段，如 '0-3s' 或 '15-45s'")
    emotion_goal: str = Field(..., description="该段的情绪目标")
    key_info: str = Field(..., description="需传达的关键信息")
    visual_hint: str = Field(..., description="视觉提示或画面建议")
    transition_logic: str = Field(..., description="转场逻辑或衔接方式")


class VlogScript(BaseModel):
    """Vlog 脚本模型"""
    hook_line: str = Field(..., description="开场白（<5秒强钩子）")
    main_script: str = Field(..., description="主体台词，含语气/停顿提示，如[轻快]、[感慨]")
    call_to_action: str = Field(..., description="结尾互动引导语")
    subtitle_highlights: List[str] = Field(..., description="字幕重点标注内容（用【】标出的部分）")
    ai_voice_suggestion: str = Field(..., description="AI配音建议：语音风格、语速、情感强度")
    bgm_style_recommendation: str = Field(..., description="BGM 风格推荐，区分平台（抖音/小红书/B站）")


class PublishingOptimizationPlan(BaseModel):
    """发布优化方案模型"""
    recommended_post_time: str = Field(..., description="推荐发布时间（基于平台活跃时段）")
    cover_texts: List[str] = Field(..., min_length=2, max_length=2, description="封面文案（2种备选）")
    hashtags: List[str] = Field(..., min_length=7, max_length=7, description="话题标签：5个精准 + 2个泛流量")
    first_comment_draft: str = Field(..., description="首评预埋文案")
    engagement_maintenance_tips: str = Field(..., description="前24小时互动维护建议")
    platform_specific_bgm_advice: str = Field(..., description="多平台 BGM 具体建议（抖音/小红书/B站差异化说明）")