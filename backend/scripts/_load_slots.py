import sys, io, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app.agent.travel.services.vector_store import VectorStoreService

svc = VectorStoreService()
n = svc.load_slot_examples()
print(f"入库完成: {n} 条")
