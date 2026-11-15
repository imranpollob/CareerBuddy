"""Live Nova competency-flow check against loopback DynamoDB Local only.

Creates an opted-out temporary profile, then removes only its own partition.
Uses inference credits; creates no AWS resources or login credentials.
"""
import json
from pathlib import Path
from uuid import uuid4
from dotenv import load_dotenv
from boto3.dynamodb.conditions import Key
from backend.config import Settings
from backend.db import DynamoRepository,item
from backend.models import Profile
from backend.service import Service
from backend.orchestrator import chat
from backend import conversation


def main():
    load_dotenv()
    settings=Settings(ai_mode='bedrock')
    repo=DynamoRepository(endpoint='http://127.0.0.1:8001',region='us-east-1')
    service=Service(repo,settings)
    service.seed()
    uid=uuid4().hex;pk=f'USER#{uid}'
    profile=Profile(id=uid,name='Temporary career-path check',role='candidate',current_role='Software Engineer',target_role='AI Engineer',career_goal='switch_careers',claimed_skills=['python','sql'],synthetic=False,marketplace_opt_in=False)
    repo.write([item(pk,'PROFILE',profile.model_dump())])
    report={'mode':'bedrock','model':settings.model_id}
    try:
        plan=service.learning.plan(uid)
        skill=next(s['skill'] for s in plan['skills'] if s['skill']=='python')
        expanded=service.learning.expand(uid,skill)
        topics=next(s for s in expanded['skills'] if s['skill']==skill)['topics']
        assert len(topics)==3
        print('Live competency path generated',flush=True)
        lesson=service.learning.lesson(uid,topics[0]['id'])
        assert lesson['examples'] and lesson['key_takeaways']
        print('Structured lesson generated',flush=True)
        attempt=service.learning.practice(uid,topics[0]['id'])
        assert attempt['competency_id']==topics[0]['id'] and all('correct_index' not in q for q in attempt['questions'])
        key=repo.get(pk,f"ASSESSMENT_KEY#{attempt['id']}")
        service.submit(uid,attempt['id'],{q['id']:int(q['correct_index']) for q in key['questions']})
        restored=Service(DynamoRepository(endpoint='http://127.0.0.1:8001',region='us-east-1'),settings)
        passport=restored.learning.passport(uid)
        assert len(passport['competencies'])==1 and passport['competencies'][0]['passed']
        assert passport['skills']==[]
        print('Competency evidence persisted without overstating whole-skill evidence',flush=True)
        response,_=chat(service,settings,uid,'candidate','Evaluate my profile and suggest my next learning topic.')
        assert any(d.specialist=='coach' for d in response.delegations)
        conversation.append(repo,uid,conversation.history(repo,uid),'Evaluate my profile',response)
        assert conversation.history(restored.repo,uid)['messages'][-1]['text']==response.message
        report.update(competencies=len(topics),structured_lesson='passed',private_key='not_exposed',competency_grading='passed',whole_skill_not_overstated=True,persistent_history='passed',coach_delegation='passed')
        Path('.local').mkdir(exist_ok=True)
        Path('.local/careerbuddy-flow-report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),flush=True)
    finally:
        args={'KeyConditionExpression':Key('PK').eq(pk),'ConsistentRead':True}
        while True:
            page=repo.table.query(**args)
            for record in page['Items']:
                repo.table.delete_item(Key={'PK':record['PK'],'SK':record['SK']})
            if 'LastEvaluatedKey' not in page:break
            args['ExclusiveStartKey']=page['LastEvaluatedKey']
        print('Temporary profile removed',flush=True)


if __name__=='__main__':
    main()
