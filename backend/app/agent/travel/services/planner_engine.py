"""
时间轴模型: 内部一律用"当天分钟数"计时, 输出前再转回 HH:MM 字符串。
搜索策略: (去程×回程×酒店) 的每个组合做一次按天填槽的回溯搜索,
收集可行方案后取"预算内花费最充分"的一个; 全部失败时给出兜底方案。
"""

import math
import random
import time

from app.core.constants import HAS_METRO

# 搜索硬超时(秒)
TIME_LIMIT = 60.0
# 单组合回溯上限(按槽位粒度)
DAY_RETRY_CAP = 3000
# 全局回溯上限
TOTAL_RETRY_CAP = 10000
# 最多收集的可行方案数
PLAN_CAP = 30
# 预算浮动比例(0.2 = 允许超出预算20%)
BUDGET_TOLERANCE = 0.2

# 一天的时间锚点(单位: 小时, 想改几点直接改数字)
BREAKFAST_T = 8        # 08:00 早餐
LUNCH_OPEN = 11        # 午餐最早开餐
LUNCH_LATE = 13        # 午餐最晚开餐
DINNER_OPEN = 17       # 晚餐最早开餐
DINNER_LATE = 20       # 晚餐最晚开餐
SLEEP_T = 23           # 休息线
WAKE_T = 7             # 起床线
HOTEL_LATE = 23.5      # 最晚入住
METRO_OPEN = 6         # 地铁首班
ARRIVE_EARLIEST = 8    # 到达目的地的最早时刻
LUNCH_READY = 10.5     # 最早出发去午餐
DINNER_READY = 16      # 最早出发去晚餐
DAY_END = 24           # 一天结束线

# 时长类参数(分钟) / 候选数
MEAL_SPAN = 60              # 一餐用时(分钟)
FREE_SPAN = 60              # "周边逛逛"垫时长(分钟)
CAND_CAP = 30               # 每类槽位最多尝试的候选数

# (下面自动×60转成分钟, 代码内部统一用分钟, 不用动)
BREAKFAST_T *= 60
LUNCH_OPEN *= 60
LUNCH_LATE *= 60
DINNER_OPEN *= 60
DINNER_LATE *= 60
SLEEP_T *= 60
WAKE_T *= 60
HOTEL_LATE *= 60
METRO_OPEN *= 60
ARRIVE_EARLIEST *= 60
LUNCH_READY *= 60
DINNER_READY *= 60
DAY_END *= 60


#时间字符串('HH:MM')转分钟数, 解析失败返回None
def _hm(text):
    try:
        h, m = str(text).split(":")
        return int(h) * 60 + int(m)
    except (ValueError, TypeError):
        return None


#分钟数转'HH:MM'字符串
def _fmt(minute):
    minute = int(minute) % (24 * 60)
    return f"{minute // 60:02d}:{minute % 60:02d}"


#两点间球面距离(km), 缺坐标按0处理
def _distance_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return 0.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


#向上取整除法
def _ceil_div(a, b):
    return -(-int(a) // int(b))


#行程规划引擎: (去程×回程×酒店)组合搜索 + 按天填槽回溯
#对外接口: Planner(cons, data).search() -> (ok, 行程天列表 或 空方案dict)
class Planner:

    #初始化: 解析约束, 数据转为记录列表, 划分子预算
    def __init__(self, cons, data):
        self.t0 = time.time()
        self.nodes = 0        # 搜索节点数(诊断用)
        self.bt = 0           # 全局回溯计数(诊断用)
        self.stop = False     # 超时/资源耗尽标志
        self.plans_found = 0
        self.retry_day = 0

        self.cons_start = cons["start_city"]
        self.cons_target = cons["target_city"]
        self.days = max(1, int(cons["days"]))
        self.people = max(1, int(cons.get("people_number", 1)))
        self.budget = float(cons.get("overall_budget") or 0)
        self.split = self._split_budget()

        self.attractions = self._load_pois(data.get("attractions"), with_stay=True)
        self.restaurants = self._load_pois(data.get("restaurants"))
        self.hotels = self._load_hotels(data.get("accommodations"))
        self.coord = {r["name"]: (r["lat"], r["lon"])
                      for r in self.attractions + self.restaurants + self.hotels}
        self.modes = ["metro", "taxi", "walk"] if self.cons_target in HAS_METRO else ["taxi", "walk"]

        self.rides_out = self._load_rides(data.get("intercity_transport"), self.cons_start, self.cons_target)
        self.rides_back = self._load_rides(data.get("intercity_transport"), self.cons_target, self.cons_start)
        self.same_city = self.cons_start == self.cons_target or (not self.rides_out and not self.rides_back)
        if self.same_city:
            self.rides_out = self.rides_back = []

    #总预算 → 子预算指导(城际/酒店/餐饮/景点), 及每餐、每晚锚点
    def _split_budget(self):
        total = self.budget or 5000
        d = self.days
        transport = total * max(0.15, 0.35 - d * 0.03)
        hotel = total * min(0.40, 0.15 + (d - 1) * 0.08)
        meals = total * 0.18
        est_rooms = max(1, _ceil_div(self.people, 4))
        return {"transport": transport, "hotel": hotel, "meals": meals,
                "attraction": total - transport - hotel - meals,
                "per_meal": meals / max(1, 2 * d),
                "per_night": hotel / max(1, (d - 1) * est_rooms)}

    # ═══════════════ 数据准备 ═══════════════

    #景点/餐厅 DataFrame → 记录列表(时间转分钟)
    @staticmethod
    def _load_pois(df, with_stay=False):
        if df is None or df.empty:
            return []
        out = []
        for r in df.to_dict("records"):
            rec = {
                "name": str(r.get("name", "")),
                "price": float(r.get("price") or 0),
                "rating": float(r.get("rating") or 0),
                "lat": r.get("lat"), "lon": r.get("lon"),
                "open": _hm(r.get("opentime")), "close": _hm(r.get("endtime")),
            }
            if with_stay:
                try:
                    rec["stay"] = int(float(r.get("recommendmaxtime") or 1.5) * 60)
                except (TypeError, ValueError):
                    rec["stay"] = 90
            out.append(rec)
        return out

    #酒店 DataFrame → 记录列表
    @staticmethod
    def _load_hotels(df):
        if df is None or df.empty:
            return []
        return [{"name": str(r.get("name", "")), "price": float(r.get("price") or 0),
                 "beds": max(1, int(r.get("numbed") or 1)),
                 "lat": r.get("lat"), "lon": r.get("lon")}
                for r in df.to_dict("records")]

    #某城市对的单程交通记录
    @staticmethod
    def _load_rides(df, sc, tc):
        if df is None or df.empty:
            return []
        out = []
        for r in df.to_dict("records"):
            if r.get("start_city") != sc or r.get("end_city") != tc:
                continue
            begin, end = _hm(r.get("BeginTime")), _hm(r.get("EndTime"))
            if begin is None or end is None:
                continue
            no = r.get("TrainID")
            if no is None or (isinstance(no, float) and math.isnan(no)):
                no = r.get("FlightID")
            kind = "train" if r.get("transport_type") == "train" else "airplane"
            out.append({"kind": kind, "no": "" if no is None else str(no),
                        "begin": begin, "end": end,
                        "cost": float(r.get("Cost") or 0),
                        "from": str(r.get("From", sc)), "to": str(r.get("To", tc))})
        return out

    # ═══════════════ 对外搜索 ═══════════════

    #对外搜索入口: 同城走单组合, 跨城遍历(去程×回程×酒店)组合择优
    def search(self):
        self.deadline = self.t0 + TIME_LIMIT
        if self.same_city:
            plan, cost, complete = self._trip(None, None, None)
            if plan and complete:
                return True, plan
            return False, self._empty()

        best, best_cost, rescue = None, -1.0, None
        for go in self._rank_out():
            if self._capped():
                break
            for back in self._rank_back():
                if self._capped():
                    break
                if self.days == 1 and back["end"] <= go["end"]:
                    self.bt += 1
                    continue
                for hotel in self._hotel_order():
                    if self._capped():
                        break
                    plan, cost, complete = self._trip(go, back, hotel)
                    if plan is None:
                        continue
                    if cost <= self.budget * (1 + BUDGET_TOLERANCE):
                        self.plans_found += 1
                        if cost > best_cost:
                            best, best_cost = plan, cost
                    elif rescue is None:
                        rescue = plan        # 超预算的完整方案留作兜底
                    if self.plans_found >= PLAN_CAP:
                        break
                if self.plans_found >= PLAN_CAP:
                    break
            if self.plans_found >= PLAN_CAP:
                break
        if best:
            return True, best
        if rescue:
            return True, rescue
        return False, self._empty()

    #超时/回溯/方案数 三项上限检查, 触发任一即停止搜索
    def _capped(self):
        if self.stop or time.time() > self.deadline or self.bt > TOTAL_RETRY_CAP:
            self.stop = True
            return True
        return False

    #去程排名: 高铁/动车/飞机优先于普速火车, 再按出发早+便宜综合分; 到达不得早于8点
    def _rank_out(self):
        rides = [r for r in self.rides_out if r["end"] >= ARRIVE_EARLIEST] or self.rides_out
        if not rides:
            return []
        tr = {v: i + 1 for i, v in enumerate(sorted({r["begin"] for r in rides}))}
        pr = {v: i + 1 for i, v in enumerate(sorted({r["cost"] for r in rides}))}
        scored = [(self._slow_train(r) * 10000 + tr[r["begin"]] + pr[r["cost"]]
                   + random.uniform(0, 0.9), r) for r in rides]
        scored.sort(key=lambda x: x[0])
        return [r for _, r in scored]

    #回程排名: 高铁优先, 同级到达越晚越好(玩得充分)
    def _rank_back(self):
        return sorted(self.rides_back,
                      key=lambda r: (self._slow_train(r) * 10000, -r["end"]))

    #普速火车(K/T/Z/数字车头)返回1, 高铁/动车/城际/飞机返回0
    @staticmethod
    def _slow_train(ride):
        if ride["kind"] != "train":
            return 0
        return 0 if ride["no"][:1].upper() in ("G", "D", "C") else 1

    #酒店顺序: 价格贴近每晚目标者优先 + 最便宜兜底
    def _hotel_order(self):
        if not self.hotels:
            return []
        target = self.split["per_night"]
        near = sorted(self.hotels, key=lambda h: abs(h["price"] - target) + random.uniform(0, 15))
        cheap = sorted(self.hotels, key=lambda h: h["price"])
        merged, seen = [], set()
        for h in near[:CAND_CAP // 2] + cheap[:CAND_CAP // 2]:
            if h["name"] not in seen:
                seen.add(h["name"])
                merged.append(h)
        return merged

    #空方案兜底
    def _empty(self):
        return {"people_number": self.people,
                "start_city": self.cons_start, "target_city": self.cons_target,
                "itinerary": []}

    # ═══════════════ 单次组合的行程 ═══════════════

    #一个(去程,回程,酒店)组合的完整行程; 失败返回 (None, 0, False)
    def _trip(self, go, back, hotel):
        self.retry_day = 0
        if self.days > 1 and hotel is None:
            return None, 0, False          # 多日行程必须有酒店可住
        rooms = max(1, _ceil_div(self.people, hotel["beds"])) if hotel else 1
        hotel_cost = hotel["price"] * rooms * (self.days - 1) if hotel and self.days > 1 else 0
        inter_cost = (go["cost"] + back["cost"]) * self.people if go else 0
        if self.budget and hotel_cost + inter_cost > self.budget * (1 + BUDGET_TOLERANCE):
            self.bt += 1
            return None, 0, False

        ctx = {"go": go, "back": back, "hotel": hotel, "rooms": rooms,
               "visited_a": set(), "visited_r": set(), "out": [None] * self.days,
               "path": set()}

        # 第一天初始活动与状态
        acts0, now0, place0 = [], 0, self.cons_target
        if go:
            first = {"type": go["kind"], "position": go["from"],
                     "price": go["cost"], "cost": go["cost"] * self.people,
                     "start_time": _fmt(go["begin"]), "end_time": _fmt(go["end"]),
                     "start": go["from"], "end": go["to"], "transports": []}
            if go["kind"] == "train":
                first["TrainID"] = go["no"]
            else:
                first["FlightID"] = go["no"]
            acts0.append(first)
            now0, place0 = go["end"], go["to"]
        else:
            now0, place0 = 8 * 60, (hotel["name"] if hotel else self.cons_target)

        if not self._fill_day(ctx, 0, now0, place0, acts0, False, False):
            return None, 0, False
        spent = sum(a.get("cost", 0) + sum(t.get("cost", 0) for t in a.get("transports", []))
                    for day in ctx["out"] for a in day)
        plan = [{"day": i + 1, "activities": acts} for i, acts in enumerate(ctx["out"])]
        return plan, spent + hotel_cost + inter_cost, True

    # ═══════════════ 按天填槽(回溯搜索) ═══════════════

    #排第day天(入口): 同一条路径上状态重复说明在兜圈子, 直接剪枝
    def _fill_day(self, ctx, day, now, place, acts, lunch_done, dinner_done):
        if self.stop or self.retry_day > DAY_RETRY_CAP:
            return False
        self.nodes += 1
        key = (day, now, place, lunch_done, dinner_done)
        if key in ctx["path"]:
            return False
        ctx["path"].add(key)
        try:
            return self._fill_day_body(ctx, day, now, place, acts,
                                       lunch_done, dinner_done)
        finally:
            ctx["path"].discard(key)

    #排第day天: 递归尝试候选槽位; 当天完成后转天(多日), 全部排好返回True
    def _fill_day_body(self, ctx, day, now, place, acts, lunch_done, dinner_done):
        last = day == self.days - 1
        hotel = ctx["hotel"]

        # 新一天首次进入: 酒店早餐(只在开天时加一次)
        if day > 0 and not acts:
            acts.append({"position": hotel["name"], "type": "breakfast", "price": 0, "cost": 0,
                         "start_time": _fmt(BREAKFAST_T), "end_time": _fmt(BREAKFAST_T + 30),
                         "transports": []})
            now, place = BREAKFAST_T + 30, hotel["name"]

        # ---- 尝试候选槽位(顺序: 三餐 > 景点 > 垫时间) ----
        for slot in self._options(ctx, day, now, place, acts, lunch_done, dinner_done):
            mark, (new_now, new_place, lunch_done2, dinner_done2) = self._apply(acts, slot)
            if self._fill_day(ctx, day, new_now, new_place, acts, lunch_done2, dinner_done2):
                return True
            self._rollback(acts, mark, slot)
            self.bt += 1
            self.retry_day += 1

        # ---- 槽位耗尽: 尝试收尾 ----
        if last:
            if self._close_last(ctx, now, place, acts, lunch_done, dinner_done):
                ctx["out"][day] = acts        # 行程定稿, 存当天活动
                return True
            return False
        # 两餐没吃齐不许收尾; 但饭点已过的餐豁免(比如傍晚才到, 午餐物理上不可能)
        if not lunch_done and now < LUNCH_LATE:
            return False
        if not dinner_done and now < DINNER_LATE:
            return False
        if not self._append_hotel(ctx, now, place, acts):
            return False
        ctx["out"][day] = acts                # 行程定稿, 存当天活动
        if self._fill_day(ctx, day + 1, 0, hotel["name"], [], False, False):
            return True
        acts.pop()                            # 后续天失败: 撤酒店, 回溯
        ctx["out"][day] = None
        return False

    #当前时刻的候选槽位, 按优先级: 三餐 > 景点 > 垫时间
    def _options(self, ctx, day, now, place, acts, lunch_done, dinner_done):
        last = day == self.days - 1
        opts = []
        # 午餐(必排): 窗口 11:00-13:00
        if not lunch_done:
            if now >= LUNCH_LATE:
                return []                     # 窗口错过 → 本分支作废
            if now >= LUNCH_READY:
                opts += self._meal_slots(ctx, now, place, acts, "lunch", last,
                                         lunch_done=True, dinner_done=False)
        # 晚餐(必排, 午餐后): 窗口 17:00-20:00
        if lunch_done and not dinner_done:
            if now >= DINNER_LATE:
                return []
            if now >= DINNER_READY:
                opts += self._meal_slots(ctx, now, place, acts, "dinner", last,
                                         lunch_done=True, dinner_done=True)
        # 景点(截止: 下一餐窗口 / 收尾时间)
        deadline = self._deadline(ctx, place, lunch_done, dinner_done, last)
        if now < deadline:
            opts += self._attraction_slots(ctx, now, place, deadline,
                                           lunch_done, dinner_done)
            if not acts or acts[-1].get("type") != "free":
                opts += self._free_slots(now, deadline, place,
                                         lunch_done, dinner_done)
        return opts

    #还能排活动的截止时刻
    def _deadline(self, ctx, place, lunch_done, dinner_done, last):
        leave = self._leave_by(ctx, place)
        if not last:
            if not lunch_done:
                return LUNCH_LATE
            if not dinner_done:
                return DINNER_LATE
            return DINNER_LATE
        # 最后一天同样按餐窗卡, 但饭点实在赶不上车时以发车为准(这顿饭就只能不吃了)
        if not lunch_done and leave >= LUNCH_LATE:
            return LUNCH_LATE
        if lunch_done and not dinner_done and leave >= DINNER_LATE:
            return DINNER_LATE
        return leave

    #午餐/晚餐候选槽位: 窗口内开餐、餐厅在营业、评分惩罚偏离每餐目标
    def _meal_slots(self, ctx, now, place, acts, kind, last, lunch_done, dinner_done):
        open_t = LUNCH_OPEN if kind == "lunch" else DINNER_OPEN
        late_t = LUNCH_LATE if kind == "lunch" else DINNER_LATE
        target = self.split["per_meal"]
        cands = []
        for r in self.restaurants:
            if r["name"] in ctx["visited_r"] or r["open"] is None or r["close"] is None:
                continue
            dur = self._travel_min(place, r["name"])
            start = max(now + dur, open_t, r["open"])
            if start > late_t or start + MEAL_SPAN > r["close"]:
                continue
            if last and not self._can_reach_station_in(ctx, r["name"], start + MEAL_SPAN):
                continue
            cands.append((abs(r["price"] - target) / max(1.0, target) * 2
                          - r["rating"] * 0.1 + random.uniform(0, 0.3), r, start, dur))
        cands.sort(key=lambda x: x[0])
        slots = []
        for _, r, start, dur in cands[:CAND_CAP]:
            ride = self._ride_for(place, r["name"], start)
            if ride is None:
                continue
            meal = {"position": r["name"], "type": kind, "price": r["price"],
                    "cost": r["price"] * self.people,
                    "start_time": _fmt(start), "end_time": _fmt(start + MEAL_SPAN),
                    "transports": [ride]}
            pre = self._gap_filler(now, start - dur)
            slots.append(((start + MEAL_SPAN, r["name"], lunch_done, dinner_done),
                          [pre, meal] if pre else [meal],
                          [(ctx["visited_r"], r["name"])]))
        return slots

    #景点候选槽位: 营业时间内、游览时长够、不超截止时刻
    def _attraction_slots(self, ctx, now, place, deadline, lunch_done, dinner_done):
        cands = []
        for a in self.attractions:
            if a["name"] in ctx["visited_a"] or a["open"] is None or a["close"] is None:
                continue
            dur = self._travel_min(place, a["name"])
            start = max(now + dur, a["open"])
            end = start + a["stay"]
            if start > deadline or end > min(deadline, a["close"]):
                continue
            cands.append((-a["rating"] + random.uniform(0, 0.2), a, start, end, dur))
        cands.sort(key=lambda x: x[0])
        slots = []
        for _, a, start, end, dur in cands[:CAND_CAP]:
            ride = self._ride_for(place, a["name"], start)
            if ride is None:
                continue
            spot = {"position": a["name"], "type": "attraction", "price": a["price"],
                    "cost": a["price"] * self.people, "tickets": self.people,
                    "start_time": _fmt(start), "end_time": _fmt(end), "transports": [ride]}
            pre = self._gap_filler(now, start - dur)
            slots.append(((end, a["name"], lunch_done, dinner_done),
                          [pre, spot] if pre else [spot],
                          [(ctx["visited_a"], a["name"])]))
        return slots

    #垫时间的自由活动(原地, 60分钟)
    def _free_slots(self, now, deadline, place, lunch_done, dinner_done):
        if now + FREE_SPAN > deadline:
            return []
        act = {"position": "周边逛逛", "type": "free", "price": 0, "cost": 0,
               "start_time": _fmt(now), "end_time": _fmt(now + FREE_SPAN), "transports": []}
        return [((now + FREE_SPAN, place, lunch_done, dinner_done), [act], [])]

    #到达活动前的长等待(>60分钟)垫成自由活动
    def _gap_filler(self, now, until):
        if until - now <= FREE_SPAN:
            return None
        return {"position": "周边逛逛", "type": "free", "price": 0, "cost": 0,
                "start_time": _fmt(now), "end_time": _fmt(until), "transports": []}

    #落槽: 追加活动, 登记访问记录; 返回 (回滚标记, 新状态)
    def _apply(self, acts, slot):
        (new_now, new_place, lunch_done, dinner_done), additions, visits = slot
        mark = len(acts)
        for item in additions:
            if item is not None:
                acts.append(item)
        for vset, name in visits:
            vset.add(name)
        return mark, (new_now, new_place, lunch_done, dinner_done)

    #回滚: 删掉刚加的活动, 撤销访问记录
    def _rollback(self, acts, mark, slot):
        _, additions, visits = slot
        del acts[mark:]
        for vset, name in visits:
            vset.discard(name)

    # ═══════════════ 一天的收尾方式 ═══════════════

    #非最后一天收尾: 追加酒店入住活动
    def _append_hotel(self, ctx, now, place, acts):
        hotel = ctx["hotel"]
        arrive = now + self._travel_min(place, hotel["name"])
        if arrive > HOTEL_LATE:
            return False
        ride = self._ride_for(place, hotel["name"], arrive)
        if ride is None:
            return False
        acts.append({"position": hotel["name"], "type": "accommodation",
                     "price": hotel["price"], "cost": hotel["price"] * ctx["rooms"],
                     "room_type": hotel["beds"], "rooms": ctx["rooms"],
                     "start_time": _fmt(arrive), "end_time": "24:00", "transports": [ride]})
        return True

    #最后一天收尾: 还能赶上饭点就不许饿着走; 饭点过了/实在赶不上才收
    def _close_last(self, ctx, now, place, acts, lunch_done, dinner_done):
        back = ctx["back"]
        if back is not None:
            # 午餐还没吃且来得及(离开前留得出1小时吃饭): 不许走
            if not lunch_done and now < LUNCH_LATE and self._leave_by(ctx, place) >= LUNCH_OPEN + MEAL_SPAN:
                return False
            # 午餐吃了晚餐还没吃且来得及: 不许走
            if lunch_done and not dinner_done and now < DINNER_LATE and self._leave_by(ctx, place) >= DINNER_OPEN + MEAL_SPAN:
                return False
            return self._close_by_return(ctx, now, place, acts)
        if dinner_done and now >= DINNER_LATE:
            return True                     # 同城单日: 晚餐后收尾
        if now >= SLEEP_T and dinner_done:
            return True
        return False

    #最后一天: 去车站赶返程车
    def _close_by_return(self, ctx, now, place, acts):
        back = ctx["back"]
        dur = self._travel_min(place, back["from"])
        if now + dur > back["begin"]:
            return False
        ride = self._ride_for(place, back["from"], back["begin"])
        if ride is None:
            return False
        act = {"type": back["kind"], "position": back["from"],
               "price": back["cost"], "cost": back["cost"] * self.people,
               "start_time": _fmt(back["begin"]), "end_time": _fmt(back["end"]),
               "start": back["from"], "end": back["to"], "transports": [ride]}
        if back["kind"] == "train":
            act["TrainID"] = back["no"]
        else:
            act["FlightID"] = back["no"]
        acts.append(act)
        return True

    # ═══════════════ 市内交通与辅助 ═══════════════

    #两点间市内通勤时长(分钟); 同地0
    def _travel_min(self, place, target):
        if place == target:
            return 0
        d = _distance_km(*self.coord.get(place, (None, None)), *self.coord.get(target, (None, None)))
        return max(10, int(d * 3))

    #生成一程市内交通(恰好arrive_by到达); 同地返回[]
    def _ride_for(self, place, target, arrive_by):
        if place == target:
            return []
        d = _distance_km(*self.coord.get(place, (None, None)), *self.coord.get(target, (None, None)))
        dur = max(10, int(d * 3))
        depart = arrive_by - dur
        for mode in self.modes:
            if mode == "metro" and not (METRO_OPEN <= depart <= SLEEP_T):
                continue                    # 地铁不运营时段
            if mode == "taxi":
                cars = max(1, _ceil_div(self.people, 4))
                unit = 10 + max(0, d - 3) * 2.5
                cost = unit * cars
            elif mode == "metro":
                unit = 3 + max(0, _ceil_div(d - 6, 6))
                cost = unit * self.people
            else:
                unit, cost = 0, 0
            return {"mode": mode, "start_time": _fmt(depart), "end_time": _fmt(arrive_by),
                    "price": round(unit, 1), "cost": round(cost, 1), "distance": round(d, 1)}
        return None

    #最后一天: 某时刻在某地, 能否在返程发车前赶到车站
    def _can_reach_station_in(self, ctx, place, by):
        back = ctx["back"]
        if back is None:
            return True
        return by + self._travel_min(place, back["from"]) <= back["begin"]

    #最后一天: 必须出发去车站的截止时刻
    def _leave_by(self, ctx, place):
        back = ctx["back"]
        if back is None:
            return DINNER_LATE
        return back["begin"] - self._travel_min(place, back["from"])

# ═══════════════ 行程后处理 ═══════════════

#睡眠时间过滤: 23:00-07:00 不排景点/餐厅(火车/酒店/早餐除外), 供后处理兜底
def sleep_ok(a):
    t = a.get("type", "")
    if t in ("train", "airplane", "accommodation", "breakfast", "intercity"):
        return True
    st = _hm(a.get("start_time")) or 0
    et = _hm(a.get("end_time")) or 0
    if st >= SLEEP_T or st < WAKE_T:
        return False
    if et > DAY_END or et <= WAKE_T:
        return False
    return True
