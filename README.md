# HLT Shift Report Generator

This tool queries relevant rates from [OMS](https://cmsoms.cern.ch/) using the [oms-api-client](https://gitlab.cern.ch/cmsoms/oms-api-client/-/tree/master?ref_type=heads) and generates a formatted report for HLT shifts. A personal example of such an output can be found [here](https://jprendi.web.cern.ch/cms-hlt-shift-report/). 

## ⚠️ Important Note
**This tool is a helper for summarizing rates, but it does NOT replace manual plot inspection.**
Always view the full diagnostic plots directly on **[OMS](https://cmsoms.cern.ch/)** to ensure data quality and identify potential issues that automated rate summaries might miss.

# Use on lxplus via web.cern.ch

1. Clone the repository into your `www` (or equivalent) directory on lxplus:
   ```bash
   git clone git@github.com:jprendi/cms-hlt-shift-report.git
   cd cms-hlt-shift-report
   ```
2. Install the OMS API client:
   ```bash
   git clone ssh://git@gitlab.cern.ch:7999/cmsoms/oms-api-client.git
   ```
3. Generate the latest report:
   ```bash
   python3 report-generator.py
   ```
4. View the report by navigating to your CERN website URL (e.g., `https://<your-username>.web.cern.ch/cms-hlt-shift-report/`). The `index.php` provides a browser interface for the report and any generated plots.
5. Review the rates and **verify them by checking the corresponding plots on [OMS](https://cmsoms.cern.ch/)**.
6. Use the **"Select all"** button in the report to highlight the content, then copy and paste it into the RCTools shift report editor.

# Use on lxplus without web.cern.ch

1. Clone the repository on lxplus:
   ```bash
   git clone git@github.com:jprendi/cms-hlt-shift-report.git
   cd cms-hlt-shift-report
   ```
2. Install the OMS API client:
   ```bash
   git clone ssh://git@gitlab.cern.ch:7999/cmsoms/oms-api-client.git
   ```
3. Generate the latest report:
   ```bash
   python3 report-generator.py
   ```
4. View the report:
   - Transfer the generated `hlt_shift_report.html` to your local machine (e.g., via `scp` or CERNBox).
   - Open the `hlt_shift_report.html` file in your local web browser.
5. Review the rates and **verify them by checking the corresponding plots on [OMS](https://cmsoms.cern.ch/)**.
6. Use the **"Select all"** button in the report to highlight the content, then copy and paste it into the RCTools shift report editor.
