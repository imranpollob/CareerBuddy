"""Private, revision-guarded learning interviews and replaceable roadmaps."""
from uuid import uuid4
from backend.db import item, Conflict
from backend.models import LearningEvaluation, Profile
from backend.intelligence import normalized_text


class Evaluation:
    KEY='LEARNING_EVALUATION#active'

    def __init__(self,service):
        self.service,self.repo=service,service.repo

    def get(self,uid):
        state=self.repo.get(f'USER#{uid}',self.KEY)
        return LearningEvaluation.model_validate(state).model_dump() if state else None

    def begin(self,uid):
        existing=self.get(uid)
        if existing and existing['status']!='completed':return existing
        profile=self.service.profile(uid)
        turn=self.service.intelligence.interview(profile,[])
        state=LearningEvaluation(id=uuid4().hex,revision=existing['revision']+1 if existing else 0,
            status='interview',mode=self.service.intelligence.settings.ai_mode,question=turn.question,
            question_number=1,total_questions=3,messages=[{'role':'assistant','content':turn.question}],claims=[],
            current_role=profile['current_role'],target_role=profile['target_role'],candidate_track=profile['candidate_track'],
            career_goal=profile['career_goal']).model_dump()
        pk=f'USER#{uid}'
        self.repo.write([item(pk,self.KEY,state)],**({'expected_revision':(pk,self.KEY,existing['revision'])} if existing else {'absent':(pk,self.KEY)}))
        return state

    def answer(self,uid,answer,revision):
        state=self.get(uid)
        if not state or state['status']!='interview' or state['revision']!=revision:
            raise Conflict('This evaluation changed. Refresh before answering.')
        messages=state['messages']+[{'role':'user','content':answer}]
        count=sum(m['role']=='user' for m in messages)
        turn=self.service.intelligence.interview(self.service.profile(uid),messages)
        source=normalized_text(' '.join(m['content'] for m in messages if m['role']=='user'))
        if any(not normalized_text(c.evidence_excerpt) or normalized_text(c.evidence_excerpt) not in source for c in turn.claims):
            raise ValueError('A proposed skill was not supported by your answers. Please retry.')
        state={**state,**turn.model_dump(exclude={'ready_to_review'}),'revision':revision+1,
               'status':'review' if count==3 else 'interview','question_number':min(count+1,3),
               'messages':messages+[{'role':'assistant','content':turn.question}]}
        self.repo.write([item(f'USER#{uid}',self.KEY,state)],expected_revision=(f'USER#{uid}',self.KEY,revision))
        return LearningEvaluation.model_validate(state).model_dump()

    def complete(self,uid,revision):
        state=self.get(uid)
        if not state or state['status']!='review' or state['revision']!=revision:
            raise Conflict('Review the current evaluation before creating a roadmap.')
        pk=f'USER#{uid}'
        profile=Profile.model_validate({**self.service.profile(uid),**{k:state[k] for k in ['current_role','target_role','candidate_track','career_goal']},
                                       'claimed_skills':list(dict.fromkeys(c['skill'] for c in state['claims']))}).model_dump()
        requirements=self.service.market(uid)['requirements']
        proposed=self.service.intelligence.roadmap(profile,state['messages'],requirements,self.service.skills(uid))
        if len(set(proposed.focus_skills))!=len(proposed.focus_skills) or not set(proposed.focus_skills)<={r['skill'] for r in requirements}:
            raise ValueError('The roadmap included unsupported role requirements. Please retry.')
        skill=proposed.focus_skills[0]
        generated=self.service.intelligence.skill_path(profile,skill,requirements)
        path={'skill':skill,'revision':0,'evaluation_id':state['id'],'rationale':generated.rationale,
              'competencies':[{**c.model_dump(),'id':f"{skill}:{state['id']}-{i+1}",'skill':skill} for i,c in enumerate(generated.competencies)]}
        saved={'goal':{k:profile[k] for k in ['current_role','target_role','career_goal']},'requested':True,
               'evaluation_id':state['id'],'focus_skills':proposed.focus_skills,'summary':proposed.summary}
        writes=[item(pk,'PROFILE',profile),item(pk,self.KEY,{**state,'status':'completed','revision':revision+1}),
                item(pk,'CAREER_PATH#active',saved),item(pk,f'PATH#{skill}',path),item(pk,'ACTIVITY#active',{})]
        # Archive generated content before replacing it; attempt/evidence records are never rewritten.
        for old in self.repo.partition(pk,'PATH#'):
            writes.append(item(pk,f"PATH_HISTORY#{old.get('evaluation_id','legacy')}#{old['skill']}",old))
        self.repo.write(writes,expected_revision=(pk,self.KEY,revision))
        return self.service.learning.plan(uid)
