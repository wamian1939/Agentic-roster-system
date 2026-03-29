"""
图形化班表输出：按员工并列泳道显示，每天单独页面
"""
from pathlib import Path
from data.models import SHIFT_TIMES

SHIFT_LABELS = {"AA": "全天", "BB": "白天", "CC": "晚班"}
PX_PER_HOUR = 40
TIMELINE_START = 6
TIMELINE_END = 23
LANE_WIDTH = 170


def employee_color(emp_id: str, is_senior: bool = False) -> str:
    """同一员工固定同一颜色；高级员工与普通员工色系区分"""
    base = sum(ord(c) for c in emp_id)
    hue = (base % 40) if is_senior else (180 + base % 80)
    return f"hsl({hue} 62% 82%)"


def schedule_to_html(schedule: list, output_path: Path, base_date=None, rule_suggestions=None):
    """生成浏览器可读的日视图排班页（员工并列，不重叠）"""
    from datetime import datetime, timedelta

    base = base_date or datetime.now().date()
    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    by_day = {}
    for s in schedule:
        by_day.setdefault(s["day"], []).append(s)

    pages_html = []
    for day in range(1, 8):
        dt = base + timedelta(days=day - (base.weekday() + 1) % 7)
        date_str = dt.strftime("%Y-%m-%d")
        day_name = day_names[day - 1]
        shifts = by_day.get(day, [])

        aa = sorted([s["employee"] for s in shifts if s["shift"] == "AA"])
        bb = sorted([s["employee"] for s in shifts if s["shift"] == "BB"])
        cc = sorted([s["employee"] for s in shifts if s["shift"] == "CC"])
        open_early = sorted(
            [s["employee"] for s in shifts if s["shift"] == "BB" and s.get("start_hour") == 10]
        )
        late_14 = sorted([s["employee"] for s in shifts if s.get("start_hour") == 14])
        day_total = len(aa) + len(bb)
        night_total = len(aa) + len(cc)

        lanes = sorted({s["employee"] for s in shifts})
        emp_senior = {s["employee"]: bool(s.get("is_senior", False)) for s in shifts}
        lane_index = {emp: i for i, emp in enumerate(lanes)}
        lanes_width = max(len(lanes) * LANE_WIDTH, LANE_WIDTH)
        timeline_h = (TIMELINE_END - TIMELINE_START) * PX_PER_HOUR

        lane_headers = "".join(
            f'<div class="lane-h {"senior" if emp_senior.get(emp, False) else ""}" '
            f'style="left:{i * LANE_WIDTH}px;width:{LANE_WIDTH}px">{emp}</div>'
            for i, emp in enumerate(lanes)
        )
        grid_lines = "".join(
            f'<div class="hline" style="top:{(h - TIMELINE_START) * PX_PER_HOUR}px"></div>'
            for h in range(TIMELINE_START, TIMELINE_END + 1)
        )

        # 同一员工当天连续班次合并成一个“连通气泡”
        emp_segments = {}
        for s in sorted(shifts, key=lambda x: (x["employee"], SHIFT_TIMES.get(x["shift"], (0, 0))[0])):
            sh = s["shift"]
            emp = s["employee"]
            start_h, end_h = SHIFT_TIMES.get(sh, (10, 22))
            # 支持任意班次按 start_hour 覆盖起始时间（例如 CC 14:00 到岗）
            if s.get("start_hour") is not None:
                start_h = int(s["start_hour"])
            label = SHIFT_LABELS.get(sh, sh)

            segs = emp_segments.setdefault(emp, [])
            if segs and start_h <= segs[-1]["end"]:
                segs[-1]["end"] = max(segs[-1]["end"], end_h)
                if label not in segs[-1]["labels"]:
                    segs[-1]["labels"].append(label)
            elif segs and start_h == segs[-1]["end"]:
                segs[-1]["end"] = end_h
                if label not in segs[-1]["labels"]:
                    segs[-1]["labels"].append(label)
            else:
                segs.append({"start": start_h, "end": end_h, "labels": [label]})

        blocks_html = []
        for emp, segs in emp_segments.items():
            for seg in segs:
                start_h = seg["start"]
                end_h = seg["end"]
                labels = " + ".join(seg["labels"])
                top = (start_h - TIMELINE_START) * PX_PER_HOUR + 2
                height = (end_h - start_h) * PX_PER_HOUR - 4
                left = lane_index[emp] * LANE_WIDTH + 4
                width = LANE_WIDTH - 8
                blocks_html.append(
                    f'<div class="shift-block {"senior" if emp_senior.get(emp, False) else ""}" '
                    f'style="top:{top}px;left:{left}px;width:{width}px;height:{height}px;'
                    f'background:{employee_color(emp, emp_senior.get(emp, False))}">'
                    f'<div class="shift-label">{labels}</div>'
                    f'<div class="shift-time">{start_h:02d}:00~{end_h:02d}:00</div>'
                    f'<div class="shift-emp">{emp}{" · 高级" if emp_senior.get(emp, False) else ""}</div></div>'
                )

        time_marks = "".join(
            f'<div class="tm" style="top:{(h - TIMELINE_START) * PX_PER_HOUR}px">{h:02d}:00</div>'
            for h in range(TIMELINE_START, TIMELINE_END + 1)
        )

        pages_html.append(f'''
        <div class="day-page" id="day-{day}" data-date="{date_str}" data-name="{day_name}">
          <div class="day-header">{day_name} {date_str}</div>
          <div class="summary">
            <div class="card"><b>开早(10-11)</b><span>{", ".join(open_early) if open_early else "-"}</span></div>
            <div class="card"><b>14点到岗</b><span>{", ".join(late_14) if late_14 else "-"}</span></div>
            <div class="card"><b>白天合计(AA+BB)</b><span>{day_total} 人</span></div>
            <div class="card"><b>晚班合计(AA+CC)</b><span>{night_total} 人</span></div>
            <div class="card"><b>AA/BB/CC</b><span>AA:{len(aa)} BB:{len(bb)} CC:{len(cc)}</span></div>
          </div>
          <div class="timeline-wrap" style="height:{timeline_h + 46}px">
            <div class="time-axis">{time_marks}</div>
            <div class="lanes-head" style="width:{lanes_width}px">{lane_headers}</div>
            <div class="blocks" style="width:{lanes_width}px;height:{timeline_h}px">{grid_lines}{"".join(blocks_html)}</div>
          </div>
        </div>
        ''')

    sugg = rule_suggestions or {}
    sugg_summary = sugg.get("summary", "暂无规则建议（未开启AI诊断或尚未生成）。")
    sugg_items = (sugg.get("suggestions", []) or [])[:3]
    sugg_html = "".join(
        f'<li>'
        f'<div class="s-title">{x.get("title","排班优化建议")} <span class="tag {x.get("priority","medium")}">{x.get("priority","medium").upper()}</span></div>'
        f'<div><b>建议：</b>{x.get("plain_advice", "-")}</div>'
        f'<div><b>原因：</b>{x.get("why", x.get("reason","-"))}</div>'
        f'<div><b>怎么做：</b>{x.get("how_to_apply","按建议修改对应规则参数")}</div>'
        f'</li>'
        for x in sugg_items
    ) or "<li>暂无建议</li>"

    html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8" />
<title>排班表</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin: 0; padding: 16px; background: #f3f5f8; font-family: "Microsoft YaHei", sans-serif; color: #1f2937; }}
h1 {{ margin: 0 0 10px; }}
.toolbar {{ display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }}
.toolbar button {{ padding: 8px 14px; border: 1px solid #2f80ed; color: #2f80ed; background: #fff; border-radius: 6px; cursor: pointer; }}
.toolbar button:hover {{ background: #2f80ed; color: #fff; }}
.curr-date {{ margin-left: auto; font-weight: 700; }}
.day-page {{ display: none; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 3px 12px rgba(0,0,0,0.08); }}
.day-page.active {{ display: block; }}
.day-header {{ background: #2f80ed; color: #fff; padding: 14px; text-align: center; font-size: 18px; font-weight: 700; }}
.summary {{ display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 8px; padding: 12px; border-bottom: 1px solid #e5e7eb; background: #f8fbff; }}
.card {{ background: #fff; border: 1px solid #dbe3ef; border-radius: 8px; padding: 8px 10px; }}
.card b {{ font-size: 12px; color: #475569; display: block; margin-bottom: 4px; }}
.card span {{ font-size: 12px; }}
.timeline-wrap {{ position: relative; padding: 12px 12px 12px 56px; overflow-x: auto; }}
.time-axis {{ position: absolute; left: 10px; top: 44px; width: 42px; color: #6b7280; font-size: 12px; }}
.tm {{ position: absolute; transform: translateY(-7px); }}
.lanes-head {{ position: relative; height: 30px; }}
.lane-h {{ position: absolute; top: 0; text-align: center; padding-top: 5px; font-size: 12px; border: 1px solid #e5e7eb; background: #f3f4f6; border-radius: 6px; color: #374151; }}
.lane-h.senior {{ border-color: #f59e0b; background: #fff7e6; color: #9a5b00; }}
.blocks {{ position: relative; margin-top: 6px; border: 1px solid #e5e7eb; border-radius: 8px; background: #fcfdff; }}
.hline {{ position: absolute; left: 0; right: 0; height: 1px; background: #edf1f5; }}
.shift-block {{ position: absolute; border-radius: 8px; border: 1px solid rgba(0,0,0,0.12); box-shadow: 0 1px 2px rgba(0,0,0,0.08); padding: 6px 8px; overflow: hidden; }}
.shift-block.senior {{ border-color: rgba(245,158,11,0.9); box-shadow: 0 0 0 1px rgba(245,158,11,0.25) inset; }}
.shift-label {{ font-weight: 700; font-size: 12px; }}
.shift-time {{ font-size: 11px; color: #475569; margin-top: 1px; }}
.shift-emp {{ font-size: 12px; margin-top: 4px; }}
.foot {{ margin-top: 12px; color: #6b7280; font-size: 12px; text-align: center; }}
.rules-panel {{ margin: 10px 0 14px; padding: 10px 12px; background: #fff; border: 1px solid #dbe3ef; border-radius: 10px; }}
.rules-panel h2 {{ margin: 0 0 8px; font-size: 16px; }}
.rules-panel p {{ margin: 0 0 8px; font-size: 13px; color: #334155; }}
.rules-panel ul {{ margin: 0; padding-left: 20px; }}
.rules-panel li {{ margin-bottom: 10px; font-size: 12px; line-height: 1.5; }}
.rules-panel .s-title {{ font-weight: 700; margin-bottom: 2px; }}
.rules-panel .tag {{ display:inline-block; font-size:10px; border-radius:10px; padding:1px 6px; margin-left:6px; color:#fff; }}
.rules-panel .tag.high {{ background:#dc2626; }}
.rules-panel .tag.medium {{ background:#d97706; }}
.rules-panel .tag.low {{ background:#2563eb; }}
.rules-actions {{ display:flex; gap:8px; align-items:center; margin:8px 0 2px; flex-wrap:wrap; }}
.rules-actions input {{ padding:6px 8px; border:1px solid #cbd5e1; border-radius:6px; min-width:230px; }}
.rules-actions button {{ padding:6px 10px; border:1px solid #2f80ed; color:#2f80ed; background:#fff; border-radius:6px; cursor:pointer; }}
.rules-actions button:hover {{ background:#2f80ed; color:#fff; }}
.apply-msg {{ font-size:12px; color:#475569; margin-top:4px; min-height:18px; }}
</style>
</head>
<body>
<h1>排班表（员工并列泳道）</h1>
<div class="rules-panel">
  <h2>本周排班建议</h2>
  <p>{sugg_summary}</p>
  <div class="rules-actions">
    <input id="api-base" value="http://127.0.0.1:8765" />
    <button onclick="applyAndRerun()">Apply建议并重排</button>
  </div>
  <div class="apply-msg" id="apply-msg">先在终端运行: python integration/demo_apply_server.py</div>
  <ul>{sugg_html}</ul>
</div>
<div class="toolbar">
  <button onclick="nav(-1)">上一日</button>
  <button onclick="show(1)">今天</button>
  <button onclick="nav(1)">下一日</button>
  <span class="curr-date" id="curr-date"></span>
</div>
{''.join(pages_html)}
<p class="foot">共 {len(schedule)} 个班次 · 浏览器视图已与文字口径对齐</p>
<script>
let curr = 1;
function show(day) {{
  curr = Math.max(1, Math.min(7, day));
  document.querySelectorAll('.day-page').forEach(el => el.classList.remove('active'));
  const p = document.getElementById('day-' + curr);
  p.classList.add('active');
  document.getElementById('curr-date').textContent = p.dataset.name + ' ' + p.dataset.date;
}}
function nav(delta) {{ show(curr + delta); }}
async function applyAndRerun() {{
  const el = document.getElementById('apply-msg');
  const base = (document.getElementById('api-base').value || 'http://127.0.0.1:8765').trim();
  el.textContent = '正在应用建议并重新排班，请稍候...';
  try {{
    const resp = await fetch(base + '/api/roster/apply-and-rerun', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: '{{}}'
    }});
    if (resp.status === 404) {{
      const resp2 = await fetch(base + '/apply-and-rerun', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: '{{}}'
      }});
      const data2 = await resp2.json();
      if (!resp2.ok || data2.success === false) throw new Error(data2.message || ('HTTP ' + resp2.status));
      el.textContent = '应用成功，2秒后自动刷新页面';
      setTimeout(() => window.location.reload(), 2000);
      return;
    }}
    const data = await resp.json();
    if (!resp.ok || data.success === false) {{
      throw new Error(data.message || ('HTTP ' + resp.status));
    }}
    el.textContent = '应用成功，2秒后自动刷新页面';
    setTimeout(() => window.location.reload(), 2000);
  }} catch (err) {{
    el.textContent = '应用失败: ' + (err?.message || err) + '。请先启动 demo_apply_server。';
  }}
}}
show(1);
</script>
</body>
</html>'''

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out
