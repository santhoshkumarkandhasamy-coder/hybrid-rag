"""Dump a sheet: values (mode v) or formula + value (mode f).
Usage: python3 -I dump_sheet.py book.xlsx <sheet> <row_from> <row_to> [v|f]"""
import openpyxl,sys,warnings
warnings.filterwarnings('ignore')
f=sys.argv[1]; s=sys.argv[2]; r0=int(sys.argv[3]); r1=int(sys.argv[4]); mode=sys.argv[5] if len(sys.argv)>5 else 'v'
wv=openpyxl.load_workbook(f,data_only=True)[s]; wf=openpyxl.load_workbook(f)[s]
for r in range(r0,r1+1):
    out=[]
    for c in wf[r]:
        v=c.value
        if v is None or v=='': continue
        vv=wv[c.coordinate].value
        if isinstance(vv,float): vv=round(vv,2)
        if isinstance(v,str) and v.startswith('=') and mode=='f': out.append(f"{c.coordinate}={vv}{{{v[:70]}}}")
        else: out.append(f"{c.coordinate}:{str(vv).replace(chr(10),' ')[:60]}")
    if out: print(r,' | '.join(out))
