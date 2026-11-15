"""Bounded four-step onboarding; background is not assessment evidence."""
from backend.db import item, Conflict
from backend.models import OnboardingState, Profile

EDUCATION = ['Secondary school / high school', 'Vocational qualification / diploma', 'Associate degree', "Bachelor’s degree", "Master’s degree", 'Doctorate / PhD', 'Other / prefer not to say']
EXPERTISE = ['Beginner', 'Intermediate', 'Advanced', 'Expert']
QUESTIONS = ['What is your current role?', 'What is your highest level of education?', 'How many years of work experience do you have?', 'How would you describe your current expertise?']
OPTIONS = [[], EDUCATION, [str(n) for n in range(31)], EXPERTISE]


class Onboarding:
    def __init__(self, service):
        self.service, self.repo = service, service.repo

    def public(self,state):
        return OnboardingState.model_validate(state).model_dump()

    def get(self,uid):
        pk,sk=f'USER#{uid}','ONBOARDING#active'
        existing=self.repo.get(pk,sk)
        if existing and existing.get('flow_version')==2:
            return self.public(existing)
        if existing and existing['status']=='completed':
            return self.public(existing)
        profile=self.service.profile(uid)
        state={'flow_version':2,'revision':(existing['revision']+1 if existing else 0),'status':'interview',
               'mode':self.service.intelligence.settings.ai_mode,'question':QUESTIONS[0],
               'question_number':1,'total_questions':4,'options':[], 'answers':{},
               'messages':[], 'claims':[], 'current_role':profile['current_role'],
               'target_role':profile['target_role'],'candidate_track':profile['candidate_track']}
        try:
            self.repo.write([item(pk,sk,state)],**({'expected_revision':(pk,sk,existing['revision'])} if existing else {'absent':(pk,sk)}))
        except Conflict:
            state=self.repo.get(pk,sk)
        return self.public(state)

    def answer(self,uid,answer,revision):
        state=self.get(uid)
        if state['revision']!=revision or state['status']!='interview':
            raise Conflict('This onboarding changed. Refresh before answering.')
        index=state['question_number']-1
        answer=answer.strip()
        if not answer or (index==0 and len(answer)>120) or (OPTIONS[index] and answer not in OPTIONS[index]):
            raise ValueError('Choose a valid answer for the current question.')
        keys=['current_role','education_level','years_experience','expertise_level']
        answers={**state['answers'],keys[index]:int(answer) if index==2 else answer}
        done=index==3
        role=answers.get('current_role',state['current_role'])
        updated={**state,'revision':revision+1,'answers':answers,'current_role':role,
                 'candidate_track':'student' if 'student' in role.lower() else 'career_switcher',
                 'status':'review' if done else 'interview','question_number':min(index+2,4),
                 'question':'' if done else QUESTIONS[index+1],'options':[] if done else OPTIONS[index+1],
                 'messages':state['messages']+[{'role':'user','content':f'{QUESTIONS[index]} {answer}'}]}
        self.repo.write([item(f'USER#{uid}','ONBOARDING#active',updated)],expected_revision=(f'USER#{uid}','ONBOARDING#active',revision))
        return self.public(updated)

    def complete(self,uid,revision):
        state=self.get(uid)
        if state['status']!='review' or state['revision']!=revision:
            raise Conflict('Complete the four questions before confirming.')
        profile=Profile.model_validate({**self.service.profile(uid),**state['answers'],
                'candidate_track':state['candidate_track'],'career_goal':'find_job' if state['candidate_track']=='student' else 'switch_careers','onboarding_completed':True}).model_dump()
        updated={**state,'revision':revision+1,'status':'completed'}
        self.repo.write([item(f'USER#{uid}','PROFILE',profile),item(f'USER#{uid}','ONBOARDING#active',updated)],
                        expected_revision=(f'USER#{uid}','ONBOARDING#active',revision))
        return profile
