#!/usr/bin/env python3
import json, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

HERE=os.path.dirname(os.path.abspath(__file__))
DC=json.load(open(os.path.join(HERE,"..","data","dc_data_base.json")))
NEW=json.load(open(os.path.join(HERE,"..","data","dc_data_v2_new.json")))
years=["2019","2020","2021","2022","2023","2024"]

wb=Workbook()
HDR=PatternFill("solid",fgColor="2C3E50"); HF=Font(color="FFFFFF",bold=True,size=11)
SUB=PatternFill("solid",fgColor="D9E2F3"); BF=Font(bold=True)
thin=Side(style="thin",color="CCCCCC"); BORD=Border(thin,thin,thin,thin); CEN=Alignment(horizontal="center")
def hdrrow(ws,row,cols):
    for j,c in enumerate(cols,1):
        cell=ws.cell(row=row,column=j,value=c); cell.fill=HDR; cell.font=HF; cell.alignment=CEN; cell.border=BORD
def autos(ws):
    for col in ws.columns:
        m=max((len(str(c.value)) for c in col if c.value is not None),default=8)
        ws.column_dimensions[get_column_letter(col[0].column)].width=min(max(m+2,10),46)
def borders(ws,r0,r1,c1):
    for r in range(r0,r1+1):
        for c in range(1,c1+1): ws.cell(row=r,column=c).border=BORD

# Summary / annual
ws=wb.active; ws.title="Annual"
ws["A1"]="Cranial decompression (OPS 5-012.0) with a primary diagnosis of cerebral infarction (I63), Germany 2019-2024"
ws["A1"].font=Font(bold=True,size=12); ws.merge_cells("A1:H1")
ws["A2"]="Broad code-based proxy; NOT validated malignant MCA infarction. Unit = discharge episode."
ws["A2"].font=Font(italic=True,size=9); ws.merge_cells("A2:H2")
cols=["Year","Episodes","≥60 share %","In-hosp deaths","Mortality %","Primary-I63 episodes","I63 ≥60 %","Ratio per 1,000"]
hdrrow(ws,4,cols); r=5
Ndc=Ndeaths=Ni63=0
for y in years:
    b=DC["years"][y]["base_cohort"]; m=DC["years"][y]["mortality"]; den=NEW["years"][y]["denominator_all_I63"]
    N=b["episode_count"]; d=m["deaths_count"]; M=den["total"]; Ndc+=N; Ndeaths+=d; Ni63+=M
    ws.append([int(y),N,round(b["age_overlay_pct"]["ge60"],1),d,round(d/N*100,1),M,den["ge60_pct"],round(N/M*1000,2)])
row=["POOLED",Ndc,49.8,Ndeaths,round(Ndeaths/Ndc*100,1),Ni63,round(85.8,1),round(Ndc/Ni63*1000,2)]
for j,v in enumerate(row,1):
    c=ws.cell(row=r+6,column=j,value=v); c.fill=SUB; c.font=BF
borders(ws,4,r+6,len(cols)); autos(ws)

# Utilisation by age
ws2=wb.create_sheet("UtilisationByAge")
ws2["A1"]="Age-specific utilisation ratio: cohort episodes per 1,000 primary-I63 episodes (pooled 2019-2024)"; ws2["A1"].font=Font(bold=True,size=12)
hdrrow(ws2,3,["Age band","Cohort episodes","Primary-I63 episodes","Ratio per 1,000"])
util=[("<40",401,21042,19.1),("40-49",703,45060,15.6),("50-54",681,54727,12.4),("55-59",976,91790,10.6),
      ("60-64",1012,125710,8.0),("65-74",1354,330590,4.1),("75-79",250,215926,1.2),("80+",121,608071,0.2),
      ("ALL",5498,1494185,3.68),("<60",2761,212619,12.99),(">=60",2737,1281566,2.14)]
for i,(a,dc,i63,rr) in enumerate(util,4): ws2.append([a,dc,i63,rr])
borders(ws2,3,3+len(util),4); autos(ws2)

# Disposition, all six years
dkeys=[("transfer_06","Transfer to another hospital (06)"),("death_07","In-hospital death (07)"),
       ("rehabilitation_09","Rehabilitation facility (09)"),("nursing_10","Nursing facility (10)"),
       ("home_routine_other_hospice_residual","Home / routine / other / suppressed hospice (residual)")]
ws3=wb.create_sheet("Disposition")
ws3["A1"]="Discharge disposition, cranial-decompression episodes, by year"; ws3["A1"].font=Font(bold=True,size=12)
ws3["A2"]="Discharge-reason codes 06/07/09/10 return unsuppressed counts. Hospice (11) queried every year but suppressed (<4) or 0. Residual = N - (06+07+09+10) contains home/routine, all other unqueried reasons AND any suppressed hospice; hospice cannot be separated and is not a distinct row."
ws3["A2"].font=Font(italic=True,size=9); ws3.merge_cells("A2:J2")
hdrrow(ws3,4,["Disposition"]+years+["Pooled n","Pooled %"])
Nd=sum(NEW["years"][y]["disposition"]["_N"] for y in years)
for k,lab in dkeys:
    tot=sum(NEW["years"][y]["disposition"][k] for y in years)
    vals=[NEW["years"][y]["disposition"][k] for y in years]
    ws3.append([lab]+vals+[tot,round(tot/Nd*100,1)])
ws3.append(["Total episodes"]+[NEW["years"][y]["disposition"]["_N"] for y in years]+[Nd,100.0])
ws3.append([])
ws3.append(["Hospice (11) raw query result"]+[NEW["years"][y]["disposition"]["hospice_11_query"] for y in years])
# arithmetic audit
for y in years:
    d=NEW["years"][y]["disposition"]
    assert d["transfer_06"]+d["death_07"]+d["rehabilitation_09"]+d["nursing_10"]+d["home_routine_other_hospice_residual"]==d["_N"]
borders(ws3,4,5+len(dkeys),len(years)+3); autos(ws3)

# Subtype composition, all six years (group level)
gkeys=[("cerebral_arterial_I63.3-5","Cerebral arterial (I63.3-5)"),("precerebral_I63.0-2","Precerebral (I63.0-2)"),
       ("other_unspec_I63.8-9","Other/unspecified (I63.8-9)"),("venous_I63.6","Venous (I63.6)")]
def gv(y,k):
    v=NEW["years"][y]["subtype_composition"]["_groups"][k]; return v if isinstance(v,int) else 0
ws4=wb.create_sheet("SubtypeComposition")
ws4["A1"]="ICD-10-GM I63 subcode composition of the cohort, by year (grouped)"; ws4["A1"].font=Font(bold=True,size=12)
ws4["A2"]="Venous cerebral infarction (I63.6) is 0-7 episodes/year (<=0.7%); excluding it changes totals trivially."
ws4["A2"].font=Font(italic=True,size=9); ws4.merge_cells("A2:J2")
hdrrow(ws4,4,["Subtype group"]+years+["Pooled n","Pooled %"])
Ns=sum(NEW["years"][y]["subtype_composition"]["_N"] for y in years)
for k,lab in gkeys:
    tot=sum(gv(y,k) for y in years)
    vals=[NEW["years"][y]["subtype_composition"]["_groups"][k] for y in years]
    ws4.append([lab]+vals+[tot,round(tot/Ns*100,1)])
ws4.append(["Total episodes"]+[NEW["years"][y]["subtype_composition"]["_N"] for y in years]+[Ns,100.0])
ws4.append([])
ws4.append(["Cerebral-arterial share (%) by year"]+[round(gv(y,"cerebral_arterial_I63.3-5")/NEW["years"][y]["subtype_composition"]["_N"]*100,1) for y in years])
borders(ws4,4,5+len(gkeys),len(years)+3); autos(ws4)

# Denominators all years
ws5=wb.create_sheet("Denominators")
ws5["A1"]="All primary-I63 inpatient episodes (utilisation denominator) by year, with age distribution (%)"; ws5["A1"].font=Font(bold=True,size=12)
bands=["18-29","30-39","40-49","50-54","55-59","60-64","65-74","75-79","80+"]
hdrrow(ws5,3,["Year","Primary-I63 episodes","≥60 %"]+bands)
for y in years:
    den=NEW["years"][y]["denominator_all_I63"]
    ws5.append([int(y),den["total"],den["ge60_pct"]]+[den["age_bands_pct"][b] for b in bands])
borders(ws5,3,3+len(years),3+len(bands)); autos(ws5)

# AgeBand mortality (derived)
ws6=wb.create_sheet("AgeBandMortality")
ws6["A1"]="Reconstructed in-hospital mortality by native age band (pooled 2019-2024)"; ws6["A1"].font=Font(bold=True,size=12)
hdrrow(ws6,3,["Age band","Cohort episodes","Deaths (reconstructed)","Mortality % (reconstructed)"])
amb=[("<40",401,53,13.2),("40-49",703,134,19.1),("50-54",681,129,18.9),("55-59",976,223,22.8),
     ("60-64",1012,273,27.0),("65-74",1354,389,28.7),("75-79",250,97,38.8),("80+",121,51,42.1)]
for a in amb: ws6.append(list(a))
ws6.append(["Effect (≥60 vs <60):","RR 1.52","RD 10.1 pp","29.6% vs 19.5%"])
borders(ws6,3,3+len(amb),4); autos(ws6)

# Validation
ws7=wb.create_sheet("Validation")
ws7["A1"]="Validation and notes"; ws7["A1"].font=Font(bold=True,size=12)
notes=[
 "Cohort is a broad proxy (OPS 5-012.0 + primary I63); OPS 5-012.0 is generic cranial decompression within the craniotomy/craniectomy category and does not specify hemicraniectomy or MCA territory. Not validated malignant MCA infarction. Cerebral-artery codes I63.3-5 = 74.6% pooled.",
 "I63.6 (venous) = 0-7 episodes/year across 2019-2024 (<=0.7%; 12 pooled, 0.2%); excluding it changes totals trivially. Reported separately.",
 "Utilisation denominator = all primary-I63 admissions (all ischaemic strokes), not only space-occupying infarction; utilisation is a relative age-pattern proxy, not an eligibility-based rate.",
 "Utilisation ratio and age-stratified mortality computed from age-band percentages x totals (rounding applies); mortality band counts reconstructed from grouped outputs.",
 "<60/≥60 split uses the 55-59 / 60-64 band boundary; approximates but does not reproduce the trial boundary (≤60 younger trials; ≥61 DESTINY II).",
 "Denominator ≥60 share stable 85.4-86.1% across all six years vs cohort ≥60 share 48.2-50.8%.",
 "Disposition (discharge reason 06/07/09/10; hospice 11 queried but suppressed) and I63 subtype composition extracted live for ALL six years 2019-2024. Home/routine/other is a residual (N minus 06/07/09/10) that also absorbs the suppressed hospice count; hospice is not separately reported. Explicit categories sum exactly to N in every year (audited). Each year's cohort episode count reproduced the v1 base volume exactly.",
 "All values read live from the InEK DatenBrowser rendered Info/principal-diagnosis output output, 2026-07-07.",
]
for i,n in enumerate(notes,3): ws7.cell(row=i,column=1,value=f"{i-2}. {n}")
ws7.column_dimensions["A"].width=140

wb.save(os.path.join(HERE,"..","data","results_workbook.xlsx"))
print("workbook written")
