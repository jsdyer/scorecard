import test from "node:test";
import assert from "node:assert/strict";
import {selected,errorBp,summary,csv} from "../web/model.mjs";
const sample = [
  {target:"2025-06",published:"2025-04-20",actual:2.5,median:2.25},
  {target:"2025-06",published:"2025-03-20",actual:2.5,median:2.5},
  {target:"2025-07",published:"2025-05-20",actual:2.25,median:2.25},
  {target:"2025-09",published:"2025-05-20",actual:null,median:2.5},
];
test("completed decisions each count once with latest eligible forecast",()=>{
  const rows=selected(sample,"","latest");
  assert.equal(rows.length,2);
  assert.deepEqual(summary(rows),{hits:1,total:2,mae:12.5});
});
test("keeps pending values separate from zero",()=>{
  assert.equal(errorBp(sample[3]),null);
  assert.deepEqual(summary([sample[3]]),{hits:0,total:0,mae:null});
  assert.match(csv([sample[3]]),/2.5,,,,/);
});
