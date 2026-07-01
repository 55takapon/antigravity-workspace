const fs = require('fs');
let code = fs.readFileSync('batch_report.js', 'utf8');
code = code.replace(/for \(const client of CLIENTS\)/g, 'for (const client of CLIENTS.filter(c => c.slug === "unaginokagura-kyoto" || c.slug === "happycars-izumikishiwada"))');
code = code.replace('await htmlToPDF(html, pdfPath);', 'fs.writeFileSync(pdfPath.replace(/\\.pdf$/, ".html"), html, "utf-8");');
fs.writeFileSync('batch_two.js', code, 'utf8');
