const axios = require('axios');
const cheerio = require('cheerio');
axios.get('https://jet-produce.com/contact2/').then(r => {
  const $ = cheerio.load(r.data);
  const form = $('form.wpcf7-form');
  form.find('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea, select').each(function() {
    const el = $(this);
    console.log(JSON.stringify({
      name: el.attr('name'),
      type: el.attr('type') || this.tagName,
      required: el.attr('aria-required'),
      class: el.attr('class')
    }));
  });
}).catch(e => console.error(e.message));
