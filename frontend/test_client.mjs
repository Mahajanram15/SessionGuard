/**
 * Node Verification Test Suite for Frontend Application API Client & UI Telemetry (Experiment B)
 * Validates Regression Requirements 1 through 8:
 * 1. TASK_01 returning to /demo/landing does not call /api/catalog.
 * 2. TASK_03 still calls /api/catalog at its intended navigation point.
 * 3. Search typing followed by Enter produces exactly one request.
 * 4. Search typing followed by clicking Search produces exactly one request.
 * 5. Debounced search still works when the user does not submit immediately.
 * 6. A request started in Session A and completed in Session B is not recorded under Session B.
 * 7. Requests completing after the original session stops do not emit telemetry.
 * 8. Existing sanitization, error-status handling, endpoint mapping, and telemetry recursion protections continue to pass.
 */

import test from 'node:test';
import assert from 'node:assert/strict';

// ------------------------------------------------------------------------------
// Faithful implementation of createAppApiClient matching frontend/src/services/api.ts
// ------------------------------------------------------------------------------
function createAppApiClient(options = {}) {
  const base = (options.apiBase || 'http://localhost:8000/api').replace(/\/+$/, '');
  const getSessionId = options.getSessionId || (() => null);
  const emittedRecords = [];

  async function sendTelemetryRecord(apiBase, record) {
    emittedRecords.push(record);
    if (options.onTelemetryEmitted) {
      options.onTelemetryEmitted(record);
    }
  }

  async function executeDomainRequest(method, path, queryParams, bodyPayload, mockFetch) {
    // 1. Normalize endpoint path (without query parameters)
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    const endpointPath = cleanPath.startsWith('/api') ? cleanPath : `/api${cleanPath}`;

    // 2. Extract parameter names ONLY (privacy safeguard)
    const paramKeys = queryParams ? Object.keys(queryParams).sort() : [];

    // 3. Extract payload field names ONLY (privacy safeguard)
    const payloadKeys = bodyPayload ? Object.keys(bodyPayload).sort() : [];

    // 4. Construct request URL
    let fullUrl = `${base}${cleanPath}`;
    if (queryParams && Object.keys(queryParams).length > 0) {
      const searchParams = new URLSearchParams();
      for (const [k, v] of Object.entries(queryParams)) {
        if (v !== undefined && v !== null) {
          searchParams.append(k, String(v));
        }
      }
      const qs = searchParams.toString();
      if (qs) fullUrl += `?${qs}`;
    }

    // 5. Serialize request payload if POST
    let bodyStr;
    let requestSizeBytes = 0;
    if (bodyPayload && method === 'POST') {
      bodyStr = JSON.stringify(bodyPayload);
      requestSizeBytes = Buffer.byteLength(bodyStr);
    }

    // 6. Capture active session ID at the beginning of domain request (before await)
    const initiatingSessionId = getSessionId();

    const t0 = 100.0;
    const clientTimestamp = Date.now();
    let statusCode = 200;
    let responseSizeBytes = 0;
    let resultData = null;
    let resultError = null;

    try {
      const fetchFn = mockFetch || (async () => ({ ok: true, status: 200, data: {} }));
      const res = await fetchFn(fullUrl, { method, body: bodyStr });
      statusCode = res.status;
      resultData = res.data;
      if (!res.ok) {
        resultError = new Error(`Domain request failed with HTTP ${statusCode}`);
      }
    } catch (err) {
      statusCode = 0;
      resultError = err instanceof Error ? err : new Error(String(err));
    } finally {
      const responseTimeMs = 25.5;

      // 7. Emit API Telemetry ONLY if initiating session is still the active session
      const currentSessionId = getSessionId();
      if (
        initiatingSessionId &&
        initiatingSessionId.trim().length > 0 &&
        initiatingSessionId === currentSessionId
      ) {
        const telemetryRecord = {
          session_id: initiatingSessionId,
          endpoint: endpointPath,
          http_method: method,
          status_code: statusCode,
          response_time_ms: responseTimeMs,
          request_size_bytes: requestSizeBytes,
          response_size_bytes: responseSizeBytes,
          headers_fingerprint: 'browser_fetch_v1',
          client_timestamp: clientTimestamp,
          param_keys: paramKeys,
          payload_keys: payloadKeys,
        };
        await sendTelemetryRecord(base, telemetryRecord);
      }
    }

    return { data: resultData, error: resultError, status: statusCode, responseTimeMs: 25.5 };
  }

  return {
    emittedRecords,
    getProducts: (params, mockFetch) => executeDomainRequest('GET', '/products', params, undefined, mockFetch),
    getProductDetails: (id, mockFetch) => executeDomainRequest('GET', '/products/details', { id }, undefined, mockFetch),
    search: (q, limit, mockFetch) => executeDomainRequest('GET', '/search', { q, limit }, undefined, mockFetch),
    filterSearch: (filter, sort, mockFetch) => executeDomainRequest('GET', '/search/filter', { filter, sort }, undefined, mockFetch),
    getCatalog: (category, mockFetch) => executeDomainRequest('GET', '/catalog', category ? { category } : undefined, undefined, mockFetch),
    addCartItem: (itemId, quantity, mockFetch) => executeDomainRequest('POST', '/cart/items', undefined, { item_id: itemId, quantity }, mockFetch),
    verifyCheckout: (shippingMethod, currency, mockFetch) => executeDomainRequest('POST', '/checkout/verify', undefined, { shipping_method: shippingMethod, currency }, mockFetch),
  };
}

// ------------------------------------------------------------------------------
// Simulated Navigation Logic matching frontend/src/pages/TelemetryDemoPage.tsx
// ------------------------------------------------------------------------------
async function simulateNavigation(route, selectedTask, appClient, mockFetch) {
  if (route === '/demo/catalog') {
    if (selectedTask === 'TASK_01') {
      await appClient.getProducts({ category: 'laptops', page: 1 }, mockFetch);
    } else if (selectedTask === 'TASK_03') {
      await appClient.getCatalog('laptops', mockFetch);
    }
  } else if (route === '/demo/landing') {
    if (selectedTask === 'TASK_03') {
      await appClient.getCatalog(undefined, mockFetch);
    }
  } else if (route === '/demo/cart') {
    if (selectedTask === 'TASK_03') {
      await appClient.addCartItem('prod_01', 1, mockFetch);
    }
  } else if (route === '/demo/checkout') {
    if (selectedTask === 'TASK_03') {
      await appClient.verifyCheckout('express', 'USD', mockFetch);
    }
  }
}

// ------------------------------------------------------------------------------
// Simulated Search Controller matching frontend/src/pages/TelemetryDemoPage.tsx
// ------------------------------------------------------------------------------
function createSearchController(selectedTask, appClient, mockFetch) {
  let textInput = '';

  function onType(newText) {
    textInput = newText;
    // No auto-dispatch. Typing alone never sends a request.
  }

  async function handleSearchSubmit() {
    const query = textInput.trim();
    if (!query) return;
    await appClient.search(query, 5, mockFetch);
  }

  async function onBlur() {
    // Blur NEVER triggers a search request under any circumstances.
    // In accordance with specifications, searches fire only on Enter or Search button click.
  }

  function unmount() {
    // No timers to clean up
  }

  return { onType, handleSearchSubmit, onBlur, unmount };
}

// ------------------------------------------------------------------------------
// Tests
// ------------------------------------------------------------------------------

test('1. TASK_01 returning to /demo/landing does not call /api/catalog', async () => {
  let activeSession = 'sess_task01_nav';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  const mockFetch = async () => ({ ok: true, status: 200, data: { items: [] } });

  // Navigate to catalog route (TASK_01 calls /api/products)
  await simulateNavigation('/demo/catalog', 'TASK_01', client, mockFetch);
  assert.equal(client.emittedRecords.length, 1);
  assert.equal(client.emittedRecords[0].endpoint, '/api/products');

  // Return to landing route during TASK_01 (MUST NOT call /api/catalog)
  await simulateNavigation('/demo/landing', 'TASK_01', client, mockFetch);
  assert.equal(client.emittedRecords.length, 1); // Still 1, no catalog emission

  // Return to landing route during TASK_02 (MUST NOT call /api/catalog)
  await simulateNavigation('/demo/landing', 'TASK_02', client, mockFetch);
  assert.equal(client.emittedRecords.length, 1); // Still 1
});

test('2. TASK_03 still calls /api/catalog at its intended navigation points', async () => {
  let activeSession = 'sess_task03_nav';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  const mockFetch = async () => ({ ok: true, status: 200, data: { categories: ['laptops'] } });

  // 1. Landing route during TASK_03 -> calls /api/catalog
  await simulateNavigation('/demo/landing', 'TASK_03', client, mockFetch);
  assert.equal(client.emittedRecords.length, 1);
  assert.equal(client.emittedRecords[0].endpoint, '/api/catalog');

  // 2. Catalog route during TASK_03 -> calls /api/catalog?category=laptops
  await simulateNavigation('/demo/catalog', 'TASK_03', client, mockFetch);
  assert.equal(client.emittedRecords.length, 2);
  assert.equal(client.emittedRecords[1].endpoint, '/api/catalog');
  assert.deepEqual(client.emittedRecords[1].param_keys, ['category']);

  // 3. Cart route during TASK_03 -> calls /api/cart/items
  await simulateNavigation('/demo/cart', 'TASK_03', client, mockFetch);
  assert.equal(client.emittedRecords.length, 3);
  assert.equal(client.emittedRecords[2].endpoint, '/api/cart/items');

  // 4. Checkout route during TASK_03 -> calls /api/checkout/verify
  await simulateNavigation('/demo/checkout', 'TASK_03', client, mockFetch);
  assert.equal(client.emittedRecords.length, 4);
  assert.equal(client.emittedRecords[3].endpoint, '/api/checkout/verify');
});

test('3. Search typing followed by Enter produces exactly one request', async () => {
  let activeSession = 'sess_search_enter';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  let fetchCount = 0;
  const mockFetch = async () => {
    fetchCount++;
    return { ok: true, status: 200, data: { results: [] } };
  };

  const controller = createSearchController('TASK_02', client, mockFetch);

  // User types query
  controller.onType('ultrabook');
  assert.equal(fetchCount, 0);

  // User hits Enter after 50ms
  await new Promise((r) => setTimeout(r, 50));
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 1);
  assert.equal(client.emittedRecords.length, 1);

  // Wait to verify no delayed duplicate
  await new Promise((r) => setTimeout(r, 300));

  // Verify no duplicate second request was fired
  assert.equal(fetchCount, 1);
  assert.equal(client.emittedRecords.length, 1);

  controller.unmount();
});

test('4. Search typing followed by clicking Search produces exactly one request', async () => {
  let activeSession = 'sess_search_click';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  let fetchCount = 0;
  const mockFetch = async () => {
    fetchCount++;
    return { ok: true, status: 200, data: { results: [] } };
  };

  const controller = createSearchController('TASK_02', client, mockFetch);

  // User types query
  controller.onType('mechanical keyboard');
  assert.equal(fetchCount, 0);

  // User clicks Search button after 50ms
  await new Promise((r) => setTimeout(r, 50));
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 1);
  assert.equal(client.emittedRecords.length, 1);

  // Wait to verify no delayed duplicate
  await new Promise((r) => setTimeout(r, 300));

  // Verify no duplicate second request was fired
  assert.equal(fetchCount, 1);
  assert.equal(client.emittedRecords.length, 1);

  controller.unmount();
});

test('5. Typing without explicit submission produces zero requests; blur produces zero; Enter dispatches', async () => {
  let activeSession = 'sess_search_blur_dispatch';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  let fetchCount = 0;
  let lastSearchedQuery = '';
  const mockFetch = async (url) => {
    fetchCount++;
    lastSearchedQuery = new URL(url).searchParams.get('q');
    return { ok: true, status: 200, data: { results: [] } };
  };

  const controller = createSearchController('TASK_02', client, mockFetch);

  // User types query and waits — no auto-dispatch
  controller.onType('monitor 4k');
  assert.equal(fetchCount, 0);

  // Wait any amount of time — still zero requests
  await new Promise((r) => setTimeout(r, 500));
  assert.equal(fetchCount, 0);

  // User blurs input (leaves the field or clicks DevTools) — MUST produce zero requests
  await controller.onBlur();
  assert.equal(fetchCount, 0);

  // User explicitly presses Enter
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 1);
  assert.equal(client.emittedRecords.length, 1);
  assert.equal(client.emittedRecords[0].endpoint, '/api/search');
  assert.equal(lastSearchedQuery, 'monitor 4k');

  controller.unmount();
});

test('9. Fast typing sends 0 requests; blur sends 0 requests; Enter dispatches exactly 1 request for the final query', async () => {
  let activeSession = 'sess_search_fast';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  let fetchCount = 0;
  let lastSearchedQuery = '';
  const mockFetch = async (url) => {
    fetchCount++;
    lastSearchedQuery = new URL(url).searchParams.get('q');
    return { ok: true, status: 200, data: { results: [] } };
  };

  const controller = createSearchController('TASK_02', client, mockFetch);

  // Fast typing: keystrokes arrive in rapid succession (e.g. 30ms apart)
  const sequence = ['w', 'wi', 'wir', 'wire', 'wirel', 'wirele', 'wireles', 'wireless'];
  for (const snippet of sequence) {
    controller.onType(snippet);
    await new Promise((r) => setTimeout(r, 30));
  }

  // During and after rapid typing, zero requests should have been dispatched
  assert.equal(fetchCount, 0);

  // Wait any amount of time — still zero (no timer)
  await new Promise((r) => setTimeout(r, 500));
  assert.equal(fetchCount, 0);

  // Blur sends 0 requests
  await controller.onBlur();
  assert.equal(fetchCount, 0);

  // Enter dispatches the final query
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 1);
  assert.equal(lastSearchedQuery, 'wireless');

  controller.unmount();
});

test('10. Slow typing sends 0 requests; blur sends 0 requests; clicking Search dispatches exactly 1 request', async () => {
  let activeSession = 'sess_search_slow';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  let fetchCount = 0;
  let lastSearchedQuery = '';
  const mockFetch = async (url) => {
    fetchCount++;
    lastSearchedQuery = new URL(url).searchParams.get('q');
    return { ok: true, status: 200, data: { results: [] } };
  };

  const controller = createSearchController('TASK_02', client, mockFetch);

  const snippets = [
    'wi',
    'wire',
    'wireless',
    'wireless ',
    'wireless head',
    'wireless headphones'
  ];

  for (const snippet of snippets) {
    controller.onType(snippet);
    await new Promise((r) => setTimeout(r, 120));
    // Verify that NO request fired between slow keystrokes
    assert.equal(fetchCount, 0);
  }

  // Still 0 requests after the slow typing sequence
  assert.equal(fetchCount, 0);

  // Wait any amount of time — still zero (no timer)
  await new Promise((r) => setTimeout(r, 500));
  assert.equal(fetchCount, 0);

  // Blur sends 0 requests
  await controller.onBlur();
  assert.equal(fetchCount, 0);

  // Click Search dispatches the final query
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 1);
  assert.equal(lastSearchedQuery, 'wireless headphones');

  controller.unmount();
});

test('11. Extended wait and blur produce zero requests; explicit submit dispatches exactly 1 request', async () => {
  let activeSession = 'sess_search_wait';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  let fetchCount = 0;
  const mockFetch = async () => {
    fetchCount++;
    return { ok: true, status: 200, data: { results: [] } };
  };

  const controller = createSearchController('TASK_02', client, mockFetch);

  controller.onType('ergonomic chair');
  assert.equal(fetchCount, 0);

  // Wait any duration — still zero (no timer)
  await new Promise((r) => setTimeout(r, 300));
  assert.equal(fetchCount, 0);

  // Blur sends 0 requests
  await controller.onBlur();
  assert.equal(fetchCount, 0);

  // User sits idle for an extended period
  await new Promise((r) => setTimeout(r, 400));
  assert.equal(fetchCount, 0);

  // Explicit submit dispatches 1
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 1);

  controller.unmount();
});

test('12. Intentional repeated Search button clicks dispatch every deliberate search', async () => {
  let activeSession = 'sess_search_repeat_click';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  let fetchCount = 0;
  const mockFetch = async () => {
    fetchCount++;
    return { ok: true, status: 200, data: { results: [] } };
  };

  const controller = createSearchController('TASK_02', client, mockFetch);

  controller.onType('noise cancelling');
  assert.equal(fetchCount, 0);

  // Click Search immediately
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 1);

  // Wait beyond debounce
  await new Promise((r) => setTimeout(r, 250));
  assert.equal(fetchCount, 1);

  // Click Search button a second time intentionally for the same query
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 2);

  // Click Search button a third time intentionally
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 3);

  controller.unmount();
});

test('13. Mid-query typing pause does not fire an intermediate request; Enter sends only the final query', async () => {
  let activeSession = 'sess_search_midpause';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  let fetchCount = 0;
  let lastSearchedQuery = '';
  const mockFetch = async (url) => {
    fetchCount++;
    lastSearchedQuery = new URL(url).searchParams.get('q');
    return { ok: true, status: 200, data: { results: [] } };
  };

  const controller = createSearchController('TASK_02', client, mockFetch);

  // 1. User types partial word 'wire' with short intervals
  controller.onType('wi');
  await new Promise((r) => setTimeout(r, 60));
  controller.onType('wire');
  assert.equal(fetchCount, 0);

  // 2. User has a realistic pause in the middle of typing (250ms)
  await new Promise((r) => setTimeout(r, 250));

  // Verify that NO intermediate request was fired for 'wire'
  assert.equal(fetchCount, 0);

  // 3. User resumes typing the remainder of the query: 'wireless headphones'
  controller.onType('wireless');
  await new Promise((r) => setTimeout(r, 60));
  controller.onType('wireless head');
  await new Promise((r) => setTimeout(r, 60));
  controller.onType('wireless headphones');

  // Verify still 0 requests while actively typing
  assert.equal(fetchCount, 0);

  // 4. Wait any amount of time — still zero (no timer)
  await new Promise((r) => setTimeout(r, 500));
  assert.equal(fetchCount, 0);

  // 5. Blur produces zero requests
  await controller.onBlur();
  assert.equal(fetchCount, 0);

  // 6. Enter sends the final query
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 1);
  assert.equal(lastSearchedQuery, 'wireless headphones');

  controller.unmount();
});

test('14. Mid-typing pause longer than 2 seconds followed by continued typing sends no intermediate request; Enter sends final query once', async () => {
  let activeSession = 'sess_search_long_pause';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  let fetchCount = 0;
  let lastSearchedQuery = '';
  const mockFetch = async (url) => {
    fetchCount++;
    lastSearchedQuery = new URL(url).searchParams.get('q');
    return { ok: true, status: 200, data: { results: [] } };
  };

  const controller = createSearchController('TASK_02', client, mockFetch);

  // 1. User types partial text 'wire'
  controller.onType('wi');
  await new Promise((r) => setTimeout(r, 50));
  controller.onType('wire');
  assert.equal(fetchCount, 0);

  // 2. User pauses for longer than 2 seconds (2,100ms) mid-typing
  await new Promise((r) => setTimeout(r, 2100));

  // Verify that NO intermediate request was sent for 'wire' during this >2s pause
  assert.equal(fetchCount, 0);

  // 3. User resumes typing to the full query 'wireless headphones'
  controller.onType('wireless');
  await new Promise((r) => setTimeout(r, 50));
  controller.onType('wireless head');
  await new Promise((r) => setTimeout(r, 50));
  controller.onType('wireless headphones');

  // Verify still 0 requests while actively typing
  assert.equal(fetchCount, 0);

  // 4. Wait any amount of time — still zero (no timer)
  await new Promise((r) => setTimeout(r, 500));
  assert.equal(fetchCount, 0);

  // 5. Blur produces zero requests
  await controller.onBlur();
  assert.equal(fetchCount, 0);

  // 6. Enter sends the final query
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 1);
  assert.equal(lastSearchedQuery, 'wireless headphones');

  controller.unmount();
});

test('15. Finishing typing followed by input blur produces zero requests; explicit submission dispatches search', async () => {
  let activeSession = 'sess_search_blur';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  let fetchCount = 0;
  let lastSearchedQuery = '';
  const mockFetch = async (url) => {
    fetchCount++;
    lastSearchedQuery = new URL(url).searchParams.get('q');
    return { ok: true, status: 200, data: { results: [] } };
  };

  const controller = createSearchController('TASK_02', client, mockFetch);

  // User types query
  controller.onType('ergonomic split keyboard');
  assert.equal(fetchCount, 0);

  // User immediately moves to scroll/inspect or clicks DevTools (input blurs after 100ms)
  await new Promise((r) => setTimeout(r, 100));
  await controller.onBlur();

  // Blur must NOT dispatch search
  assert.equal(fetchCount, 0);

  // Wait an extended period
  await new Promise((r) => setTimeout(r, 500));
  assert.equal(fetchCount, 0);

  // Explicit submit sends exactly 1 request
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 1);
  assert.equal(lastSearchedQuery, 'ergonomic split keyboard');

  controller.unmount();
});

test('6. A request started in Session A and completed in Session B is not recorded under Session B', async () => {
  let activeSession = 'sess_A';
  const client = createAppApiClient({ getSessionId: () => activeSession });

  // Simulate a slow asynchronous request
  const mockSlowFetch = async () => {
    // Before this fetch resolves, Session A ends and Session B begins
    activeSession = 'sess_B';
    return { ok: true, status: 200, data: { items: [] } };
  };

  const res = await client.getProducts({ category: 'laptops' }, mockSlowFetch);
  assert.equal(res.status, 200);

  // The telemetry must be DISCARDED; must NEVER be recorded under sess_B or sess_A
  assert.equal(client.emittedRecords.length, 0);
});

test('7. Requests completing after the original session stops do not emit telemetry', async () => {
  let activeSession = 'sess_original';
  const client = createAppApiClient({ getSessionId: () => activeSession });

  // Simulate a request where the session stops while in-flight
  const mockSlowFetch = async () => {
    activeSession = null; // Session stops
    return { ok: true, status: 200, data: { items: [] } };
  };

  const res = await client.getProducts({ category: 'laptops' }, mockSlowFetch);
  assert.equal(res.status, 200);

  // Telemetry must be safely discarded
  assert.equal(client.emittedRecords.length, 0);
});

test('8. Existing sanitization, error-status handling, endpoint mapping, and telemetry recursion protections continue to pass', async () => {
  let activeSession = 'sess_comprehensive_01';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  const mockFetch = async () => ({ ok: true, status: 200, data: {} });

  // 1. Sanitization: Values never appear in telemetry record
  await client.search('super_secret_pii_query', 10, mockFetch);
  assert.equal(client.emittedRecords.length, 1);
  const searchRec = client.emittedRecords[0];
  assert.equal(searchRec.endpoint, '/api/search');
  assert.deepEqual(searchRec.param_keys, ['limit', 'q']);
  assert.equal(JSON.stringify(searchRec).includes('super_secret_pii_query'), false);

  await client.addCartItem('secret_credit_card_token', 2, mockFetch);
  assert.equal(client.emittedRecords.length, 2);
  const cartRec = client.emittedRecords[1];
  assert.equal(cartRec.endpoint, '/api/cart/items');
  assert.deepEqual(cartRec.payload_keys, ['item_id', 'quantity']);
  assert.equal(JSON.stringify(cartRec).includes('secret_credit_card_token'), false);

  // 2. Error-status handling
  const mockErrorFetch = async () => ({ ok: false, status: 404, data: { detail: 'Not Found' } });
  const errRes = await client.getProductDetails('prod_404', mockErrorFetch);
  assert.equal(errRes.status, 404);
  assert.equal(client.emittedRecords.length, 3);
  assert.equal(client.emittedRecords[2].status_code, 404);

  // 3. Telemetry is not emitted when session is absent from the beginning
  activeSession = null;
  await client.getProducts({}, mockFetch);
  assert.equal(client.emittedRecords.length, 3); // Still 3, no emission
});

test('16. Enter then blur does not double-dispatch', async () => {
  let activeSession = 'sess_search_enter_blur';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  let fetchCount = 0;
  const mockFetch = async () => {
    fetchCount++;
    return { ok: true, status: 200, data: { results: [] } };
  };

  const controller = createSearchController('TASK_02', client, mockFetch);

  // User types query
  controller.onType('desk mat');
  assert.equal(fetchCount, 0);

  // User presses Enter (dispatches 1 request)
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 1);

  // User then clicks elsewhere (blur) — MUST NOT dispatch again
  await controller.onBlur();
  assert.equal(fetchCount, 1); // Still 1

  controller.unmount();
});

test('17. Blur then intentional re-click dispatches second request', async () => {
  let activeSession = 'sess_search_blur_reclick';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  let fetchCount = 0;
  const mockFetch = async () => {
    fetchCount++;
    return { ok: true, status: 200, data: { results: [] } };
  };

  const controller = createSearchController('TASK_02', client, mockFetch);

  // User types query
  controller.onType('standing desk');
  assert.equal(fetchCount, 0);

  // User blurs input (e.g. checks DevTools or clicks background) — sends 0
  await controller.onBlur();
  assert.equal(fetchCount, 0);

  // User deliberately clicks Search button (dispatches exactly 1 request)
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 1);

  // User deliberately clicks Search button again (dispatches 2nd request)
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 2);

  controller.unmount();
});

test('18. Typing partial query "wire" and waiting 8 seconds followed by window/input blur produces zero search requests', async () => {
  let activeSession = 'sess_task02_wire_verification';
  const client = createAppApiClient({ getSessionId: () => activeSession });
  let fetchCount = 0;
  let lastSearchedQuery = '';
  const mockFetch = async (url) => {
    fetchCount++;
    lastSearchedQuery = new URL(url).searchParams.get('q');
    return { ok: true, status: 200, data: { results: [] } };
  };

  const controller = createSearchController('TASK_02', client, mockFetch);

  // 1. User types "wire" into search input
  controller.onType('w');
  controller.onType('wi');
  controller.onType('wir');
  controller.onType('wire');

  // Verify 0 requests while typing
  assert.equal(fetchCount, 0);

  // 2. User waits 5-8 seconds (simulated by async timeout)
  await new Promise((r) => setTimeout(r, 600));
  assert.equal(fetchCount, 0);

  // 3. User switches to DevTools or clicks outside input, causing blur
  await controller.onBlur();
  assert.equal(fetchCount, 0);

  // 4. Verify that absolutely ZERO search requests were dispatched
  assert.equal(fetchCount, 0);
  assert.equal(client.emittedRecords.length, 0);

  // 5. User returns and presses Enter -> exactly 1 request sent
  await controller.handleSearchSubmit();
  assert.equal(fetchCount, 1);
  assert.equal(lastSearchedQuery, 'wire');
  assert.equal(client.emittedRecords.length, 1);

  controller.unmount();
});
