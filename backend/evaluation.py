"""Private, revision-guarded learning interviews and replaceable roadmaps."""
import re
from uuid import uuid4
from backend.db import item, Conflict
from backend.models import LearningEvaluation, Profile
from backend.intelligence import normalized_text
from backend.tools.jobs import jobs_for_role, requirements, canonical_skill


class Evaluation:
    KEY='LEARNING_EVALUATION#active'

    def __init__(self,service):
        self.service,self.repo=service,service.repo

    def get(self,uid):
        state=self.repo.get(f'USER#{uid}',self.KEY)
        return LearningEvaluation.model_validate(state).model_dump() if state else None

    def begin(self,uid):
        existing=self.get(uid)
        if existing and existing['status']!='completed' and existing.get('flow_version')==4:return existing
        profile=self.service.profile(uid)
        # Resume only interviews that collected explicit goals; old questions may contain defaults.
        # Target role and purpose have their own fields; the free-text question covers the rest.
        question='Which skills, tools, or projects should we consider, and what would you most like to learn next?'
        state=LearningEvaluation(flow_version=4,id=uuid4().hex,revision=existing['revision']+1 if existing else 0,
            status='interview',mode=self.service.intelligence.settings.ai_mode,question=question,
            question_number=1,total_questions=3,messages=[{'role':'assistant','content':question}],claims=[],
            current_role=profile['current_role'],target_role=profile['target_role'],candidate_track=profile['candidate_track'],
            career_goal=profile['career_goal']).model_dump()
        pk=f'USER#{uid}'
        self.repo.write([item(pk,self.KEY,state)],**({'expected_revision':(pk,self.KEY,existing['revision'])} if existing else {'absent':(pk,self.KEY)}))
        return state

    def answer(self,uid,answer,revision,target_role=None,career_goal=None):
        state=self.get(uid)
        if not state or state['status']!='interview' or state['revision']!=revision:
            raise Conflict('This evaluation changed. Refresh before answering.')
        if state['question_number']==1:
            if not target_role or not target_role.strip() or career_goal not in {'stay_relevant','find_job','switch_careers'}:
                raise ValueError('Choose your target role and career purpose before continuing.')
            state={**state,'target_role':target_role.strip(),'career_goal':career_goal}
            answer=f"Target role: {state['target_role']}. Career purpose: {career_goal}. " + answer
        messages=state['messages']+[{'role':'user','content':answer}]
        count=sum(m['role']=='user' for m in messages)
        turn=self.service.intelligence.interview({**self.service.profile(uid),'target_role':state['target_role'],'career_goal':state['career_goal'],'goal_confirmed':True},messages)
        # Every stored claim must quote the user's own words. An ungrounded claim is dropped
        # instead of failing the whole answer, which would force the user to retype it.
        def loose(text):
            return re.sub(r'[^a-z0-9]+',' ',normalized_text(text)).strip()
        user_text=' '.join(m['content'] for m in messages if m['role']=='user')
        source=loose(user_text)
        # Only sentences about what the user already does; never goals or things they want to learn.
        aspiration=re.compile(r"\b(learn|learning|want|wants|need|needs|would like|hope|plan|get better|improve|interested|target role|career purpose)\b",re.I)
        all_sentences=[s.strip() for s in re.split(r'(?<=[.!?])\s+',user_text) if s.strip()]
        sentences=[s for s in all_sentences if not aspiration.search(s)]
        grounded=[]
        for c in turn.claims:
            quote=loose(c.evidence_excerpt)
            if quote and f' {quote} ' in f' {source} ':
                # A verbatim quote from "I need to learn TypeScript" is a goal, not a skill.
                if any(f' {quote} ' in f' {loose(s)} ' for s in sentences) or not any(f' {quote} ' in f' {loose(s)} ' for s in all_sentences):
                    grounded.append(c)
                continue
            # The quote was paraphrased, but the skill is named in the user's own words:
            # keep it and cite the user's actual sentence as evidence.
            names={loose(c.label),loose(c.skill.replace('_',' '))}-{''}
            sentence=next((s for s in sentences if any(f' {n} ' in f' {loose(s)} ' for n in names)),None)
            if sentence:
                grounded.append(c.model_copy(update={'evidence_excerpt':sentence[:240]}))
        # Models occasionally leak markup ("…internship?</") into the question text.
        question=re.sub(r'<[^>]*>?','',turn.question).strip()
        turn=turn.model_copy(update={'claims':grounded,'question':question or turn.question})
        state={**state,**turn.model_dump(exclude={'ready_to_review'}),'revision':revision+1,
               'target_role':state['target_role'],'career_goal':state['career_goal'],'status':'review' if count==3 else 'interview','question_number':min(count+1,3),
               'messages':messages+[{'role':'assistant','content':turn.question}]}
        self.repo.write([item(f'USER#{uid}',self.KEY,state)],expected_revision=(f'USER#{uid}',self.KEY,revision))
        return LearningEvaluation.model_validate(state).model_dump()

    def complete(self,uid,revision):
        state=self.get(uid)
        if not state or state['status']!='review' or state['revision']!=revision:
            raise Conflict('Review the current evaluation before creating a roadmap.')
        pk=f'USER#{uid}'
        profile=Profile.model_validate({**self.service.profile(uid),**{k:state[k] for k in ['current_role','target_role','candidate_track','career_goal']},
                                       'goal_confirmed':True,'claimed_skills':list(dict.fromkeys(c['skill'] for c in state['claims']))}).model_dump()
        role_jobs=jobs_for_role(self.service.jobs(),profile['target_role'])
        role_requirements=requirements(role_jobs)
        proposed=self.service.intelligence.roadmap(profile,state['messages'],role_requirements,self.service.skills(uid))
        # Start with skills the person does not already use; known ones move to the end.
        known={canonical_skill(s) for s in profile['claimed_skills']}
        ordered=sorted(proposed.focus_skills,key=lambda s:canonical_skill(s) in known)
        proposed=proposed.model_copy(update={'focus_skills':ordered})
        skill=proposed.focus_skills[0]
        generated=self.service.intelligence.skill_path(profile,skill,role_requirements)
        path={'skill':skill,'revision':0,'evaluation_id':state['id'],'rationale':generated.rationale,
              'competencies':[{**c.model_dump(),'id':f"{skill}:{state['id']}-{i+1}",'skill':skill} for i,c in enumerate(generated.competencies)]}
        saved={'goal':{k:profile[k] for k in ['current_role','target_role','career_goal']},'requested':True,
               'evaluation_id':state['id'],'market_role_covered':bool(role_jobs),'market_job_ids':[j['id'] for j in role_jobs],'focus_skills':proposed.focus_skills,'summary':proposed.summary}
        writes=[item(pk,'PROFILE',profile),item(pk,self.KEY,{**state,'status':'completed','revision':revision+1}),
                item(pk,'CAREER_PATH#active',saved),item(pk,f'PATH#{skill}',path),item(pk,'ACTIVITY#active',{})]
        # Archive generated content before replacing it; attempt/evidence records are never rewritten.
        for old in self.repo.partition(pk,'PATH#'):
            writes.append(item(pk,f"PATH_HISTORY#{old.get('evaluation_id','legacy')}#{old['skill']}",old))
        self.repo.write(writes,expected_revision=(pk,self.KEY,revision))
        return self.service.learning.plan(uid)
