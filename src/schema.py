from __future__ import annotations
from pydantic import BaseModel, Field

class ArticleSummary(BaseModel):
    title: str = Field(..., description="Concise paper title")
    main_objectives: str = Field(..., description="1–3 sentences")
    research_questions: str = Field(..., description="Single string; items separated by '; '")
    study_type: str = Field(..., description="Study design (experimental, case study, review, qualitative, quantitative, mixed-methods)")
    methodology: str = Field(..., description="2–4 sentences on data collection and analysis")
    main_findings: str = Field(..., description="2–5 sentences with primary results")
    conclusions: str = Field(..., description="1–3 sentences")
    limitations: str = Field(..., description="1–3 sentences or 'Not explicitly stated'")
    rationale: str | None = Field(
        default=None,
        description="(Optional) 2–6 sentences explaining how answers were derived; may cite sections/excerpts",
    )
