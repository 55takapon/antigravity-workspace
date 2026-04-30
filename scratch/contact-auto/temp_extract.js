const playwright = require('playwright');
(async () => {
  const browser = await playwright.chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto('https://mmtv.jp/inquiry/');
  await page.waitForTimeout(2000);
  const inputs = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('input, select, textarea')).map(el => {
      let labelText = '';
      if (el.id) {
        const l = document.querySelector('label[for="' + el.id + '"]');
        if (l) labelText = l.innerText;
      }
      return {
        tag: el.tagName,
        type: el.type,
        name: el.name,
        placeholder: el.placeholder,
        label: labelText
      };
    });
  });
  console.log(JSON.stringify(inputs, null, 2));
  await browser.close();
})();
