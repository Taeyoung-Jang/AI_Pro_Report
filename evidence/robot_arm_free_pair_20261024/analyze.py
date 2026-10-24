import json, math, csv
from pathlib import Path
from robot_arm import free_pair_search as f, search, phase_measure
root=Path('experiments/robot_arm_libero/free_pair_continuation_v5').resolve()
out=Path('development/robot_arm_free_pair_analysis_20261024')
design=f.verify(root)
rows=[]
for d in sorted(root.glob('seed_*/*/attempt_*')):
 c=search.read(d/'candidate.json'); r=f.receipt(d,c)
 row={'case':str(d.relative_to(root)), 'method':d.parent.name,'seed':int(d.parents[1].name[5:]),'index':int(d.name[-5:]),'status':r['status'],'outcome':r.get('task_outcome'),'parameters':c['parameters']}
 if r['status']=='VALID':
  m=search.read(d/'measurement.json'); assert phase_measure.case_measure(d,r)==m
  row.update(measurement=m,steps=sum(r['steps']))
  ph=[json.loads(s) for s in (d/'physics.jsonl').read_text().splitlines()]
  row['final_gap_m']=math.dist(ph[-1]['bowl_xyz_m'][:2],ph[-1]['plate_xyz_m'][:2])
  row['videos']=[str(p.relative_to(root)) for p in d.glob('videos/*.mp4')]
 if (d/'request.json').exists():
  past=[x for x in f.history(root,row['seed']) if int(x['evidence_id'].rsplit('_',1)[1])<row['index']]
  assert search.read(d/'request.json')==f.body(design,past)
  p=f.proposal(design,search.read(d/'response.json'))
  assert c==f.candidate(design,p['parameters'],row['seed'],row['index'],p['hypothesis'])
 else: assert c==f.candidate(design,f.uniform(design,row['seed'],row['index']),row['seed'],row['index'],'uniform bootstrap' if row['index']<2 else 'uniform random')
 rows.append(row)
summary=f.summary(root)
metrics={}
for method in ('afs','random'):
 rr=[x for x in rows if x['method']==method]; valid=[x for x in rr if x['status']=='VALID']
 metrics[method]={'attempt_rate':sum(x['outcome']=='FAIL' for x in rr)/len(rr),'steps':sum(x['steps'] for x in valid),'by_seed':{},'by_segment':{}}
 for seed in (727,733,739):
  group=[x for x in rr if x['seed']==seed]; metrics[method]['by_seed'][seed]={k:sum(x['outcome']==k for x in group) for k in ('PASS','FAIL')}
 for label,group in [('bootstrap',[x for x in rr if x['index']<2]),('selected',[x for x in rr if x['index']>=2])]: metrics[method]['by_segment'][label]={'attempts':len(group),'valid':sum(x['status']=='VALID' for x in group),'fail':sum(x['outcome']=='FAIL' for x in group)}
 for box in (1,2):
  metrics[method][f'box{box}_upper_bound_counts']={a:sum(abs(x['parameters'][f'box{box}_{a}']-design['domain'][f'box{box}_{a}'][1])<1e-9 for x in valid) for a in ('width','depth','height')}
analysis={'root':str(root),'verification':'root sources/models/inherited artifacts; all 24 evidence seals; all 23 full-physics measurements recomputed; six AFS own-seed request/response bindings and all uniform candidates verified','summary':summary,'attempt_denominator_metrics':metrics,'attempt_rate_difference':metrics['afs']['attempt_rate']-metrics['random']['attempt_rate'],'attempt_relative_gain':(metrics['afs']['attempt_rate']/metrics['random']['attempt_rate']-1),'episodes':rows}
(out/'analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
with (out/'episodes.csv').open('w') as stream:
 fields=['case','status','outcome','steps','pattern','rise_m','movement_m','nearest_goal_m','final_gap_m','robot_contact_s','bowl_contact_s']
 w=csv.DictWriter(stream,fieldnames=fields);w.writeheader()
 for x in rows:
  m=x.get('measurement',{});o=m.get('motion_observations',{});ct=m.get('contact_duration_s',{})
  w.writerow(dict(zip(fields,[x['case'],x['status'],x['outcome'],x.get('steps'),o.get('pattern'),o.get('max_rise_after_settle_m'),o.get('max_xy_movement_after_settle_m'),o.get('min_goal_center_xy_gap_after_settle_m'),x.get('final_gap_m'),ct.get('robot_obstacle'),ct.get('bowl_obstacle')])))
print(json.dumps(metrics,indent=2))
for x in rows:
 if x['outcome']=='FAIL': print(x['case'],json.dumps(x['measurement']['motion_observations']), 'finalgap',x['final_gap_m'])
