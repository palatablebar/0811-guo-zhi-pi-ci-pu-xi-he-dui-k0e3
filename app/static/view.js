import {element, pretty} from './client.js';

const labels = {READY:'通过', MISMATCH:'差异待复核', PENDING:'待复核', APPROVED:'已签发', HELD:'已暂缓', BLOCKED:'跨批停发'};
const headers = ['业务分组', '输入行', '计算值', '参考值', '判定'];

export function badge(status) {
  return element('span', labels[status] || status, {class:'badge', 'data-result':status, title: status});
}

function sharedView(balance) {
  const box = document.querySelector('#shared');
  box.replaceChildren();
  if (!balance?.shared?.length) { box.hidden = true; return; }
  box.hidden = false;
  box.append(element('h3','跨批次放行结论'));
  const table = element('table');
  const head = element('tr');
  head.append(...['原料批号','可用量','累计领用','剩余','结论','受影响批次'].map(title => element('th', title, {scope:'col'})));
  table.createTHead().append(head);
  const body = table.createTBody();
  for (const row of balance.shared) {
    const tr = body.insertRow();
    tr.dataset.over = String(row.over);
    [row.material, row.available, row.consumed, row.surplus].forEach(value => tr.insertCell().textContent = value);
    tr.insertCell().append(badge(row.over ? 'BLOCKED' : 'READY'));
    tr.insertCell().textContent = row.cases.join('、') || '—';
  }
  box.append(table);
  const note = balance.blocked.length
    ? `累计占用超过可用量，批次 ${balance.blocked.join('、')} 不得签发`
    : '各原料批号累计占用均未超过可用量';
  box.append(element('p', note, {class:'shared-note'}));
}

export function snapshot(report, selected, stage) {
  const stats = report.intake;
  document.querySelector('[data-metric="input"]').textContent = stats.input;
  document.querySelector('[data-metric="accepted"]').textContent = stats.accepted;
  document.querySelector('[data-metric="isolated"]').textContent = stats.rejected;
  document.querySelector('[data-metric="cases"]').textContent = report.cases?.length ?? '—';
  const table = document.querySelector('#rows');
  table.replaceChildren();
  const head = element('tr');
  const body = table.createTBody();
  if (stage === 'intake') {
    head.append(...['源行', '记录键', '业务分组', '原因码'].map(title => element('th', title, {scope:'col'})));
    for (const item of stats.isolation) {
      const tr = body.insertRow();
      tr.append(...[item.line,item.record,item.case,item.reason].map(value=>element('td',value)));
    }
    if (!stats.isolation.length) body.insertRow().insertCell().textContent = '当前文件没有隔离行';
  } else {
    head.append(...headers.map(title => element('th', title, {scope:'col'})));
    const blocked = new Set(report.balance?.blocked || []);
    for (const row of report.cases || []) {
      const tr = body.insertRow();
      const button = element('button',row.case,{type:'button','data-case':row.case,'aria-pressed':String(row.case===selected)});
      tr.insertCell().append(button);
      [row.records.length, row.measure?.value ?? '—', row.measure?.expected ?? '—'].forEach(value=>tr.insertCell().textContent=value);
      const verdict = tr.insertCell();
      verdict.append(badge(row.status));
      if (blocked.has(row.case)) verdict.append(badge('BLOCKED'));
    }
  }
  table.createTHead().append(head);
  sharedView(report.balance);
  const picked = report.cases?.find(row=>row.case===selected);
  document.querySelector('#detail-title').textContent = picked ? `分组 ${picked.case}` : '采信摘要';
  const shown = picked ? picked.measure?.evidence ?? picked.prep?.details ?? {原因:picked.status} : stats.reasons;
  document.querySelector('#detail').textContent = pretty(shown);
  document.querySelector('#counts').textContent = report.balance ? `行数 ${report.balance.accounted}/${report.balance.input} · ${report.balance.ready} 组通过 · ${report.balance.blocked.length} 组跨批停发` : `采信 ${stats.accepted} 行 · 隔离 ${stats.rejected} 行`;
}

export function history(items, active) {
  const target = document.querySelector('#history');
  target.replaceChildren();
  for (const run of items) {
    const button = element('button', run.id.slice(0,10), {'data-run':run.id,'aria-pressed':String(run.id===active),type:'button'});
    const item = element('li');
    item.append(button, badge(run.status));
    target.append(item);
  }
  if (!items.length) target.append(element('li','尚无执行批次'));
}
