async function run() {
  const url = 'https://docs.google.com/spreadsheets/d/1NNQItK0YcRDiM03YGuMSafbp-wk2WAeGTE7sFtn62pI/export?format=csv';
  try {
    const response = await fetch(url);
    const text = await response.text();
    console.log(text.substring(0, 1000));
  } catch (e) { console.error(e); }
}
run();
