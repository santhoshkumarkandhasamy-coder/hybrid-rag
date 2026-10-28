"""List formulas that point at rows you are about to delete (fix them first, or LibreOffice turns them into #REF!).
Usage: python3 -I refscan.py book.xlsx "{'BS_1':[18], 'PL_2':[20,21]}"
"""
import openpyxl,re,sys,ast
from openpyxl.utils import column_index_from_string as ci
wb=openpyxl.load_workbook(sys.argv[1])
targets=ast.literal_eval(sys.argv[2])  # {sheet:[rows]}
ref=re.compile(r"(?:'([^']+)'|([A-Za-z_][\w\.]*))!\$?([A-Z]{1,3})\$?(\d+)(?::\$?([A-Z]{1,3})\$?(\d+))?")
loc=re.compile(r"(?<![!\w\$'])\$?([A-Z]{1,3})\$?(\d+)(?::\$?([A-Z]{1,3})\$?(\d+))?(?![\w(!])")
for ws in wb:
    for row in ws.iter_rows():
        for c in row:
            v=c.value
            if not (isinstance(v,str) and v.startswith('=')): continue
            for m in ref.finditer(v):
                s=m.group(1) or m.group(2); r1=int(m.group(4)); r2=int(m.group(6) or r1)
                if s in targets and any(r1<=t<=r2 and (r1==r2 or t in (r1,r2)) for t in targets[s]) and s!=ws.title:
                    print('X',ws.title,c.coordinate,v[:100])
            if ws.title in targets:
                vv=ref.sub('',v)
                for m in loc.finditer(vv):
                    r1=int(m.group(2)); r2=int(m.group(4) or r1)
                    if any((r1==t or r2==t) for t in targets[ws.title]) and c.row not in targets[ws.title]:
                        print('L',ws.title,c.coordinate,v[:100])
