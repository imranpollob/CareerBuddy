"""An explicit offline Model provider, exercising the real Strands tool loop.

Only this provider uses deterministic intent rules. Bedrock mode lets the model
select tools. Both modes execute the same nested Agents and business tools.
"""
import json
from uuid import uuid4
from strands.models import Model


class MockModel(Model):
    def __init__(self, role):
        self.role = role
        self.config = {"model_id": "skillpilot-offline-fixture", "context_window_limit": 32000}

    def get_config(self):
        return self.config

    def update_config(self, **kwargs):
        self.config.update(kwargs)

    async def structured_output(self, output_model, prompt, system_prompt=None, **kwargs):
        raise NotImplementedError("Mock uses validated JSON text, not structured_output")
        yield  # pragma: no cover

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        specs = {s["name"]: s for s in tool_specs or []}
        results = [b["toolResult"] for m in messages for b in m["content"] if "toolResult" in b]
        prompt = next((b["text"] for m in reversed(messages) if m["role"] == "user" for b in m["content"] if "text" in b), "")
        tools = []
        if not results:
            if self.role != "orchestrator":
                name = next(iter(specs))
                inputs = {}
                if name == "prepare_skill_assessment":
                    inputs["skill"] = next((s for s in ["python", "rag", "llm", "pytorch", "aws", "evaluation", "sql"] if s in prompt.lower()), "" if "next" in prompt.lower() else "python")
                tools = [(name, inputs)]
            else:
                text = prompt.lower()
                if any(w in text for w in ["assess", "quiz", "test", "reassess"]):
                    tools.append(("assessment_specialist", {"request": prompt}))
                if any(w in text for w in ["coach", "roadmap", "learn", "lesson", "gap", "evaluate my profile"]):
                    tools.append(("coach_specialist", {"request": prompt}))
                if any(w in text for w in ["match", "recommend", "candidate", "find jobs"]):
                    tools.append(("marketplace_specialist", {"request": prompt}))
                if any(w in text for w in ["market", "demand", "requirements", "transition", "become", "career", "analyze jobs"]):
                    tools.append(("job_market_specialist", {"request": prompt}))
        elif self.role != "orchestrator":
            summary_tool = next((s for s in specs.values() if "summary" in s.get("inputSchema", {}).get("json", {}).get("properties", {})), None)
            if summary_tool:
                tools = [(summary_tool["name"], {"summary": "Analysis uses the authoritative tool snapshot. " + {
                    "assessment": "A four-question assessment is ready in the dashboard. Submit there for server grading.",
                    "coach": "Follow a lesson and reassessment to turn missing skills into evidence.",
                    "marketplace": "Review supported requirements and remaining gaps. Coverage is not a hiring prediction.",
                    "job_market": "Skill frequencies are counted from the saved sample; source URLs are retained."
                }[self.role]})]
        yield {"messageStart": {"role": "assistant"}}
        if tools:
            for index, (name, args) in enumerate(tools):
                yield {"contentBlockStart": {"start": {"toolUse": {"toolUseId": uuid4().hex, "name": name}}, "contentBlockIndex": index}}
                yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(args)}}, "contentBlockIndex": index}}
                yield {"contentBlockStop": {"contentBlockIndex": index}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            if self.role != "orchestrator":
                summaries = {"job_market": "I analyzed the saved job sample and counted normalized skill mentions. Review the attached sources and start a fundamentals assessment.",
                             "assessment": "Your assessment is ready in the dashboard. Submit all four answers there for deterministic grading; chat cannot assign a score.",
                             "coach": "Your roadmap prioritizes missing evidence by observed job demand. Open a lesson, practice the exercise, then reassess to update your matches.",
                             "marketplace": "Matches compare listed requirements with passed fundamentals assessments. Review the supported skills and remaining gaps; this is not a hiring prediction."}
                output = json.dumps({"summary": summaries[self.role]})
            elif results:
                summaries = []
                for result in results:
                    for block in result.get("content", []):
                        try:
                            summaries.append(json.loads(block.get("text", "{}"))["summary"])
                        except (KeyError, ValueError):
                            pass
                output = "\n\n".join(summaries) or "The requested data is available in your dashboard."
            else:
                output = "I’m CareerBuddy. I can analyze job requirements, prepare a skills assessment, create a learning roadmap, or explain job matches. What would you like to work on?"
            yield {"contentBlockStart": {"start": {}, "contentBlockIndex": 0}}
            yield {"contentBlockDelta": {"delta": {"text": output}, "contentBlockIndex": 0}}
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "end_turn"}}
        yield {"metadata": {"usage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0}, "metrics": {"latencyMs": 0}}}
