const http = require('http');
const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');

const PORT = 3000;
const DATA_FILE = path.join(__dirname, 'gbp-ops-data.json');

// Ensure data file exists
if (!fs.existsSync(DATA_FILE)) {
  fs.writeFileSync(DATA_FILE, JSON.stringify({}));
}

// Run sync-posts.ps1 on startup
function runSync(callback) {
  const scriptPath = path.join(__dirname, 'sync-posts.ps1');
  execFile('powershell', ['-ExecutionPolicy', 'Bypass', '-File', scriptPath], (err, stdout, stderr) => {
    if (err) {
      console.error('[sync] Error:', stderr || err.message);
      if (callback) callback(false);
    } else {
      console.log('[sync] post-status.js updated.');
      if (callback) callback(true);
    }
  });
}

runSync();

const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
};

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // API Endpoints
  if (req.url === '/api/data') {
    if (req.method === 'GET') {
      fs.readFile(DATA_FILE, 'utf8', (err, data) => {
        if (err) {
          res.writeHead(500);
          res.end(JSON.stringify({ error: 'Failed to read data file' }));
          return;
        }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(data || '{}');
      });
      return;
    }

    if (req.method === 'POST') {
      let body = '';
      req.on('data', chunk => {
        body += chunk.toString();
      });
      req.on('end', () => {
        fs.writeFile(DATA_FILE, body, 'utf8', (err) => {
          if (err) {
            res.writeHead(500);
            res.end(JSON.stringify({ error: 'Failed to save data file' }));
            return;
          }
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ success: true }));
        });
      });
      return;
    }
  }

  // API: sync trigger
  if (req.url === '/api/sync' && req.method === 'POST') {
    runSync((ok) => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: ok }));
    });
    return;
  }


  let filePath = path.join(__dirname, req.url === '/' ? 'index.html' : req.url);
  const extname = path.extname(filePath);
  const contentType = MIME_TYPES[extname] || 'text/plain';

  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') {
        res.writeHead(404);
        res.end('404 Not Found');
      } else {
        res.writeHead(500);
        res.end('500 Internal Server Error');
      }
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content, 'utf-8');
    }
  });
});

server.listen(PORT, () => {
  console.log(`GBP Ops Dashboard Server running at http://localhost:${PORT}/`);
  console.log(`Data will be saved to ${DATA_FILE}`);
});
