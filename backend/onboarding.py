from backend.db import item, Conflict
from backend.intelligence import normalized_text
from backend.models import OnboardingState, Profile


class Onboarding:
    def __init__(self, service):
        self.service, self.repo, self.ai = service, service.repo, service.intelligence

    def public(self,state):
        return OnboardingState.model_validate(state).model_dump()

    def get(self,uid):
        pk,sk=f"USER#{uid}","ONBOARDING#active"
        existing=self.repo.get(pk,sk)
        if existing:
            return self.public(existing)
        profile=self.service.profile(uid)
        turn=self.ai.interview(profile,[])
        state={"revision":0,"status":"interview","mode":self.ai.settings.ai_mode,"question":turn.question,
               "messages":[{"role":"assistant","content":turn.question}],"claims":[],
               "current_role":profile["current_role"],"target_role":profile["target_role"],"candidate_track":profile["candidate_track"]}
        try:
            self.repo.write([item(pk,sk,state)],absent=(pk,sk))
        except Conflict:
            state=self.repo.get(pk,sk)
        return self.public(state)

    def answer(self,uid,answer,revision):
        state=self.get(uid)
        if state["revision"]!=revision or state["status"]=="completed":
            raise Conflict("This interview changed. Refresh before answering.")
        messages=state["messages"]+[{"role":"user","content":answer}]
        answer_count=sum(m["role"]=="user" for m in messages)
        if answer_count>6:
            raise ValueError("Review and confirm the discovered skills before continuing")
        turn=self.ai.interview(self.service.profile(uid),messages)
        source=normalized_text(" ".join(m["content"] for m in messages if m["role"]=="user"))
        claims=[]
        for claim in turn.claims:
            if normalized_text(claim.evidence_excerpt) not in source:
                raise ValueError("A proposed skill was not supported by your answers. Please retry.")
            if claim.skill not in {c["skill"] for c in claims}:
                claims.append(claim.model_dump())
        review=answer_count>=2 and (turn.ready_to_review or answer_count>=6)
        updated={**state,"revision":revision+1,"status":"review" if review else "interview",
                 "question":turn.question,"messages":messages+[{"role":"assistant","content":turn.question}],
                 "claims":claims,"current_role":turn.current_role,"target_role":turn.target_role,
                 "candidate_track":turn.candidate_track}
        self.repo.write([item(f"USER#{uid}","ONBOARDING#active",updated)],expected_revision=(f"USER#{uid}","ONBOARDING#active",revision))
        return self.public(updated)

    def complete(self,uid,revision):
        state=self.get(uid)
        if state["status"]!="review" or state["revision"]!=revision:
            raise Conflict("Review the current skill summary before confirming")
        profile=Profile.model_validate({**self.service.profile(uid),"current_role":state["current_role"],"target_role":state["target_role"],
                                        "candidate_track":state["candidate_track"],"claimed_skills":[c["skill"] for c in state["claims"]],
                                        "onboarding_completed":True}).model_dump()
        updated={**state,"revision":revision+1,"status":"completed"}
        writes=[item(f"USER#{uid}","PROFILE",profile),item(f"USER#{uid}","ONBOARDING#active",updated)]
        self.repo.write(writes,expected_revision=(f"USER#{uid}","ONBOARDING#active",revision))
        return profile
