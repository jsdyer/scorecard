export function months(records) {
  return [...new Set(records.map(row => row.target))].sort().reverse();
}

export function selected(records, target, view) {
  if (view === "target") {
    return records.filter(row => row.target === target).sort((a,b) => b.published.localeCompare(a.published));
  }
  const latest = new Map();
  for (const row of records) {
    if (row.actual === null) continue;
    const prior = latest.get(row.target);
    if (!prior || prior.published < row.published) latest.set(row.target, row);
  }
  return [...latest.values()].sort((a,b) => b.target.localeCompare(a.target));
}

export function errorBp(row) {
  return row.actual === null ? null : Math.round((row.median - row.actual) * 100);
}

export function summary(rows) {
  const errors = rows.map(errorBp).filter(error => error !== null);
  return {
    hits: errors.filter(error => error === 0).length,
    total: errors.length,
    mae: errors.length ? errors.reduce((sum,x) => sum + Math.abs(x), 0) / errors.length : null,
  };
}

export function csv(rows) {
  const keys = ["target","decision","edition","published","respondents","low","median","high","actual","error_bp","source"];
  return [keys.join(","), ...rows.map(row => keys.map(key => key === "error_bp" ? errorBp(row) : row[key]).join(","))].join("\r\n")+"\r\n";
}
