// Reusable Node Provider Contract 0.1 stdio fixture and Relay Client v1 caller.
const fs = require('fs');
const { spawn } = require('child_process');

function frame(value) {
  const body = Buffer.from(JSON.stringify(value), 'utf8');
  return Buffer.concat([Buffer.from(`Content-Length: ${body.length}\r\n\r\n`), body]);
}

function provider(manifestPath) {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  let buffer = Buffer.alloc(0);
  let waiting;
  const send = value => process.stdout.write(frame(value));
  process.stdin.on('data', chunk => {
    buffer = Buffer.concat([buffer, chunk]);
    while (true) {
      const headerEnd = buffer.indexOf('\r\n\r\n');
      if (headerEnd < 0) return;
      const header = buffer.subarray(0, headerEnd).toString('ascii');
      const match = /^Content-Length: (\d+)$/i.exec(header);
      if (!match) process.exit(2);
      const length = Number(match[1]);
      if (buffer.length < headerEnd + 4 + length) return;
      const message = JSON.parse(buffer.subarray(headerEnd + 4, headerEnd + 4 + length));
      buffer = buffer.subarray(headerEnd + 4 + length);
      if (message.method === 'initialize') {
        send({ jsonrpc: '2.0', id: message.id,
          result: { contract_version: '0.1', manifest } });
      } else if (message.method === 'invoke') {
        const invocation = message.params;
        const word = invocation.input.text;
        const evidence = { structured_data: { rule_id: 'node-phrase', observed: word } };
        send({ jsonrpc: '2.0', method: 'event', params: {
          invocation_id: invocation.invocation_id, sequence: 1,
          kind: 'evidence', payload: evidence } });
        if (word.includes('WAIT')) {
          waiting = { id: message.id, invocation_id: invocation.invocation_id };
          return;
        }
        if (word.includes('ERROR')) {
          send({ jsonrpc: '2.0', id: message.id, result: {
            invocation_id: invocation.invocation_id, state: 'ERROR',
            error: { code: 'com.example.failure', message: 'fixture failure' } } });
          return;
        }
        const result = { protocol: 'draft', disposition: 'EXECUTED',
          execution_outcome: 'SUCCESS', applicability: 'APPLICABLE',
          determination: 'KNOWN', verdict: word.includes('TBD') ? 'FAIL' : 'PASS',
          evidence: [evidence] };
        send({ jsonrpc: '2.0', id: message.id, result: {
          invocation_id: invocation.invocation_id, state: 'COMPLETED',
          output: { result } } });
      } else if (message.method === 'cancel' && waiting) {
        send({ jsonrpc: '2.0', id: waiting.id, result: {
          invocation_id: waiting.invocation_id, state: 'CANCELLED' } });
      }
    }
  });
}

function client(python, configPath, graphPath, dbPath, text) {
  const providerArgs = configPath === '-'
    ? ['--project-root', require('path').dirname(graphPath)]
    : ['--providers', configPath];
  const child = spawn(python, ['-m', 'openverify.relay.entrypoints.cli', 'client',
    '--database', dbPath, ...providerArgs]);
  let buffer = '';
  const send = value => child.stdin.write(JSON.stringify(value) + '\n');
  child.stdout.on('data', chunk => {
    buffer += chunk.toString('utf8');
    while (buffer.includes('\n')) {
      const index = buffer.indexOf('\n');
      const line = buffer.slice(0, index);
      buffer = buffer.slice(index + 1);
      const response = JSON.parse(line);
      if (!response.ok) {
        console.error(JSON.stringify(response));
        child.kill();
        process.exitCode = 1;
        return;
      }
      if (response.id === 'register') {
        send({ client_version: '1', id: 'run', op: 'run',
          graph_id: response.result.graph_id, request_id: 'node-run', inputs: { text } });
        if (text.includes('WAIT')) setTimeout(() => send({
          client_version: '1', id: 'cancel', op: 'cancel', request_id: 'node-run'
        }), 100);
      } else if (response.id === 'run') {
        console.log(JSON.stringify(response.result));
        child.stdin.end();
      }
    }
  });
  child.stderr.on('data', chunk => process.stderr.write(chunk));
  child.on('exit', code => { if (code) process.exitCode = code; });
  send({ client_version: '1', id: 'register', op: 'register',
    definition: JSON.parse(fs.readFileSync(graphPath, 'utf8')) });
}

if (process.argv[2] === 'provider') provider(process.argv[3]);
else if (process.argv[2] === 'client') client(...process.argv.slice(3));
else process.exit(2);
