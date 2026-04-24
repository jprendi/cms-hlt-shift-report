from omsapi import OMSAPI
import sys
from datetime import datetime, timedelta
from collections import defaultdict

def generate_recent_reports():
    omsapi = OMSAPI("https://cmsoms.cern.ch/agg/api", "v1", cert_verify=False)
    print("Authenticating...")
    omsapi.auth_device(client_id="cmsoms-prod-public")

    time_cutoff = datetime.utcnow() - timedelta(hours=24)
    time_cutoff_str = time_cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"Looking for finished collision runs since {time_cutoff_str}...\n")

    q_run = omsapi.query("runs")
    q_run.filter("sequence", "GLOBAL-RUN", "EQ")
    q_run.filter("end_time", time_cutoff_str, "GE")
    q_run.sort("run_number", asc=False)
    q_run.paginate(1, 50)

    runs_data = q_run.data().json().get("data", [])

    valid_runs = []
    for r in runs_data:
        info = r["attributes"]
        trigger_mode = info.get("l1_hlt_mode", "").lower()
        if "collisions" in trigger_mode and info.get("end_time"):
            valid_runs.append(info)

    if not valid_runs:
        print("No finished collision runs found in the last 24 hours.")
        return

    print("DATA QUALITY FEEDBACK:")

    for run_info in valid_runs:
        run_number = run_info.get("run_number")
        fill_number = run_info.get("fill_number")
        trigger_key = run_info.get("l1_key_stripped")

        q_ls = omsapi.query("lumisections")
        q_ls.filter("run_number", run_number, "EQ")
        q_ls.paginate(1, 5000)
        ls_data = q_ls.data().json().get("data", [])

        valid_ls = [ls["attributes"] for ls in ls_data if ls["attributes"].get("delivered_lumi", 0) > 0]
        if not valid_ls:
            valid_ls = [ls["attributes"] for ls in ls_data]

        l1_dict = {}
        q_l1 = omsapi.query("l1triggerrates")
        q_l1.filter("run_number", run_number, "EQ")
        q_l1.custom("group[granularity]", "lumisection")
        page = 1
        while True:
            q_l1.paginate(page, 5000)
            l1_data = q_l1.data().json().get("data", [])
            if not l1_data: break
            for item in l1_data:
                attr = item["attributes"]
                ls_num = attr.get("first_lumisection_number", attr.get("lumisection_number"))
                pre_rate = attr.get("total_before_deadtime", {}).get("rate", 0)
                post_rate = attr.get("l1a_total", {}).get("rate", 0)
                l1_dict[ls_num] = {"pre": pre_rate / 1000.0, "post": post_rate / 1000.0}
            if len(l1_data) < 5000: break
            page += 1

        dt_dict = {}
        q_dt = omsapi.query("deadtimes")
        q_dt.filter("run_number", run_number, "EQ")
        q_dt.custom("group[granularity]", "lumisection")
        page = 1
        while True:
            q_dt.paginate(page, 5000)
            dt_data = q_dt.data().json().get("data", [])
            if not dt_data: break
            for item in dt_data:
                attr = item["attributes"]
                ls_num = attr.get("first_lumisection_number", attr.get("lumisection_number"))
                total_dt = attr.get("overall_total_deadtime", {}).get("percent", 0.0)
                bactive_dt = attr.get("beamactive_total_deadtime", {}).get("percent", 0.0)
                dt_dict[ls_num] = {"total": total_dt, "bactive": bactive_dt}
            if len(dt_data) < 5000: break
            page += 1

        hlt_dict = defaultdict(lambda: {"physics": 0.0, "scouting": 0.0, "parking": 0.0})
        q_hlt = omsapi.query("streams-summed-per-lumisection")
        q_hlt.filter("run_number", run_number, "EQ")
        page = 1
        while True:
            q_hlt.paginate(page, 5000)
            data_list = q_hlt.data().json().get("data", [])
            if not data_list: break
            for item in data_list:
                attr = item["attributes"]
                ls_num = attr.get("lumisection_number")
                if not ls_num: continue
                name = attr.get("stream", "").lower()
                rate_hz = attr.get("rate")
                if rate_hz is None:
                    accepted_count = attr.get("accepted", 0)
                    rate_hz = accepted_count / 23.3104
                rate_khz = rate_hz / 1000.0
                if "physics" in name:
                    hlt_dict[ls_num]["physics"] += rate_khz
                elif "scouting" in name:
                    hlt_dict[ls_num]["scouting"] += rate_khz
                elif "parking" in name:
                    hlt_dict[ls_num]["parking"] += rate_khz
            if len(data_list) < 5000: break
            page += 1

        blocks = []
        current_block = None
        for ls in sorted(valid_ls, key=lambda x: x.get("lumisection_number", 0)):
            ls_num = ls.get("lumisection_number")
            ps_index = ls.get("prescale_index", 0)
            raw_ps_name = ls.get("prescale_name")
            ps_name = str(raw_ps_name) if raw_ps_name else f"PS Index {ps_index}"
            if current_block is None:
                current_block = {"start": ls_num, "end": ls_num, "ps_index": ps_index, "ps_name": ps_name, "ls_nums": [ls_num], "ls_data": [ls]}
            elif ps_index == current_block["ps_index"] and ls_num == current_block["end"] + 1:
                current_block["end"] = ls_num
                current_block["ls_nums"].append(ls_num)
                current_block["ls_data"].append(ls)
            else:
                blocks.append(current_block)
                current_block = {"start": ls_num, "end": ls_num, "ps_index": ps_index, "ps_name": ps_name, "ls_nums": [ls_num], "ls_data": [ls]}
        if current_block:
            blocks.append(current_block)

        run_info["_blocks"] = []
        for b in blocks:
            n_ls = len(b["ls_nums"])
            avg_pu = sum(ls.get("pileup", 0) for ls in b["ls_data"]) / n_ls if n_ls else 0
            l1_pre_sum, l1_post_sum = 0, 0
            dt_sum, dt_bact_sum = 0, 0
            hlt_phys_sum, hlt_scout_sum, hlt_park_sum = 0, 0, 0
            rates_count, dt_count = 0, 0
            for ls_num in b["ls_nums"]:
                if ls_num in l1_dict:
                    l1_pre_sum += l1_dict[ls_num]["pre"]
                    l1_post_sum += l1_dict[ls_num]["post"]
                    rates_count += 1
                if ls_num in dt_dict:
                    dt_sum += dt_dict[ls_num]["total"]
                    dt_bact_sum += dt_dict[ls_num]["bactive"]
                    dt_count += 1
                if ls_num in hlt_dict:
                    hlt_phys_sum += hlt_dict[ls_num]["physics"]
                    hlt_scout_sum += hlt_dict[ls_num]["scouting"]
                    hlt_park_sum += hlt_dict[ls_num]["parking"]

            avg_l1_pre  = l1_pre_sum  / rates_count if rates_count else 0
            avg_l1_post = l1_post_sum / rates_count if rates_count else 0
            avg_dt      = dt_sum      / dt_count    if dt_count    else 0
            avg_dt_bact = dt_bact_sum / dt_count    if dt_count    else 0
            avg_hlt_phys  = hlt_phys_sum  / n_ls if n_ls else 0
            avg_hlt_scout = hlt_scout_sum / n_ls if n_ls else 0
            avg_hlt_park  = hlt_park_sum  / n_ls if n_ls else 0

            block_result = {
                "ps_name": b["ps_name"], "start": b["start"], "end": b["end"],
                "avg_pu": avg_pu, "avg_l1_pre": avg_l1_pre, "avg_l1_post": avg_l1_post,
                "avg_dt": avg_dt, "avg_dt_bact": avg_dt_bact,
                "avg_hlt_phys": avg_hlt_phys, "avg_hlt_scout": avg_hlt_scout, "avg_hlt_park": avg_hlt_park,
            }
            run_info["_blocks"].append(block_result)

            print(f"LS {b['start']}-{b['end']}, {b['ps_name']}, PU ~{avg_pu:.1f}")
            print(f"Total L1 rate: {avg_l1_pre:.1f} kHz (pre-DT), {avg_l1_post:.1f} kHz (post-DT), DT ~ {avg_dt:.1f}%, Beam active DT ~ {avg_dt_bact:.1f}%")
            print(f"HLT rates: Physics ~ {avg_hlt_phys:.1f} kHz, Parking ~ {avg_hlt_park:.1f} kHz, Scouting ~ {avg_hlt_scout:.1f} kHz")
        print("")

    # -------------------------------------------------------
    # BUILD HTML REPORT FILE
    # -------------------------------------------------------
    seen_fills = []
    fills_runs = defaultdict(list)
    for run_info in valid_runs:
        fn = run_info.get("fill_number")
        if fn not in fills_runs:
            seen_fills.append(fn)
        fills_runs[fn].append(run_info)

    def is_meaningful_block(b):
        """Skip blocks that are clearly junk: unnamed PS, zero rates, or only 1 LS."""
        if b["ps_name"].startswith("PS Index"):
            return False
        n_ls = b["end"] - b["start"] + 1
        if n_ls < 2:
            return False
        if b["avg_l1_pre"] == 0 and b["avg_l1_post"] == 0:
            return False
        return True

    html_body = ""

    for fill_number in seen_fills:
        runs = fills_runs[fill_number]
        fill_url = f"https://cmsoms.cern.ch/cms/fills/report?cms_fill={fill_number}"

        html_body += f'<p><strong><a href="{fill_url}">Fill {fill_number}</a></strong></p>\n<ul>\n'

        for run_info in runs:
            run_number = run_info.get("run_number")
            trigger_key = run_info.get("l1_key_stripped", "unknown_key")
            run_url = f"https://cmsoms.cern.ch/cms/runs/report?cms_run={run_number}"

            blocks = run_info.get("_blocks", [])
            good_blocks = [b for b in blocks if is_meaningful_block(b)]

            if not good_blocks:
                html_body += f'  <li><strong><a href="{run_url}">Run {run_number}</a></strong> (trigger key: {trigger_key}). No meaningful data.</li>\n'
                continue

            html_body += f'  <li><strong><a href="{run_url}">Run {run_number}</a></strong> (trigger key: {trigger_key}).\n    <ul>\n'

            for b in good_blocks:
                n_ls = b["end"] - b["start"] + 1
                html_body += f'''\
      <li><strong>{b["ps_name"]}</strong> (LS {b["start"]}–{b["end"]}, {n_ls} LS, PU ~{b["avg_pu"]:.1f})
        <ul>
          <li>Total L1T rate ~{b["avg_l1_pre"]:.1f} kHz (pre-dt), ~{b["avg_l1_post"]:.1f} kHz (post-dt)</li>
          <li>Total dt ~{b["avg_dt"]:.1f}%, beam-active dt ~{b["avg_dt_bact"]:.1f}%</li>
          <li>HLT Physics* ~{b["avg_hlt_phys"]:.1f} kHz, Scouting ~{b["avg_hlt_scout"]:.1f} kHz, Parking ~{b["avg_hlt_park"]:.1f} kHz</li>
        </ul>
      </li>\n'''

            html_body += "    </ul>\n  </li>\n"

        html_body += "</ul>\n\n"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>HLT Shift Report</title>
<style>
  body {{
    font-family: Arial, sans-serif;
    font-size: 14px;
    max-width: 860px;
    margin: 40px auto;
    padding: 20px;
    background: #f9f9f9;
  }}
  .report-box {{
    background: white;
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 24px 32px;
    margin-bottom: 20px;
  }}
  .instructions {{
    background: #e8f4fd;
    border-left: 4px solid #2196F3;
    padding: 12px 16px;
    margin-bottom: 24px;
    border-radius: 0 4px 4px 0;
    font-size: 13px;
  }}
  a {{ color: #1a0dab; }}
</style>
</head>
<body>
<div class="instructions">
  <strong>Instructions:</strong>
  <ol>
    <li>Review the rates below. <strong>Important:</strong> Always verify these values by viewing the diagnostic plots directly on <a href="https://cmsoms.cern.ch/" target="_blank">OMS</a>.</li>
    <li>Select all content in the box below (use the button or Cmd+A / Ctrl+A inside the box).</li>
    <li>Copy (Cmd+C) and paste directly into the editor field on the RCTools page.</li>
  </ol>
</div>
<div class="report-box" id="report" contenteditable="true">
{html_body}
</div>
<button onclick="selectReport()" style="padding:8px 18px;font-size:14px;cursor:pointer;">
  Select all (then Cmd+C to copy)
</button>
<script>
function selectReport() {{
  const el = document.getElementById('report');
  const range = document.createRange();
  range.selectNodeContents(el);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
}}
</script>
</body>
</html>"""

    report_path = "hlt_shift_report.html"
    with open(report_path, "w") as f:
        f.write(html)
    print(f"\nShift report written to: {report_path}")
    print("1. Open it in a browser.")
    print("2. Review rates and VERIFY with plots on OMS: https://cmsoms.cern.ch/")
    print("3. Click 'Select all', copy, and paste into RCTools.")

if __name__ == "__main__":
    generate_recent_reports()

