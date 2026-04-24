# HLT Shift Report Generator

This tool queries relevant rates from [OMS](https://cmsoms.cern.ch/) using the [oms-api-client](https://gitlab.cern.ch/cmsoms/oms-api-client/-/tree/master?ref_type=heads) and generates a formatted report for HLT shifts.

## ⚠️ Important Note
**This tool is a helper for summarizing rates, but it does NOT replace manual plot inspection.**
Always view the full diagnostic plots directly on **[OMS](https://cmsoms.cern.ch/)** to ensure data quality and identify potential issues that automated rate summaries might miss.

## Setup
The **intended usage** of this tool is within your `web.cern.ch` (or similar) user area. This allows you to view the generated reports and diagnostic plots directly in a browser via a stable URL.

### Option 1: web.cern.ch (Recommended)
1. Clone the repository into your `www` (or equivalent) directory:
   ```bash
   git clone git@github.com:jprendi/cms-hlt-shift-report.git
   cd cms-hlt-shift-report
   ```

2. Install the OMS API client:
   ```bash
   git clone ssh://git@gitlab.cern.ch:7999/cmsoms/oms-api-client.git
   ```

### Option 2: Local or Remote (lxplus)
If you prefer to run the script locally or on `lxplus` without a web server:
1. Follow the same cloning and installation steps as above.
2. After generating a report, you will need to transfer `hlt_shift_report.html` to your local machine (e.g., via `scp` or CERNBox) to open it in a browser.

## Usage
1. Generate the latest report:
   ```bash
   python3 report-generator.py
   ```

2. View the report:
   - **web.cern.ch:** Navigate to your CERN website URL (e.g., [https://jprendi.web.cern.ch/cms-hlt-shift-report/](https://jprendi.web.cern.ch/cms-hlt-shift-report/)). The `index.php` provides a nice browser for the report and any generated plots.
   - **Local:** Open the resulting `hlt_shift_report.html` directly in your browser.
   - **lxplus:** Download the `hlt_shift_report.html` file to your computer and open it.
3. Review the rates and **check the corresponding plots on OMS**.
4. Use the "Select all" button in the report to copy the content and paste it into the RCTools shift report editor.
