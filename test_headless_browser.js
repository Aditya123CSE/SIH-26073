const { spawn } = require('child_process');

async function run() {
  console.log('--- Starting Chromium in Headless mode ---');
  const port = 9333;
  const chrome = spawn('/usr/bin/chromium', [
    '--headless=new',
    '--disable-gpu',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    `--remote-debugging-port=${port}`,
    'http://127.0.0.1:8080'
  ]);

  let killed = false;
  function cleanup() {
    if (!killed) {
      killed = true;
      try { chrome.kill(); } catch (e) {}
    }
  }
  process.on('exit', cleanup);
  process.on('SIGINT', cleanup);

  // Wait for remote debugging port to open and target to appear
  let pageWsUrl = null;
  for (let i = 0; i < 40; i++) {
    await new Promise(r => setTimeout(r, 250));
    try {
      const res = await fetch(`http://127.0.0.1:${port}/json/list`);
      const list = await res.json();
      const pageTarget = list.find(t => t.type === 'page' && t.url.includes('8080'));
      if (pageTarget) {
        pageWsUrl = pageTarget.webSocketDebuggerUrl;
        break;
      }
    } catch (e) {}
  }

  if (!pageWsUrl) {
    console.error('Failed to find page target on Chromium CDP port');
    cleanup();
    process.exit(1);
  }

  console.log('Connected to Chromium CDP page target:', pageWsUrl);

  const ws = new WebSocket(pageWsUrl);
  let id = 1;
  const pending = new Map();
  const consoleErrors = [];
  const runtimeExceptions = [];

  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const msgId = id++;
      pending.set(msgId, { resolve, reject, method });
      ws.send(JSON.stringify({ id: msgId, method, params }));
    });
  }

  await new Promise((resolve) => {
    ws.onopen = resolve;
  });

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(msg.error);
      else resolve(msg.result);
    } else if (msg.method) {
      if (msg.method === 'Runtime.consoleAPICalled') {
        const type = msg.params.type;
        const text = msg.params.args.map(a => a.value || JSON.stringify(a)).join(' ');
        if (type === 'error') {
          consoleErrors.push(text);
          console.error('[BROWSER ERROR]', text);
        } else if (type === 'warn') {
          // console.warn('[BROWSER WARN]', text);
        } else {
          // console.log('[BROWSER LOG]', text);
        }
      } else if (msg.method === 'Runtime.exceptionThrown') {
        const text = msg.params.exceptionDetails.text + ': ' +
          (msg.params.exceptionDetails.exception?.description || msg.params.exceptionDetails.text);
        runtimeExceptions.push(text);
        console.error('[RUNTIME EXCEPTION]', text);
      }
    }
  };

  // Enable domains
  await send('Page.enable');
  await send('Runtime.enable');
  await send('DOM.enable');

  console.log('Waiting 3.5s for page and initial API assimilation to load...');
  await new Promise(r => setTimeout(r, 3500));

  async function evaluate(expression) {
    const res = await send('Runtime.evaluate', {
      expression,
      returnByValue: true,
      awaitPromise: true
    });
    if (res.exceptionDetails) {
      throw new Error(res.exceptionDetails.text + ': ' + (res.exceptionDetails.exception?.description || ''));
    }
    return res.result?.value;
  }

  console.log('\n--- 1. Testing Page Title & App Header ---');
  const title = await evaluate('document.title');
  console.log('Page Title:', title);

  const stationsCount = await evaluate('allStations ? allStations.length : 0');
  console.log('Loaded Stations count:', stationsCount);

  console.log('\n--- 2. Testing Notification Bell Dropdown ---');
  // Click bell button
  const bellClickRes = await evaluate(`
    (() => {
      const bell = document.getElementById('header-bell-btn');
      if (!bell) return { error: 'No header-bell-btn' };
      bell.click();
      const dd = document.getElementById('notification-dropdown');
      const isVisible = dd && !dd.classList.contains('hidden');
      const countPill = document.getElementById('notif-count-pill')?.innerText;
      const itemCount = dd?.querySelectorAll('#notification-list > div')?.length || 0;
      return { isVisible, countPill, itemCount };
    })()
  `);
  console.log('Bell button click result:', bellClickRes);

  // Close dropdown by clicking acknowledge or outside
  const closeRes = await evaluate(`
    (() => {
      closeNotificationDropdown();
      const dd = document.getElementById('notification-dropdown');
      return { isHidden: dd && dd.classList.contains('hidden') };
    })()
  `);
  console.log('Notification dropdown close result:', closeRes);

  console.log('\n--- 3. Testing Navigation Tab Switching ---');
  const pages = ['guide', 'overview', 'map', 'sandbox', 'inspector', 'xai'];
  for (const page of pages) {
    const switchRes = await evaluate(`
      (() => {
        switchPage('${page}');
        const el = document.getElementById('page-${page}');
        return {
          page: '${page}',
          isActive: el && !el.classList.contains('hidden'),
          hash: window.location.hash
        };
      })()
    `);
    console.log('Switched to page [' + page + ']:', switchRes);
    await new Promise(r => setTimeout(r, 200));
  }

  console.log('\n--- 4. Testing Fault Injection Sandbox & Buttons ---');
  await evaluate(`switchPage('sandbox')`);
  const faultButtonsRes = await evaluate(`
    (() => {
      const faults = ['drift', 'flatline', 'sensor_lockup', 'thermodynamic_conflict', 'solar_radiation_night'];
      const results = {};
      for (const f of faults) {
        try {
          injectAnomaly(f);
          results[f] = 'SUCCESS';
        } catch (e) {
          results[f] = 'ERROR: ' + e.message;
        }
      }
      try {
        resetStationSimulation();
        results['reset'] = 'SUCCESS';
      } catch (e) {
        results['reset'] = 'ERROR: ' + e.message;
      }
      return results;
    })()
  `);
  console.log('Fault Injection Button Execution:', faultButtonsRes);

  console.log('\n--- 5. Testing Station Deep Dive & Selector ---');
  await evaluate(`switchPage('inspector')`);
  const stationSelectRes = await evaluate(`
    (() => {
      if (allStations && allStations.length > 1) {
        selectStation(allStations[1].station_id);
        const name = document.getElementById('deep-station-name')?.innerText;
        return { selectedId: allStations[1].station_id, renderedName: name };
      }
      return { error: 'No stations' };
    })()
  `);
  console.log('Station Selection Result:', stationSelectRes);

  console.log('\n--- 6. Testing Modals (Audit Report, Technician Dispatch) ---');
  const modalTestRes = await evaluate(`
    (() => {
      const res = {};
      try {
        openStationReportModal('DEL01');
        const modal = document.getElementById('station-report-modal');
        res.reportModalOpened = modal && !modal.classList.contains('hidden');
        closeStationReportModal();
        res.reportModalClosed = modal && modal.classList.contains('hidden');
      } catch (e) {
        res.reportModalError = e.message;
      }

      try {
        openTechMachineModal('DEL01');
        const techModal = document.getElementById('tech-machine-modal');
        res.techModalOpened = techModal && !techModal.classList.contains('hidden');
        closeTechMachineModal();
        res.techModalClosed = techModal && techModal.classList.contains('hidden');
      } catch (e) {
        res.techModalError = e.message;
      }
      return res;
    })()
  `);
  console.log('Modals test result:', modalTestRes);

  console.log('\n--- 7. Testing Audio Synthesizer Toggle & Layout Density ---');
  const togglesRes = await evaluate(`
    (() => {
      const res = {};
      try {
        toggleCyberAudio();
        res.audioToggled = true;
      } catch (e) {
        res.audioError = e.message;
      }
      try {
        setLayoutDensity('compact');
        res.densityCompact = document.body.classList.contains('density-compact');
        setLayoutDensity('expansive');
        res.densityExpansive = document.body.classList.contains('density-expansive');
        setLayoutDensity('standard');
        res.densityStandard = !document.body.classList.contains('density-compact') && !document.body.classList.contains('density-expansive');
      } catch (e) {
        res.densityError = e.message;
      }
      return res;
    })()
  `);
  console.log('Audio & Density test result:', togglesRes);

  console.log('\n--- 8. Testing Summary of Console & Runtime Errors ---');
  console.log('Total Console Errors:', consoleErrors.length);
  if (consoleErrors.length > 0) {
    consoleErrors.forEach((e, idx) => console.log('  [#' + (idx+1) + ']', e));
  }
  console.log('Total Runtime Exceptions:', runtimeExceptions.length);
  if (runtimeExceptions.length > 0) {
    runtimeExceptions.forEach((e, idx) => console.log('  [#' + (idx+1) + ']', e));
  }

  cleanup();
  console.log('\n--- Headless Browser Verification Complete ---');
  process.exit(0);
}

run().catch(err => {
  console.error('Fatal Test Runner Error:', err);
  process.exit(1);
});
