# HLT Shift Report Generator

This tool queries relevant rates from [OMS](https://cmsoms.cern.ch/) using the [oms-api-client](https://gitlab.cern.ch/cmsoms/oms-api-client/-/tree/master?ref_type=heads) and generates a formatted report for HLT shifts.

## ⚠️ Important Note
**This tool is a helper for summarizing rates, but it does NOT replace manual plot inspection.**
Always view the full diagnostic plots directly on **[OMS](https://cmsoms.cern.ch/)** to ensure data quality and identify potential issues that automated rate summaries might miss.

## Setup
It is recommended to set up this tool in your `web.cern.ch` (or similar) user area so you can view the generated reports directly in a browser.

1. Clone the repository:
   ```bash
   git clone git@github.com:jprendi/cms-hlt-shift-report.git
   cd cms-hlt-shift-report
   ```

2. Install the OMS API client:
   ```bash
   git clone ssh://git@gitlab.cern.ch:7999/cmsoms/oms-api-client.git
   ```

## Usage
1. Generate the latest report:
   ```bash
   python3 report-generator.py
   ```

2. Open the resulting `hlt_shift_report.html` (or your website URL) in a browser.
3. Review the rates and **check the corresponding plots on OMS**.
4. Use the "Select all" button in the report to copy the content and paste it into the RCTools shift report editor.
