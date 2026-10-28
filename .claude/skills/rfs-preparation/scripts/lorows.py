"""Insert / delete whole rows through LibreOffice so every formula reference in the workbook is updated.
Usage: python3 lorows.py in.xlsx out.xlsx ops.json
ops.json: [["del","BS_1",18,1], ["ins","Notes_Assets",41,3], ...]  (1-based row, count; list ops bottom-up per sheet)"""
import sys, subprocess, tempfile, shutil, json, glob
from pathlib import Path
for d in glob.glob('/root/.claude/skills/**/xlsx/scripts', recursive=True):
    sys.path.insert(0, d)
from office.soffice import get_soffice_env, run_soffice
src, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
ops = json.loads(Path(sys.argv[3]).read_text())
shutil.copy(src, out)
lines = ['Sub InsertStub()', '  Dim doc As Object, sh As Object', '  doc = ThisComponent']
for op, s, r, n in ops:
    fn = 'insertByIndex' if op == 'ins' else 'removeByIndex'
    lines.append(f'  sh = doc.Sheets.getByName("{s}") : sh.Rows.{fn}({r - 1}, {n})')
lines += ['  doc.calculateAll()', '  doc.store()', '  doc.close(True)', 'End Sub']
macro = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">\n'
         '<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">\n'
         + '\n'.join(lines).replace('&', '&amp;').replace('"', '&quot;') + '\n</script:module>')
with tempfile.TemporaryDirectory(prefix='lo_prof_') as prof:
    url = Path(prof).as_uri()
    run_soffice(['--headless', '--terminate_after_init', f'-env:UserInstallation={url}'], capture_output=True, timeout=60)
    (Path(prof) / 'user' / 'basic' / 'Standard' / 'Module1.xba').write_text(macro)
    cmd = ['timeout', '300', 'soffice', '--headless', '--norestore', f'-env:UserInstallation={url}',
           'vnd.sun.star.script:Standard.Module1.InsertStub?language=Basic&location=application', str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, env=get_soffice_env(), timeout=330)
    print('rc', r.returncode, r.stderr[-500:])
