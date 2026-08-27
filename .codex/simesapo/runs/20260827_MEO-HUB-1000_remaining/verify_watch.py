import sys,time,runpy
from pathlib import Path
BASE=Path(__file__).parent
for cycle in range(300):
 if (BASE/'stop_verification.flag').exists():break
 sys.argv=[str(BASE/'verify_batch.py'),'--recheck-weak']
 print('verification_cycle',cycle,flush=True)
 runpy.run_path(str(BASE/'verify_batch.py'),run_name='__main__')
 time.sleep(20)
