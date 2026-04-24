# Quick start

This tool queries relevant rates from OMS using the (oms-api-client)[https://gitlab.cern.ch/cmsoms/oms-api-client/-/tree/master?ref_type=heads].

It is best to set up this area in your e.g. `web.cern.ch` area, where you can view it on a website directly.

Setup is as followed:
```
git clone git@github.com:jprendi/cms-hlt-shift-report.git
cd cms-hlt-shift-report
git clone ssh://git@gitlab.cern.ch:7999/cmsoms/oms-api-client.git
python3 report-generator.py
```
and then go onto your website and view the html file, and copy paste. It is important to note to still view the plots on OMS!
