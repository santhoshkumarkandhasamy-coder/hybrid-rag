---
name: rfs-preparation
description: Prepare or revise Restated Financial Statements (RFS / Restated Summary Statements under SEBI ICDR - Annexures I to VI) in Excel for an IPO, from trial balances, audited financial statements, FA register, actuarial gratuity reports, ITRs, computation of income, MSME interest workings, sanction letters, ageing and capital-structure documents, including a stub (interim) period. Use whenever the user uploads an RFS workbook or a company's supporting documents and asks to prepare / restate / add a stub period / "give the final RFS in the same format".
---

# RFS preparation - house workflow and format

Built from the full Techfruits Solutions engagement (draft RFS FY24-FY26 -> v1..v6 -> stub Sep-26 ->
21-point format revision -> final file approved by the user). This file keeps the **process, rules and
format** only. **Never carry one client's data into another engagement.** The reference RFS (e.g. KMC
Aluminium Ltd, final with UDIN) is used for **format only - never its data**.

The user is a CA, writes in Tanglish (Tamil + English). Reply in Tanglish, short, tables for numbers.

---------------------------------------------------------------------------------------------------
## A. How the user works (interaction pattern)

1. First message: draft RFS + a few documents, "documents one by one upload pandren, full read panite final
   file kodu". Then documents arrive in batches with "do that remaining work".
2. **Every batch:** read every document completely (all sheets, hidden sheets, all PDF pages), apply what it
   supports, recalculate, verify, and send a new version (`..._Revised.xlsx`, `_v2`, `_v3` ...) with a summary:
   what changed per document (with a small Books vs Restated table where figures moved), impact on restated
   PAT / net worth, and a numbered list of ⚠️ points to confirm + pending documents.
3. When the user says "study this first and let me know before generating final output" - **do not deliver a
   file**. Analyse, try on a test copy, report numbered questions (with your proposal for each) and wait.
   Answers come back numbered ("1. <amount> 2. venam, reverse pannatha, add up pannu 3. ..."). If an answer is
   ambiguous, restate your understanding with the exact figures and ask once.
4. The user then sends a numbered change list (general + sheet-wise). Apply **all** of them in **one single
   output file**; arrange the order yourself. Final reply: point-by-point where each change is, judgment calls
   (where instructions conflicted with the data), and what is still pending from management.
5. Keep a **pending list in MasterData** (A47 onwards) and repeat open items in each reply until closed.

## B. Golden rules

1. Format from the reference, **numbers from our files only**.
2. **Notes linked, never typed.** BS / P&L note amounts are formulas to TB sheets, `Adj Entry RFS`, or an
   annexure. External figures (actuarial, ITR, sanction, ageing, MSME) are typed once in the annexure / input
   sheet as `=amount/MasterData!$B$15` and linked onward.
3. Restatements only through **dated journal entries in `Adj Entry RFS`** with narration + source reference;
   they flow to the year they relate to; effects before the first RFS year go to **opening reserves**.
4. Where the books passed a catch-up entry directly to reserves (prior-period gratuity, FA alignment credit),
   reverse it in the year booked and restate it in the years it belongs to.
5. Deferred tax at the 115BAA rate (22% x 1.1 x 1.04 = 25.168%) on timing restatements (depreciation,
   gratuity); none on MSME interest (Sec 23 MSMED - permanent).
6. Negatives in brackets everywhere; zero as "-".
7. Remove lines nil in all years, except rows of prescribed tables copied from the reference.
8. Every period-end must satisfy: TB balance 0, BS balances, PL/CFS ties, SOA restated = statements, all
   check cells 0, recalculation 0 errors. Previous-year figures must not move unless a change was intended -
   always report restated PAT / net worth before vs after.
9. Flag but don't silently fix management workings (e.g. MSME interest formula /183 instead of /365): ask
   which figure to use.
10. Never copy credentials found in client files into outputs.

## C. Inputs checklist (ask for what is missing, one by one)

| Document | Used for |
|---|---|
| Draft RFS workbook, reference RFS | starting point / format |
| TB per year + stub TB (Tally export) | TB sheets, all notes |
| Audited FS per year (Excel: BS, P&L, Notes, Computation, Deferred tax, Additional Info/RPT, MSME, ageing, Ratios) + audit reports PDF | regrouping to audited classification, RPT, tax, non-adjusting items |
| FA register / FA details (incl. next-year sheet for stub) | depreciation restatement, Notes_PPE, SAP useful-life table |
| Capital structure (authorised history, allotments, transfers, shareholding), COIs incl. conversion to public co. | Equity notes, MasterData CIN/name, SAP_4 |
| Actuarial AS 15 reports every year | gratuity restatement + disclosure, current/non-current split |
| MSME interest computation per year (+ stub) | MSME restatement, Sec 22 disclosure |
| ITR acknowledgements + computation of income | current tax restatement, tax shelter |
| Sanction letters + repayment schedules (all lenders) | Borrowing Terms, secured/unsecured, current maturities, security notes, PG in RPT |
| Debtor / creditor ageing each year end + stub | ageing schedules |
| Peer-review certificate + engagement partner, UDIN, date, place | signature blocks (check the certificate is addressed to *this* company) |
| Signatories (2 directors + CFO + CS with DIN), independent directors (DIN, date), sitting fees | MasterData, signatures, RPT |
| Closing stock for each period (stub!) | inventories, P&L |

## D. Engagement stages (what was done, do the same for the next company)

1. **FA register -> depreciation restatement.** Rebuild WDV / depreciation per register (Schedule II) per year,
   compare with books; opening WDV difference -> opening reserves; year differences -> that year's P&L;
   write-offs at register WDV; reverse any books' alignment credit; DT on each. Sheets `FA Register`
   (copy, formulas intact) and `FA Restatement` (class-wise summary, reconciliation, Part C class-wise
   gross / acc dep / WDV per year feeding Notes_PPE, stub columns).
2. **Capital structure.** Shareholder register vs transfers; authorised capital history table in MasterData
   (use what the user confirms - e.g. "no change since incorporation" overrides the documents); promoter and
   >5% holdings; SAP_4 incorporation date, conversion date, new CIN.
3. **Audit reports.** Opinion, CARO applicability, litigation -> Annexure V non-adjusting items (report dates,
   UDIN, FRN), audit-trail disclosure, statutory auditor block in MasterData.
4. **Ageing.** Totals must equal BS for each year; credit balances in debtors -> advance from customers;
   ignore hidden sheets belonging to other companies; flag inconsistent buckets year-on-year and old
   unprovided debtors (IPO due-diligence risk).
5. **Gratuity.** Split DBO by year from actuarial reports; amount up to the opening date -> opening reserves;
   year expense -> P&L; books' prior-period debit to reserves reversed; current portion from the report to
   short-term provisions; if reports of different years disagree, follow the series used in the audited FS /
   latest report and disclose; reconcile books expense vs actuarial (e.g. direct gratuity payment).
6. **MSME interest.** Use management workings per year; provide unprovided interest year-wise as finance cost
   with liability "Interest accrued on dues to MSME"; no DT; Sec 22 disclosure; for the stub keep earlier
   years' liability and add only the period expense (books' write-back reversed).
7. **Borrowings / sanction letters.** `Borrowing Terms` note (lender, facility, sanction date, limit, rate,
   tenure / repayment, security, guarantees, outstanding per period; totals tie to Notes 5 & 8);
   secured vs unsecured by actual security (PDC/NACH + PG only = unsecured); current maturities from repayment
   schedules -> short-term borrowings; short tenure loans (e.g. 6 instalments) -> short-term; security text
   under Note 8; directors' PG / mortgage in RPT; flag BG limits vs "contingent liabilities Nil".
8. **Current tax -> ITR.** Restate current tax to tax as per return when the books' excess is never reversed;
   Tax Computation return details block.
9. **Audited FS alignment.** Compare totals line by line with RFS TB; align classification (current maturities,
   gratuity split, regroupings); RPT from audited FS.
10. **Computation of income.** Fill tax shelter (IT depreciation, 43B(h), 40(a)(ia), 40A(7), write-offs,
    allowances) until computed taxable income = ITR total income (difference 0).
11. **Peer-review auditor** into MasterData (signature blocks are formulas).
12. **Reference format (KMC).** Notes_PPE per reference: for each period Gross block (opening, additions,
    deletions, closing), accumulated depreciation (opening, for the year, on deletions, closing), net block;
    (a) PPE classes, (b) intangibles, total; (c) CWIP and (d) intangible assets under development movement +
    ageing; checks net block = books + restatement and depreciation = Note 26. SAP_4 useful-life / rate table,
    impairment policy. Borrowing Terms as a separate note, then Capitalisation, Additional Disclosures.
13. **Stub period.** Add a column *before* the latest FY in every annexure (LibreOffice column insert so all
    references shift), new `TB <stub>` sheet mapped like earlier years (reuse previous mapping by ledger name,
    explicit mapping for new ledgers, exclude duplicate ledgers / header rows, memo row for current-period
    profit since Tally TB has none), stub restatements (pro-rata depreciation on additions from purchase date,
    exclude assets bought after the stub date, DT, current tax on restated profit, MSME period expense,
    sale of assets: deletion + profit in other income, CFS add-back / proceeds), closing stock input in
    MasterData, stub ratios not annualised, stub ageing / interim actuarial / director-wise remuneration
    as pending inputs.
14. **Conversion certificate.** New CIN everywhere (MasterData), name "Limited", "formerly known as ...",
    SAP_4 background, events-after-reporting-period disclosure.
15. **Final format revision** - the 21 points below.

## E. The 21 points (final approved format) and how to implement them

1. **Negatives in brackets** - whole workbook: `_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)`,
   counts `_(* #,##0_);_(* (#,##0);_(* "-"??_);_(@_)`, `0.00%;(0.00%);"-"`, `0.00;(0.00);"-"`; General cells
   holding negatives/decimals -> amount format.
2. **Gratuity in short-term provisions linked from the gratuity annexure**; figures typed only in the annexure
   (current / non-current table); long-term = TB total + adj - current. Rule for all notes: link to TB or
   annexure, never typed.
3. **Auditor signing partner details** -> MasterData (firm, FRN, PRC, partner, M.No.).
4. **Four signatories**: 2 directors, CFO, CS -> MasterData table; signature blocks in BS, PL, CFS:
   left auditor (For firm / Chartered Accountants / FRN / PRC / Sd/- partner / Partner / M.No. / UDIN),
   right "For and on behalf of the Board of Directors of <company>", CIN, Director (DIN), Director (DIN),
   CFO & Director (DIN), Company Secretary, Place, Date.
5. **Equity note: only opening balance + restated profit** for the year (no restatement / books-reserve lines).
6. **SOA profit-reconciliation notes precise like the reference**: lettered lines (A Depreciation, B Gratuity,
   C MSME interest, D Current tax, E Deferred tax...) and under "Notes for reconciliation of profit" a bold
   "A) <item>:" heading + one paragraph each ("During the preparation of the Restated Financial Statements,
   it was observed that ... adjusted in the respective years").
7. **Shareholders' funds reconciliation item-wise** (PPE/depreciation, gratuity, MSME interest, income tax,
   deferred tax, with letters) incl. a column for the opening date; notes A)-E); never "adjustments directly
   routed through reserves".
8. **Authorised capital** as the user confirms (e.g. unchanged since incorporation) + a note line.
9. **Deferred tax disclosure as reference**: Opening / Add: credit (expense) for the year / Closing;
   components (depreciation & other timing differences; expenses disallowed - gratuity); net; note.
10. **Trade payables ageing + MSME disclosure exactly as reference**: `<n>(a) Dues to Micro and Small
    Enterprises - Disclosure as per Section 22 of the MSMED Act, 2006` with a) principal / interest, b), c),
    d), e) (boxed); `<n>(b)..` ageing per period: Particulars (merged 2 rows) | "Outstanding for following
    periods from due date of payment" over <1 yr, 1-2, 2-3, >3, Total; rows (A) MSME, (B) Others,
    (C) Disputed MSME, (D) Disputed others; Total; boxed.
11. **Trade receivables ageing exactly as reference**: <6 months, 6 m-1 yr, 1-2, 2-3, >3, Total; rows
    Undisputed good / Undisputed doubtful / Disputed good / Disputed doubtful / Less: allowance; Total; main
    note uses the same five categories.
12. **Remove lines nil in all years** (e.g. other current assets - others, DTL, exceptional items, share issue
    proceeds in CFS, unused auditor lines) - not rows of prescribed tables.
13. **Other income broken into separate lines** from TB ledgers (interest on FD, interest on IT refund, discount
    received, creditors written back, forex gain, profit on sale of PPE, government incentives); interest
    rows feed CFS interest income / received.
14. **Formatting same as reference**: Times New Roman 10; title rows B2:B4 bold centred merged; B5 bold; B6
    italic units line; note no. bold in B, title bold in C; header row top+bottom border, bold, centred,
    wrapped (height 28, 40 for stub "For the period ended"); totals bold with top+bottom border; boxed grids
    for ageing / MSME / ratio tables; long text merged and justified; gridlines off; A4 portrait fit-to-width;
    print area excludes check columns; comparative opening-date column grey italic.
15. **RPT as per audited financials** (pull from "Additional Info"); KMP list incl. CFO, CS, independent
    directors; transactions grouped with totals; outstanding balances; guarantees; footnotes where FS was
    incomplete / not updated (use books then).
16. **Remove a party wrongly shown in the audited FS** when the user says so; keep the related amount where
    it belongs (e.g. in the actual director's loan account) with a footnote.
17. **Gratuity disclosure as reference with report figures**: a) assumptions (discount, salary escalation,
    attrition + graded withdrawal, retirement, funding, vesting, mortality, employees), b) change in PV of
    DBO, c) actuarial gain/loss, d) P&L expense (+ direct payments = Note 24), e) BS reconciliation,
    f) current/non-current, g) experience adjustments, h) sensitivity, i) plan assets; notes (derived figures,
    stub without valuation, Labour Codes / new wage code status).
18. **Tax computation as reference, nil lines dropped**: PBT (A); rate; income considered separately (B);
    permanent differences (C); timing differences - book vs IT depreciation, disallowances and allowances (D);
    net (E); income from other sources (F); taxable income (G); tax; vs current tax; then return/computation
    details; notes (115BAA/no MAT, sources, stub basis).
19. **Accounting ratios as reference**: revenue (A), PAT (B), tax / depreciation / interest, EBITDA, margin,
    net worth, RONW, shares, weighted shares (bonus-adjusted), EPS, NAV, current assets / liabilities, current
    ratio, notes (formulas, definitions, no bonus, stub not annualised). EPS in Notes_P&L links here.
20. **Analytical ratios as reference**: one boxed block per period vs previous: Ratio | Numerator |
    Denominator | current | previous | % variance | reason (>25%); 11 Schedule III ratios; averages via a
    helper table outside the print area; quantified reasons; stub flow ratios "not comparable - not
    annualised"; first-year comparatives without prior P&L "N.A.".
21. **Additional disclosures as reference + latest SEBI ICDR / Schedule III**: title deeds, revaluation,
    loans to promoters/directors/KMP/RP (table), benami, current-asset statements to banks, wilful defaulter,
    struck-off companies, charges, layers, schemes, utilisation of borrowed funds & premium (A/B), borrowings
    used for purpose, auditor payments (table), undisclosed income, imports/forex (table), crypto, CSR,
    CWIP/IAUD ageing ref, segment, audit trail (Rule 3(1)), dividend, events after reporting period,
    Labour Codes, cross-refs to the other ICDR notes.

## F. Workbook structure

Sheets: `MasterData, BS_1, PL_2, CFS_3, SAP_4, SOA_5, Notes_Equity & Reserves, Notes_Liabilities, Notes_PPE,
Notes_Assets, Notes_P&L, RPT, Gratuity and contingencies, Tax Computation, Accounting ratios, Analytical Ratios,
Borrowing Terms, Capitalisation, Additional Disclosures, TB <stub>, TB <FY3>, TB <FY2>, TB <FY1>, Debtor Ageing,
Creditor Ageing, Shareholder Register, Adj Entry RFS, FA Restatement, FA Register`.
Annexure I BS, II PL, III CFS, IV SAP (background + policies), V SOA, VI notes.
Columns: stub first, latest FY -> earliest FY, then opening BS date (comparative, grey italic). Notes: C label,
D..H periods; checks (TNR 8 italic) right of the table. Header cells are formulas on MasterData dates.
MasterData: CIN, name, formerly known as, address, authorised capital (=SUM of history), FV, bonus factor,
dates, scale B15 = 100000 (Rs. lakhs), closing stock inputs, tax rate, peer-review auditor block, statutory
auditors, signatory table (Sr, DIN, Name, Designation, Category, Signatory), capital history, pending list.
TB sheets: A ledger, F BS/P&L, G group = note caption, H signed amount, I lakhs; notes `SUMIF(G, caption, I)`,
ledger lines `SUMIFS(I, G, group, A, ledger)`. `Adj Entry RFS`: A date, B particulars, C master (= caption),
D BS/P&L, E Dr, F Cr, H source; notes add `SUMIFS` by master with the period window (P&L) or cumulative to
the period end (BS).

## G. Tooling (scripts/ in this skill)

- `dump_reference.py` - read-only dump of huge reference workbooks (normal load times out).
- `dump_sheet.py` - values / formulas of a sheet range.
- `refscan.py` - formulas pointing at rows you will delete (fix first; explicit `SUM(D17,D18)` -> ranges).
- `lorows.py` - insert / delete rows (or adapt for columns) through LibreOffice so all references update.
- `h7.py` - openpyxl helpers: `put, text, box, hline, clear, find, tb, adj_win, adj_cum, as_at, for_per`,
  number formats. Locate rows by label with `find` after any structural change.
- Recalculate with the xlsx skill's `recalc.py` (0 errors). Render key sheets (values-only copy ->
  `soffice --convert-to pdf` -> `pdftoppm`) and look at them before delivering.
- openpyxl pitfalls: column dimension groups (e.g. F:I) override single widths - normalise; merged cells
  must be unmerged before writing; dicts of f-strings evaluate eagerly.

## H. Things to always check and flag

Peer-review certificate addressed to another company; reports disagreeing across years; ITR total income vs
computed; BG limits vs contingent liabilities Nil; old unprovided debtors / bank covenants; audited FS of the
latest year carrying forward last year's notes (RPT, imports) unchanged; new loans' current / non-current
split and processing fees; stub closing stock missing (stub shows a fake loss); management formula errors
(days /183 vs /365); large unexplained stub transactions (e.g. NBFC Dr/Cr with nil closing); duplicate
ledgers in Tally exports; parties wrongly described in audited FS.

## I. Deliverable

One file `<Company>_RFS_<stub>_FY..-FY.._Final.xlsx` (recalculated), sent with the Tanglish summary:
changes point-by-point, restated PAT / net worth per period, judgment calls, pending items from management.
