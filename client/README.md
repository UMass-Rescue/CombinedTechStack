# Electron React Flask Boilerplate

## Initialization

Be sure to have the latest Nodejs and NPM installed: Nodejs >= 14.7.0 , NPM >= 6.14.7

```bash
npm run init
```

## Testing

## Frontend JS Testing

### Automatic

```bash
npm run test
```

### Manual

```bash
npm install -g jest jest-cli
export DISPLAY=:0
jest
```


## Backend Python Testing

### Automatic

Automated testing for a web app with javascript requires browser emulation. For these tests
we use the selenium python module (included in requirements.txt) and chromedriver. The latter
can be installed at the command line as follows for linux:

```bash
sudo apt install chromium-chromedriver
```

Or installed separately for windows:

[Chromedriver](https://chromedriver.chromium.org/)


Now unit tests can be invoked as follows.

```bash
npm run pytest
```

## Debug

Linux:

```bash
npm run debug
```

Windows: (in separate powershell terminals):

```ps1
npm run start-backend
npm run start-react
npm run start-electron
```
