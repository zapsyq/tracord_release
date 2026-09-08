"""全链路测试：走 agent 测 tool calling + 直接调 Planner 出 timeline 行程"""
import asyncio, sys, time, io, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def _tmin(t):
    if not t or ':' not in str(t): return 0
    h, m = map(int, str(t).split(':'))
    return h * 60 + m

async def run_one(name, query, out):
    from app.agent.tracord_agent import TracordAgent
    from app.agent.travel.services.slot_filler import SlotFillerService
    from app.agent.travel.services.travel_plan_tool import load_data, Planner, _clean_overlaps

    # 1. 全链路：走 agent，判断 tool calling 是否成功
    agent = TracordAgent(None, None, None, 1)
    text = []
    async for c in agent.execute_stream(query):
        text.append(c)
    chain_result = "".join(text)
    # 链路成功 = 回复里带了行程数据标记（现在规划结果是 ⟦PLAN⟧JSON⟦/PLAN⟧, 不再是"第1天"流水账）
    chain_ok = "⟦PLAN⟧" in chain_result

    # 2. 直接调 Planner，出 timeline 行程
    cons = await SlotFillerService().fill_slots(query)
    if cons['start_city'] in ('?', ''):
        cons['start_city'] = cons['target_city']
    if cons['start_city'] == cons['target_city'] and cons['days'] > 1:
        cons['days'] = 1

    data = await load_data(cons)
    planner = Planner(cons, data)
    bs = planner.budget_split
    ok, result = planner.search()
    plan = {'itinerary': result} if isinstance(result, list) else result
    _clean_overlaps(plan.get('itinerary', []))

    total = sum(a.get('cost', 0) + sum(t.get('cost', 0) for t in a.get('transports', []))
                for d in plan.get('itinerary', []) for a in d.get('activities', []))
    act_count = sum(len(d.get('activities', [])) for d in plan.get('itinerary', []))
    elapsed = time.time() - planner.t0

    # 分品类统计
    tr_c = hotel_c = meal_c = attr_c = inner_c = 0
    for d in plan.get('itinerary', []):
        for a in d.get('activities', []):
            tp = a.get('type',''); c = a.get('cost',0)
            if tp in ('train','airplane','intercity'): tr_c += c
            elif tp == 'accommodation': hotel_c += c
            elif tp in ('lunch','dinner'): meal_c += c
            elif tp == 'attraction': attr_c += c
            inner_c += sum(t.get('cost',0) for t in a.get('transports',[]))

    budget = cons['budget']
    status = 'OK' if plan.get('itinerary') and total > 0 else 'FAIL'
    if total > budget * 1.2: status = 'OVER'

    out.append(f"\n{'='*70}")
    out.append(f"{name}  {cons['start_city']}→{cons['target_city']}  {cons['days']}天  Y{budget}  | 输入: {query}")
    out.append(f"全链路: {'OK' if chain_ok else 'FAIL'} | 子预算: 交通{bs['transport']:.0f} 酒店{bs['hotel']:.0f} 餐饮{bs['meals']:.0f} 景点{bs['attraction']:.0f}")
    out.append(f"{'='*70}")
    out.append(f"状态: {status} | 总Y{total:.0f}/Y{budget} ({total/budget*100:.0f}%) | {act_count}活动 | {elapsed:.1f}s")
    out.append(f"交通{tr_c:.0f} 酒店{hotel_c:.0f} 餐饮{meal_c:.0f} 景点{attr_c:.0f} 市内交通{inner_c:.0f}")

    for d in plan.get('itinerary', []):
        out.append(f"  Day {d['day']}:")
        timeline = []
        for a in d.get('activities', []):
            for t in a.get('transports', []):
                dur = _tmin(t.get('end_time','')) - _tmin(t.get('start_time',''))
                timeline.append((t['start_time'], f"    {t['start_time']}-{t['end_time']} {t['mode']:6s} {dur:3d}min Y{t['cost']:.0f}"))
            icon = {'train':'🚄','airplane':'✈️','attraction':'🎯','lunch':'🍜','dinner':'🍽️','breakfast':'🍳','accommodation':'🏨','free':'🚶','intercity':'🚄'}.get(a['type'],'📍')
            timeline.append((a['start_time'], f"    {a['start_time']}-{a['end_time']} {icon} {a['type']:12s} {a.get('position',a.get('start',''))[:25]:25s} Y{a.get('cost',0):5.0f}"))
        timeline.sort(key=lambda x: _tmin(x[0]))
        for _, line in timeline:
            out.append(line)
    return chain_ok, status, total, budget, elapsed

async def main():
    TESTS = [
        ('南宁→贵阳', '南宁到贵阳四天旅游攻略，预算2000'),
    ]

    out = []
    summary = []
    chain_ok_count = 0
    t0 = time.time()
    for name, q in TESTS:
        try:
            chain_ok, status, total, budget, elapsed = await run_one(name, q, out)
            if chain_ok: chain_ok_count += 1
            pct = total/budget*100 if budget else 0
            summary.append(f"{name:12s} {q:32s} → 链路{'OK' if chain_ok else 'FAIL'} Y{total:5.0f} {pct:3.0f}% {status:5s}")
        except Exception as e:
            summary.append(f"{name:12s} ERROR: {e}")
            out.append(f"\n{name}: ERROR {e}")

    out.append(f"\n{'='*70}")
    out.append(f"链路成功率: {chain_ok_count}/{len(TESTS)} | 总耗时: {time.time()-t0:.0f}s")
    out.append(f"{'='*70}")
    out.append("\n--- 汇总 ---")
    for s in summary:
        out.append(s)

    result = '\n'.join(out)
    os.makedirs('docs', exist_ok=True)
    path = 'docs/batch_test_budget.md'
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# 全链路测试 + 行程 timeline\n\n```\n')
        f.write(result)
        f.write('\n```\n')
    print(f"结果已保存到 {path}")
    print(result[-3000:])

asyncio.run(main())
