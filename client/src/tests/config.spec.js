const puppeteer = require('puppeteer');
const path = require('path');
const rimraf = require("rimraf");
const fs = require('fs');
jest.setTimeout(10000);


var CONFIG = {
  headless:false,
  slowMo: 0,
};

var browser = null;
var page = null;

beforeAll(async ()=> {
  try {
    resetTesters();
  } catch(err){
    //pass
  }

  browser = await puppeteer.launch({
    headless: CONFIG.headless,
    slowMo: CONFIG.slowMo
  });
  page = await browser.newPage();

  page.emulate({
    viewport: {
      width: 1700,
      height: 1000
    },
    userAgent: ''
  });

});

afterAll(async ()=> {
  try {
    browser.close();
  }
  catch(err) {
    //pass
  }
  resetTesters();
})


const getBrowser = () => { return browser };
const getPage    = () => { return page    };



describe('puppeteer', () => {
  test('is correctly installed', async () => {
    expect(browser).not.toBe(null);
    expect(page).not.toBe(null);
  });
});


/********** USEFUL FUNCTIONS  ****************/

const sleep = (s) => {
  return new Promise(resolve => setTimeout(resolve, s*1000));
}



const MaterialSelect = async (page, newSelectedValue, cssSelector) => {
    await page.evaluate((newSelectedValue, cssSelector) => {
        var clickEvent = document.createEvent('MouseEvents');
        clickEvent.initEvent("mousedown", true, true);
        var selectNode = document.querySelector(cssSelector);
        selectNode.dispatchEvent(clickEvent);
        [...document.querySelectorAll('li')].filter(el => el.innerText == newSelectedValue)[0].click();
    }, newSelectedValue, cssSelector);
}

const checkFileNotEmpty = (type, name) => {
  var fpath = "";
  if (type === 'custom'){
    fpath = customPath;
  }
  else if (type === 'exports'){
    fpath = exportsPath;
  }
  else {
    fpath = reportsPath;
  }

  try {
    var final_path = path.join(fpath, name);
    var stats = fs.statSync(final_path);
    var fileSizeInBytes = stats["size"];
    return fileSizeInBytes > 0;
  } catch(err){
    return false;
  }

}



module.exports = {
  CONFIG,
  getBrowser,
  getPage,
  sleep,
  MaterialSelect,
}
