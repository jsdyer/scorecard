import {months, selected, errorBp, summary, csv} from "./model.mjs";

const el = id => document.getElementById(id);
const formatDate = value => new Intl.DateTimeFormat("en-CA", {year:"numeric",month:"short",day:"numeric",timeZone:"UTC"}).format(new Date(value+"T00:00:00Z"));
const formatMonth = value => new Intl.DateTimeFormat("en-CA",{month:"long",year:"numeric",timeZone:"UTC"}).format(new Date(value+"-01T00:00:00Z"));
const percent = value => value.toFixed(2)+"%";
const signed = value => (value > 0 ? "+" : "")+value+" bp";
let records = [];
let visible = [];

function cell(tr, value) {
  const td = tr.insertCell();
  td.textContent = value;
  return td;
}

function draw() {
  const view=el("view").value, target=el("target").value;
  el("target").disabled = view !== "target";
  visible = selected(records,target,view);
  const {total,hits,mae} = summary(visible);
  const latest = visible[0];
  if (view === "target") {
    el("headline").textContent = formatMonth(target)+" decision";
    el("reading").textContent = latest.actual === null
      ? "The Bank has yet to publish a decision in this snapshot. Follow how the median changes across survey releases."
      : "On "+formatDate(latest.decision)+", the Bank announced "+percent(latest.actual)+". The most recent eligible survey had put it at "+percent(latest.median)+".";
    el("caption").textContent = "Surveys available before this decision, most recent first";
  } else {
    el("headline").textContent = hits+" of "+total+" medians matched the decision";
    el("reading").textContent = "Across these "+total+" decisions, the latest public forecast missed by an average of "+mae.toFixed(1)+" basis points in either direction.";
    el("caption").textContent = "Latest eligible survey for each completed decision";
  }
  const body = el("rows");
  body.replaceChildren();
  for (const row of visible) {
    const tr=body.insertRow();
    cell(tr,row.decision ? formatDate(row.decision) : formatMonth(row.target));
    const link=document.createElement("a");
    link.href=row.source; link.textContent=formatDate(row.published); link.title=row.edition+" survey";
    tr.insertCell().append(link);
    cell(tr,row.respondents);
    cell(tr,percent(row.low)+" – "+percent(row.high));
    cell(tr,percent(row.median));
    cell(tr,row.actual === null ? "Pending" : percent(row.actual));
    const err=errorBp(row);
    cell(tr,err === null ? "—" : signed(err)).className=err === 0 ? "hit" : "";
  }
}

async function start() {
  try {
    const response=await fetch("./data/scorecard.json");
    if (!response.ok) throw Error("snapshot unavailable");
    const data=await response.json();
    records=data.receipts;
    for (const month of months(records)) {
      const pending=records.find(row => row.target === month).actual === null;
      el("target").add(new Option(formatMonth(month)+(pending ? " · pending" : ""),month));
    }
    el("target").value=selected(records,"","latest")[0].target;
    const count = new Set(records.map(r => r.edition)).size;
    el("status").textContent="Bank data retrieved "+formatDate(data.retrieved)+" · "+count+" survey releases · "+records.length+" eligible forecasts";
    draw();
    el("results").hidden=false;
    el("view").addEventListener("change",draw);
    el("target").addEventListener("change",draw);
    el("download").addEventListener("click",() => {
      const url=URL.createObjectURL(new Blob([csv(visible)],{type:"text/csv;charset=utf-8"}));
      const a=document.createElement("a"); a.href=url; a.download="policy-rate-"+(el("view").value === "latest" ? "history" : el("target").value)+".csv";
      a.click(); setTimeout(() => URL.revokeObjectURL(url),1000);
    });
  } catch {
    el("status").textContent="The scorecard could not load. Download the complete dataset below or reload the page.";
  }
}
start();
