from __future__ import annotations

from dataclasses import dataclass

from JLPT_generator.adapters.ai import AiProvider
from JLPT_generator.domain import SessionRun
from JLPT_generator.use_cases.prompts import final_analysis_prompt


@dataclass(frozen=True)
class AnalyzePerformanceUseCase:
    provider: AiProvider

    def run(self, *, session: SessionRun) -> str:
        prompt = final_analysis_prompt(session=session)
        return self.provider.analyze_session_text(prompt=prompt).text
