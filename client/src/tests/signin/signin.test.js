const puppeteer = require('puppeteer');
const CONFIG = require('../config.spec.js')

var browser = null;
var page = null;

beforeEach(async ()=> {
  browser = CONFIG.getBrowser();
  page = CONFIG.getPage();

  await page.goto('http://localhost:3000/');
});



describe('app', () => {
  test('loads', async () => {
    // pass
  });
});
